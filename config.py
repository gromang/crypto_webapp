import os
from dotenv import load_dotenv

load_dotenv()

dbsettings = {'database': os.getenv("DBNAME"),
            'user': os.getenv("USER"),
            'password': os.getenv("PASSWORD"),
            'host': os.getenv("HOST"),
            'port': os.getenv("PORT"),
            }