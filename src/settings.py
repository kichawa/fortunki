import os


PROJECT_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_PATH = os.path.join(PROJECT_DIR, 'storage.sqlite3.db')

PER_PAGE_LIMIT = 10

VOTE_COOKIE_KEY = '_s'
