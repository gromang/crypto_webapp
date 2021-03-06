import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SKEY")
REMEMBER_COOKIE_DURATION = timedelta(days=5)
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_DATABASE_URI = f"postgresql://{os.getenv('USER')}:" \
    f"{os.getenv('PASSWORD')}@{os.getenv('HOST')}:" \
    f"{os.getenv('PORT')}/{os.getenv('DBNAME')}"

dbsettings = {'database': os.getenv("DBNAME"),
              'user': os.getenv("USER"),
              'password': os.getenv("PASSWORD"),
              'host': os.getenv("HOST"),
              'port': os.getenv("PORT"),
              }

pair_table = {
    "btcusd": "data_btc",
    "ethusd": "data_eth",
    "ltcusd": "data_ltc",
    "xrpusd": "data_xrp"
}

traiding_pairs = ["BTCUSD", "LTCUSD", "ETHUSD", "XRPUSD"]

intervals = {
    "1 min": 1,
    "5 min": 5,
    "15 min": 15,
    "30 min": 30,
    "1 hour": 60,
    "2 hour": 120,
    "4 hour": 240,
    "6 hour": 360,
    "12 hour": 720
}

depth_limits = [300, 200, 100, 80, 60, 50, 40, 30, 20, 10, 5]
