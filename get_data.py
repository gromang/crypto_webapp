import logging
import os
import psycopg2
import requests

from datetime import datetime

from config import dbsettings

now = datetime.now()
logging.basicConfig(filename=f"{os.getcwd()}\logs\{now.strftime('%Y-%m-%d__%H')}.log", level=logging.INFO,
                    filemode="a", format='%(levelname)s %(asctime)s : %(message)s')
logging.info(f'-------------------{now}-------------------')


class CryptoData:
    def __init__(self, symbol, interval, depth):
        self.symbol = symbol
        self.interval = interval
        self.depth = depth

    def connection_to_base(self):
        conn = psycopg2.connect(database=dbsettings['database'],
                                user=dbsettings['user'],
                                password=dbsettings['password'],
                                host=dbsettings['host'],
                                port=dbsettings['port'],
                                )
        return conn

    def last_data_time(self, table_name: str):
        with self.connection_to_base() as conn:
            with conn.cursor() as curs:
                curs.execute(f'''SELECT * FROM data_btc ORDER BY "{table_name}" DESC LIMIT 1 ''')
                last_timestamp = curs.fetchone()[1]
                last_time = datetime.fromtimestamp(last_timestamp).strftime("%Y-%m-%d %H:%M"))
                # value = datetime.fromtimestamp(record[1])
                # my_list.append({
                #     "id": record[0],
                #     "Timestamp": value.strftime('%d-%m-%Y %H:%M:%S'),
                #     "Open": float(record[2]),
                #     "Close": float(record[3]),
                #     "High": float(record[4]),
                #     "Low": float(record[5]),
                #     "Volume": float(record[6])
                # })
        return last_time



if __name__ == "__main__":
    test = CryptoData("BTCUSD", 1, 50)
    test.last_data_time("data_btc")
