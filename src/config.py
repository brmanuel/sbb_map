import os

DATABASE_URI = 'postgresql+psycopg2://{}:{}@{}:{}/{}'.format(
    os.environ['DBUSER'],
    os.environ['DBPASS'],
    os.environ['DBHOST'],
    int(os.environ['DBPORT']),
    os.environ['DBNAME']
)
