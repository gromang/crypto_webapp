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
    def __init__(self, symbol, interval: int, depth):
        """
        interval : candle interval in minutes, for example, 4 hour = 240 min
        """
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

    def connection_to_base(self):
        try:
            conn = psycopg2.connect(
                database=dbsettings['database'],
                user=dbsettings['user'],
                password=dbsettings['password'],
                host=dbsettings['host'],
                port=dbsettings['port'],
            )
            return conn
        except psycopg2.Error as e:
            # Обратить внимание, что при отсутсвии коннекта -ошибка в лог не пишется, исправить
            logging.error(e.pgerror())
            return False

    def get_last_time(self, table_name: str):
        try:
            with self.connection_to_base() as conn:
                with conn.cursor() as curs:
                    # забираем таймстамп последней записи
                    curs.execute(
                        f'''SELECT "Timestamp" FROM {table_name} WHERE id=(SELECT max(id) FROM {table_name})'''
                    )
                    timestamp = curs.fetchone()[0]
                    return timestamp
        except:
            logging.error("get_last_time Error")
            return False

    def get_start_interval(self):
        # функция определяет с какого времени начинается последний интервал.
        # Например, в 14.49 пришел запрос на отображение 50-ти 15-ти минутных свечей.
        # Общепринято отображение свечи начинать не с произвольного места,
        # а привязывать интервал свечи к известным временным делениям.
        # То есть, начало последнего интервала - 14.45
        # Для 30-ти минутной свечи - 14.30
        # Часовая свеча - 14.00
        # 4-х часовая - 12.00
        # и так далее
        interval = self.interval
        current_timestamp = self.get_last_time("data_btc") or self.get_previous_candle_time()
        current_minute = int(datetime.fromtimestamp(current_timestamp).strftime("%M"))
        if 0 < interval < 2:
            return current_timestamp
        elif interval in (2,3,5,10,15,20,30):
            start_interval_timestamp = current_timestamp - (current_minute % interval)*60
            return start_interval_timestamp
        elif interval in (60,120,180,240,360,720):
            current_hour = int(datetime.fromtimestamp(current_timestamp).strftime("%H"))
            differense = (current_hour % (interval/60))*3600
            start_interval_timestamp = current_timestamp - differense - current_minute*60
            return start_interval_timestamp
        else:
            return False


if __name__ == "__main__":
    test = CryptoData("BTCUSD",180, 100)
    print(datetime.fromtimestamp(test.get_start_interval()).strftime("%Y-%m-%d %H:%M"))

# for record in curs:
#     value = datetime.fromtimestamp(record[1])
#     my_list.append({
#         "id": record[0],
#         "Timestamp": value.strftime('%d-%m-%Y %H:%M:%S'),
#         "Open": float(record[2]),
#         "Close": float(record[3]),
#         "High": float(record[4]),
#         "Low": float(record[5]),
#         "Volume": float(record[6])
#     })
