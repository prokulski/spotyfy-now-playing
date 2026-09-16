import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Optional

try:
    from pythonjsonlogger.json import JsonFormatter
except ImportError:
    JsonFormatter = None

# Domyślne wartości
DEFAULT_APP_NAME = "SET_APP_NAME"
DEFAULT_LOG_DIR = Path().cwd() / "logs"
DEFAULT_CONSOLE_LOG_LEVEL = "INFO"
DEFAULT_FILE_LOG_LEVEL = "INFO"
ROTATE_LOGS_DAYS = 7


class LoggerSingleton:
    """Singleton logger dla całej aplikacji."""

    _instance: Optional["LoggerSingleton"] = None
    _logger: Optional[logging.Logger] = None

    def __new__(cls) -> "LoggerSingleton":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Tworzy singleton bez konfiguracji loggera."""

    def configure(
        self,
        logger_name: str = DEFAULT_APP_NAME,
        log_to_console: bool = True,
        log_to_file: bool = True,
        log_to_json: bool = False,
        log_dir: str | Path = DEFAULT_LOG_DIR,
        console_log_level: str = DEFAULT_CONSOLE_LOG_LEVEL,
        file_log_level: str = DEFAULT_FILE_LOG_LEVEL,
    ) -> "LoggerSingleton":
        """
        Konfiguruje singleton loggera z podanymi parametrami.

        Użycie:
            LoggerSingleton().configure(
                log_to_json=True,
                file_log_level="DEBUG"
            )
            logger = get_logger()
        """
        self._logger = self._configure_logger(
            logger_name=logger_name,
            log_to_console=log_to_console,
            log_to_file=log_to_file,
            log_to_json=log_to_json,
            log_dir=log_dir,
            console_log_level=console_log_level,
            file_log_level=file_log_level,
        )
        return self

    def _configure_logger(self, **kwargs) -> logging.Logger:
        """Konfiguracja loggera z domyślnymi parametrami."""
        logger_name = kwargs.get("logger_name", DEFAULT_APP_NAME)
        log_to_console = kwargs.get("log_to_console", True)
        log_to_file = kwargs.get("log_to_file", True)
        log_to_json = kwargs.get("log_to_json", False)
        log_dir = kwargs.get("log_dir", DEFAULT_LOG_DIR)
        console_log_level = kwargs.get("console_log_level", DEFAULT_CONSOLE_LOG_LEVEL)
        file_log_level = kwargs.get("file_log_level", DEFAULT_FILE_LOG_LEVEL)

        logger = logging.getLogger(logger_name)

        # Jeśli logger już ma handlery, nie konfiguruj go ponownie
        if logger.handlers:
            return logger

        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "[%(asctime)s][%(levelname)-8s][ %(filename)s:%(lineno)s ][ %(funcName)s() ] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Konwersja poziomów logowania na int
        console_log_level_int = self._parse_log_level(console_log_level)
        file_log_level_int = self._parse_log_level(file_log_level)

        if log_to_console:
            c_handler = logging.StreamHandler()
            c_handler.setFormatter(formatter)
            c_handler.setLevel(console_log_level_int)
            logger.addHandler(c_handler)

        log_dir = Path(log_dir)
        if log_to_file:
            log_dir.mkdir(parents=True, exist_ok=True)
            file_log_filename = log_dir / f"{logger_name}.log"

            f_handler = TimedRotatingFileHandler(
                file_log_filename,
                encoding="utf-8",
                when="midnight",
                interval=1,
                backupCount=ROTATE_LOGS_DAYS,
            )
            f_handler.setFormatter(formatter)
            f_handler.setLevel(file_log_level_int)
            logger.addHandler(f_handler)

        if log_to_json:
            json_log_dir = log_dir / "json"
            json_log_dir.mkdir(parents=True, exist_ok=True)
            json_log_filename = json_log_dir / f"{logger_name}-json.log"

            if JsonFormatter is not None:
                json_formatter = JsonFormatter(
                    "%(asctime)s %(levelname)s %(filename)s %(lineno)d %(funcName)s %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                )
                json_handler = TimedRotatingFileHandler(
                    json_log_filename,
                    encoding="utf-8",
                    when="midnight",
                    interval=1,
                    backupCount=7,
                )
                json_handler.setFormatter(json_formatter)
                json_handler.setLevel(file_log_level_int)
                logger.addHandler(json_handler)

        return logger

    @staticmethod
    def _parse_log_level(level: str | int) -> int:
        """Konwersja poziomu logowania na int."""
        if isinstance(level, str):
            return getattr(logging, level.upper(), logging.INFO)
        return level

    def get_logger(self) -> logging.Logger:
        """Zwraca instancję loggera."""
        if self._logger is None:
            raise RuntimeError("Logger has not been configured")
        return self._logger


def get_logger(
    logger_name: str = DEFAULT_APP_NAME,
    log_to_console: bool = True,
    log_to_file: bool = True,
    log_to_json: bool = False,
    log_dir: str | Path = DEFAULT_LOG_DIR,
    console_log_level: str = DEFAULT_CONSOLE_LOG_LEVEL,
    file_log_level: str = DEFAULT_FILE_LOG_LEVEL,
) -> logging.Logger:
    """
    Zwraca singleton instancję loggera dla całej aplikacji.

    Parametry są używane tylko przy PIERWSZYM wywołaniu.
    Kolejne wywołania zwrócą już skonfigurowany logger.

    Użycie:
        # Pierwsze użycie - konfigurujemy loggera
        logger = get_logger(log_to_json=True, file_log_level="DEBUG")

        # Kolejne użycia - zwracamy istniejący logger
        logger = get_logger()
        logger.info("Wiadomość")
    """
    singleton = LoggerSingleton()

    # Jeśli logger nie istnieje, skonfiguruj go z podanymi parametrami
    if singleton._logger is None:
        singleton.configure(
            logger_name=logger_name,
            log_to_console=log_to_console,
            log_to_file=log_to_file,
            log_to_json=log_to_json,
            log_dir=log_dir,
            console_log_level=console_log_level,
            file_log_level=file_log_level,
        )

    return singleton.get_logger()
