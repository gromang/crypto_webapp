import os
from dotenv import load_dotenv

load_dotenv()

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
