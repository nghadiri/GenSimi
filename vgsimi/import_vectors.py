
from util.config import load_app_settings
settings = load_app_settings()

uri=settings['neo4j']['uri']
user=settings['neo4j']['user']
password=settings['neo4j']['password']

