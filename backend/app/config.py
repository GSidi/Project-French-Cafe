from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

"""
 - __file__ — a variable Python sets automatically in every module: the path to this file. 
 Inside config.py, it's the path to config.py. Depending on how Python was invoked, it may be relative (app\config.py) rather than absolute.
- .resolve() — turns it into a guaranteed absolute path and expands any .. or symlinks. 
 So you get  <path>\config.py. This is what makes the result independent of your working directory.
- .parents — a sequence of the containing folders, walking upward:
┌────────────┬────────────────────────────────────────────┐
│            │                                            │
├────────────┼────────────────────────────────────────────┤
│ parents[0] │ ...\backend\app                            │
├────────────┼────────────────────────────────────────────┤
│ parents[1] │ ...\backend                                │
├────────────┼────────────────────────────────────────────┤
│ parents[2] │ ...\Cafeteria's Project ← the project root │
└────────────┴────────────────────────────────────────────┘
So parents[2] is where .env and docker-compose.yml live.
"""
ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """
    - ROOT_DIR / ".env" — pathlib overloads the / operator to join paths. Cleaner than string concatenation and it
    handles the Windows separator for you. - env_file= — tells pydantic-settings to read that file when the class is
    instantiated. Values already present in the real environment win over the file, which is what you want: in
    production you'd set actual env vars and ship no .env at all. - extra="ignore" — your .env has POSTGRES_PASSWORD
    and friends, but Compose may add others over time. Without this, any key in the file that isn't a declared field
    raises a validation error. "ignore" says: read what I declared, skip the rest.
    """
    model_config = SettingsConfigDict(env_file=ROOT_DIR / ".env", extra="ignore")
    postgres_user: str
    postgres_password: str
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str

    @property
    def database_url(self) -> str:
        return f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"


settings = Settings()
