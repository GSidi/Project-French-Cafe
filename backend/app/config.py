from pathlib import Path
from pydantic_settings import BaseSettings,SettingsConfigDict

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


