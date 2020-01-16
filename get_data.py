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
    """
        symbol: тикет криптовалюты, 
        interval : размер свечи в минутах, например 4-х часовая свеча - 240 минут, 
        depth: глубина выдаваемых данных, например, 50 свечей
    """
    def __init__(self, symbol, interval: int, depth):
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

    def get_last_time(self):
        table_name = "data_btc"
        with self.connection_to_base() as conn:
            with conn.cursor() as curs:
                # забираем таймштамп последней записи
                curs.execute(
                    f'''SELECT "Timestamp" FROM {table_name} WHERE id=(SELECT max(id) FROM {table_name})'''
                )
                timestamp = curs.fetchone()[0]
                return timestamp
        logging.error("get_last_time Error")
        return False

    def get_last_interval(self):
        '''
        Функция определяет время начала последнего интервала. 
        Например, в 14.49 пришел запрос на отображение 15-ти минутных свечей. 
        Отображение свечи нужно начинать не с произвольного места, 
        а привязывать к известным временным делениям. 
        То есть,для нашего примера крайний интервал начинается в 14.45, 
        а для 30-ти минутной свечи - 14.30, часовой свечи - 14.00 и т.д.
        '''
        interval = self.interval
        # Определим текущее время и заберем значение минуты и часа
        current_timestamp = self.get_last_time() or self.get_previous_candle_time()
        current_minute = int(datetime.fromtimestamp(current_timestamp).strftime("%M"))
        current_hour = int(datetime.fromtimestamp(current_timestamp).strftime("%H"))
        # Если интервал - минутный, то достаточно вернуть текущее время
        if interval == 1:
            difference = 0
        elif interval in (2,3,5,10,15,20,30):
            difference = (current_minute % interval)*60
        elif interval in (60,120,180,240,360,720):
            difference = ((current_hour % (interval/60))*60 + current_minute)*60
        else:
            return False
        begin_interval_timestamp = current_timestamp - difference
        last_interval = {"begin": begin_interval_timestamp, "end":current_timestamp}
        return last_interval

    def get_data_edges(self):
        last_interval = self.get_last_interval()
        first_edge_data = last_interval['begin'] - self.interval*self.depth*60
        last_edge_data = last_interval['end']
        data_edges = {"begin":first_edge_data, "end":last_edge_data}
        return data_edges

    def get_raw_data(self):
        data_edges = self.get_data_edges()
        raw_data_list=[]
        table_name = "data_btc"
        with self.connection_to_base() as conn:
            with conn.cursor() as curs:
                curs.execute(
                    f'''SELECT * FROM {table_name} WHERE "Timestamp" >= {data_edges['begin']}'''
                )
                for record in curs:
                    value = datetime.fromtimestamp(record[1])
                    raw_data_list.append({
                        "Time": value.strftime('%d-%m-%Y %H:%M:%S'),
                        "Open": float(record[2]),
                        "Close": float(record[3]),
                        "High": float(record[4]),
                        "Low": float(record[5]),
                        "Volume": float(record[6])
                    })
        return raw_data_list

    def make_new_candles(self):
        raw_data = self.get_raw_data()
        



if __name__ == "__main__":
    test = CryptoData("BTCUSD",5, 12)
    print(test.get_raw_data())
