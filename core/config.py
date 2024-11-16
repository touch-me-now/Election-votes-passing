from pathlib import Path

from pydantic import MongoDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).parent.parent


class Settings(BaseSettings, frozen=True):
    election_id: int
    election_type: str
    election_base_url: str = "https://newess.shailoo.gov.kg/api/election/"
    mongo_url: MongoDsn
    election_db_name: str = "election"
    votes_collection: str = "votes"
    manual_votes: str = "countvotes"
    parties_collection: str = "parties"
    cities_collection: str = "cities"
    cities_json_file: Path = BASE_DIR / "static/cities.json"
    log_file_path: Path = BASE_DIR / "app.log"

    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env")


settings = Settings()
