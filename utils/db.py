import time
from collections.abc import Callable, Mapping
from typing import Any, Protocol

from sqlalchemy import (
    BigInteger,
    Column,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
    delete,
    insert,
    inspect,
)
from sqlalchemy.engine import URL, Engine
from sqlalchemy.exc import InterfaceError, OperationalError
from sqlalchemy.orm import Session, sessionmaker

from utils.config import DatabaseConfig
from utils.logger import get_logger


class Record(Protocol):
    def to_dict(self) -> dict[str, Any]: ...


class Database:
    def __init__(self, config: DatabaseConfig):
        self._logger = get_logger()
        self.config = config
        self.engine = self._create_engine(config)
        self.metadata = MetaData()
        self._session_factory = sessionmaker(bind=self.engine)
        self._logger.info(
            "Database engine initialized",
            extra={"database": config.name, "host": config.host, "port": config.port},
        )

    @staticmethod
    def _create_engine(config: DatabaseConfig) -> Engine:
        url = URL.create(
            drivername=config.driver,
            username=config.user,
            password=config.password,
            host=config.host,
            port=config.port,
            database=config.name,
        )
        return create_engine(url, pool_pre_ping=True, pool_recycle=3600)

    def build_tables(self) -> tuple[Table, Table]:
        return (
            self._build_table(
                "sp_plays",
                [
                    Column("timestamp", BigInteger, primary_key=True),
                    Column("item_id", String(64)),
                    Column("item_progress", Integer),
                    Column("item_durration", Integer),
                    Column("item_progress_percent", Float),
                    Column("device_name", String(255)),
                    Column("device_type", String(255)),
                ],
            ),
            self._build_table(
                "sp_features",
                [
                    Column("timestamp", BigInteger),
                    Column("item_id", String(64), primary_key=True),
                    Column("item_name", String(255)),
                    Column("item_artist", String(255)),
                    Column("item_track_number", Integer),
                    Column("item_popularity", Integer),
                    Column("item_url", String(255)),
                    Column("album_id", String(255)),
                    Column("album_name", String(255)),
                    Column("album_type", String(255)),
                    Column("album_url", String(255)),
                    Column("album_cover", String(255)),
                    Column("album_release_date", String(255)),
                    Column("album_total_tracks", Integer),
                    Column("danceability", Float),
                    Column("energy", Float),
                    Column("key", Integer),
                    Column("loudness", Float),
                    Column("mode", Integer),
                    Column("speechiness", Float),
                    Column("acousticness", Float),
                    Column("instrumentalness", Float),
                    Column("liveness", Float),
                    Column("valence", Float),
                    Column("tempo", Float),
                    Column("time_signature", Integer),
                    Column("lastfm_track_title", String(255)),
                    Column("lastfm_track_url", String(255)),
                    Column("lastfm_track_mbid", String(64)),
                    Column("lastfm_track_listeners", Integer),
                    Column("lastfm_track_playcount", Integer),
                    Column("lastfm_artist_mbid", String(64)),
                    Column("lastfm_album_title", String(255)),
                    Column("lastfm_album_mbid", String(64)),
                    Column("lastfm_track_tags", String(255)),
                ],
            ),
        )

    def _build_table(self, name: str, columns: list[Column]) -> Table:
        if inspect(self.engine).has_table(name):
            table = Table(name, self.metadata, autoload_with=self.engine)
            self._logger.debug("Database table reflected", extra={"table": name})
            return table

        table = Table(name, self.metadata, *columns)
        table.create(bind=self.engine)
        self._logger.info("Database table created", extra={"table": name})
        return table

    def close(self) -> None:
        try:
            self.engine.dispose()
            self._logger.info("Database connection closed")
        except Exception as e:
            self._logger.warning("Error closing database connection", extra={"error": str(e)})

    def reconnect(self) -> None:
        self._logger.warning("Reconnecting to database...")
        self.close()
        self.engine = self._create_engine(self.config)
        self._session_factory = sessionmaker(bind=self.engine)
        self._logger.info(
            "Database engine re-initialized",
            extra={"database": self.config.name, "host": self.config.host, "port": self.config.port},
        )

    def _execute_in_session(self, func: Callable[[Session], None]) -> None:
        for attempt in range(2):
            try:
                with self._session_factory.begin() as session:
                    func(session)
                return
            except (OperationalError, InterfaceError) as e:
                self._logger.warning(
                    "Database connection lost during execute, reconnecting...",
                    extra={"error": str(e), "attempt": attempt + 1},
                )
                self.reconnect()
                if attempt == 1:
                    raise
                time.sleep(1)

    def insert_record(self, table: Table, values: Mapping[str, object]) -> None:
        self._execute_in_session(lambda session: session.execute(insert(table).values(values)))

    def delete_record(self, table: Table, item_id: str) -> None:
        self._execute_in_session(
            lambda session: session.execute(delete(table).where(table.c.item_id == item_id))
        )

    def save_record(
        self,
        table: Table,
        values: Mapping[str, object] | Record,
        extra_values: Mapping[str, object] | None = None,
    ) -> None:
        if isinstance(values, Mapping):
            record = dict(values)
        else:
            record = values.to_dict()

        if extra_values:
            record.update(extra_values)

        record["timestamp"] = int(time.time())

        def _do_save(session: Session) -> None:
            if table.name == "sp_features":
                session.execute(delete(table).where(table.c.item_id == record.get("item_id")))

            session.execute(insert(table).values(record))

        try:
            self._execute_in_session(_do_save)
        except Exception:
            self._logger.exception(
                "Database record save failed",
                extra={"table": table.name, "item_id": record.get("item_id")},
            )
            raise
