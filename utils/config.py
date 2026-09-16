import os
from dataclasses import dataclass
from pathlib import Path

import yaml
from dotenv import load_dotenv


@dataclass(frozen=True)
class DatabaseConfig:
    driver: str
    name: str
    user: str
    password: str
    host: str
    port: int


@dataclass(frozen=True)
class Config:
    spotify_client_id: str
    spotify_client_secret: str
    spotify_username: str
    spotify_scope: str
    spotify_redirect_uri: str
    lastfm_api_key: str
    database: DatabaseConfig
    sleep_time: int


def load_config() -> Config:
    project_dir = Path(__file__).resolve().parent.parent
    load_dotenv(project_dir / ".env")
    with (project_dir / "config.yaml").open(encoding="utf-8") as config_file:
        yaml_config = yaml.safe_load(config_file)

    return Config(
        spotify_client_id=os.environ["SPOTIFY_CLIENT_ID"],
        spotify_client_secret=os.environ["SPOTIFY_CLIENT_SECRET"],
        spotify_username=os.environ["SPOTIFY_USERNAME"],
        spotify_scope=yaml_config["spotify"]["scope"],
        spotify_redirect_uri=yaml_config["spotify"]["redirect_uri"],
        lastfm_api_key=os.environ["LASTFM_API_KEY"],
        database=DatabaseConfig(
            driver=yaml_config["database"]["driver"],
            name=os.environ["DB_NAME"],
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            host=os.environ["DB_HOST"],
            port=int(os.environ["DB_PORT"]),
        ),
        sleep_time=yaml_config["sleep_time"],
    )
