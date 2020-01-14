import logging
import os
import psycopg2
import requests

from datetime import datetime

from config import dbsettings

now = datetime.now()
logging.basicConfig(filename=f"{os.getcwd()}/logs/{now.strftime('%Y-%m-%d__%H')}.log", level=logging.INFO,
                    filemode="a", format='%(levelname)s %(asctime)s : %(message)s')
logging.info(f'-------------------{now}-------------------')


class CryptoData:
    def __init__(self, symbol, interval, depth):
        self.symbol = symbol
        self.interval = interval
        self.depth = depth

    def get_previous_candle_time(self):
        try:
            get_utc_time = requests.get("https://yandex.com/time/sync.json")
            get_utc_time.raise_for_status()
        except (
            requests.exceptions.RequestException,
            requests.exceptions.HTTPError,
        ) as err:
            logging.error(f"GET TIME ERROR: {err}")
            return False
        get_utc_time = get_utc_time.json()
        # Забираем и форматируем Timestamp (отбрасываем милисекунды)
        utc_ts = int(str(get_utc_time["time"])[:-3])
        # Получаем текущую минуту
        current_minute_time = datetime.fromtimestamp(
            utc_ts).strftime("%Y-%m-%d %H:%M")
        # Получаем timestamp предыдущей минуты
        ts = int(
            datetime.strptime(current_minute_time,
                              "%Y-%m-%d %H:%M").timestamp() - 60
        )
        logging.info(f"Formed candle time: {ts}")
        return ts

    def connection_to_base():
        conn = psycopg2.connect(database=database['database'],
                                user=database['user'],
                                password=database['password'],
                                host=database['host'],
                                port=database['port'],
                                )

        print("База данных успешно открыта")
        return conn

    def retrieving_table_data(table_database: str):
        my_list = []
        with connection_to_base() as conn:
            with conn.cursor() as curs:
                curs.execute(
                    f'''SELECT * FROM "{table_database}" '''
                )

                for record in curs:
                    value = datetime.fromtimestamp(record[1])
                    my_list.append({
                        "id": record[0],
                        "Timestamp": value.strftime('%d-%m-%Y %H:%M:%S'),
                        "Open": float(record[2]),
                        "Close": float(record[3]),
                        "High": float(record[4]),
                        "Low": float(record[5]),
                        "Volume": float(record[6])
                    })

        print('Таблица успешно прочитана')
        conn.close()
        return my_list


if __name__ == "__main__":
    retrieving_table_data('crypto_project')
