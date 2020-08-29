import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

# Open csv file
b = open("hobbies.csv")
# Read the file
reader = csv.reader(b)
# Adding each row to database
for name in reader:
  db.execute("INSERT INTO hobbies (name) VALUES (:name)", {"name": name})
db.commit()