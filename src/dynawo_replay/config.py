from pathlib import Path

from pydantic_settings import BaseSettings

PACKAGE_DIR = Path(__file__).parent


class Settings(BaseSettings):
    DYNAWO_HOME: Path = Path("~/dynawo/")
    TMP_DIR: Path = Path("/tmp/")


settings = Settings()
