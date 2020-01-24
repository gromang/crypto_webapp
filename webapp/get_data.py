import csv
import logging
import os
from datetime import datetime

import psycopg2
import requests

from webapp.config import dbsettings, pair_table

now = datetime.now()
logging.basicConfig(filename=f"{os.getcwd()}/logs/{now.strftime('%Y-%m-%d_%H_%M_%S_%f')}.log", level=logging.INFO,
                    filemode="w", format='%(levelname)s %(asctime)s : %(message)s')
logging.info(f'\n\n_______________________________________________________________________________________________________________')


class CryptoData:
    """
        symbol: тикет криптовалюты. Запись вида: BTCUSD

        interval : размер свечи в минутах, например 4-х часовая свеча - 240 минут

        depth: глубина выдаваемых данных, например, 50 свечей
    """

    def __init__(self, symbol: str, interval: int, depth: int):
        self.symbol = symbol.lower()
        self.interval = interval
        self.depth = depth
        self.table_name = pair_table[self.symbol]
        logging.info(f"_init_ : \nSymbol : {self.symbol}\nInterval : {self.interval}\nDepth : {self.depth}\nTable name: {self.table_name}")

    def __get_previous_candle_time__(self):
        try:
            get_utc_time = requests.get("https://yandex.com/time/sync.json")
            get_utc_time.raise_for_status()
        except (requests.exceptions.RequestException, requests.exceptions.HTTPError) as err:
            logging.error(f"GET TIME ERROR: {err}")
            return False
        get_utc_time = get_utc_time.json()
        # Забираем и форматируем Timestamp (отбрасываем милисекунды)
        utc_ts = int(str(get_utc_time["time"])[:-3])
        # Получаем текущую минуту
        current_minute_time = datetime.fromtimestamp(utc_ts).strftime("%Y-%m-%d %H:%M")
        # Получаем timestamp предыдущей минуты
        ts = int(datetime.strptime(current_minute_time, "%Y-%m-%d %H:%M").timestamp() - 60)
        logging.info(f"Formed candle time: {ts}")
        return ts

    def __connection_to_base__(self):
        try:
            conn = psycopg2.connect(
                database=dbsettings['database'],
                user=dbsettings['user'],
                password=dbsettings['password'],
                host=dbsettings['host'],
                port=dbsettings['port'],
            )
            logging.info("Connection to base - successfull")
            return conn
        except psycopg2.Error as e:
            # Обратить внимание, что при отсутсвии коннекта -ошибка в лог не пишется, исправить
            logging.error(e.pgerror())
            return False

    def __get_last_time__(self):
        with self.__connection_to_base__() as conn:
            with conn.cursor() as curs:
                # забираем таймштамп последней записи
                curs.execute(
                    f'''SELECT "Timestamp" FROM {self.table_name} WHERE id=(SELECT max(id) FROM {self.table_name})'''
                )
                timestamp = curs.fetchone()[0]
                logging.info(f"Function __get_last_time__ : return timestamp {timestamp}")
                return timestamp
        logging.error("get_last_time Error")
        return False

    def __get_last_interval__(self):
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
        current_timestamp = self.__get_last_time__() or self.__get_previous_candle_time__()
        current_minute = int(datetime.fromtimestamp(
            current_timestamp).strftime("%M"))
        current_hour = int(datetime.fromtimestamp(
            current_timestamp).strftime("%H"))
        logging.info(f"Function __get_last_interval__ :\ninterval :\t{interval} min\ncurrent_timestamp :\t{current_timestamp} ({datetime.fromtimestamp(current_timestamp).strftime('%d-%m %H:%M')})\ncurrent_hour :\t{current_hour}\ncurrent_minute :\t{current_minute}")
        # Если интервал - минутный, то достаточно вернуть текущее время
        if interval == 1:
            difference = 0
        elif interval in (2, 3, 5, 10, 15, 20, 30):
            difference = (current_minute % interval)*60
        elif interval in (60, 120, 180, 240, 360, 720):
            difference = ((current_hour % (interval/60))
                          * 60 + current_minute)*60
        else:
            return False
        begin_interval_timestamp = current_timestamp - difference
        last_interval = {"begin": begin_interval_timestamp,
                         "end": current_timestamp}
        logging.info(f"Function __get_last_interval__ :\ndifference :\t{difference} \t({difference/60})\nbegin_interval_timestamp :\t{begin_interval_timestamp} ({datetime.fromtimestamp(begin_interval_timestamp).strftime('%d-%m %H:%M')})\nlast_interval :\t{last_interval}")
        return last_interval

    def __get_data_edges__(self):
        last_interval = self.__get_last_interval__()
        first_edge_data = last_interval['begin'] - self.interval*self.depth*60
        last_edge_data = last_interval['end']
        data_edges = {"begin": first_edge_data, "end": last_edge_data}
        logging.info(f"Function __get_data_edges__ :\nlast_interval {last_interval}\nfirst_edge_data {first_edge_data} ({datetime.fromtimestamp(first_edge_data).strftime('%d-%m %H:%M')})\nlast_edge_data {last_edge_data} ({datetime.fromtimestamp(last_edge_data).strftime('%d-%m %H:%M')})\ndata_edges {data_edges}")
        return data_edges

    def get_raw_data(self):
        data_edges = self.__get_data_edges__()
        raw_data_list = []
        logging.info(f"Function get_raw_data :\ndata_edges {data_edges}\nraw_data_list {raw_data_list} ")
        with self.__connection_to_base__() as conn:
            with conn.cursor() as curs:
                curs.execute(
                    f'''SELECT * FROM {self.table_name} WHERE "Timestamp" >= {data_edges['begin']} ORDER BY "Timestamp"'''
                )
                for record in curs:
                    raw_data_list.append({
                        "Timestamp": int(record[1]),
                        "Open": float(record[2]),
                        "Close": float(record[3]),
                        "High": float(record[4]),
                        "Low": float(record[5]),
                        "Volume": float(record[6])
                    })
        logging.info(f"Function get_raw_data complete. raw_data_list consists of {len(raw_data_list)} elements")
        return raw_data_list

    def __check_raw_data__(self): pass

    def get_new_candles_sql(self): pass

    def make_new_candles_dict(self):
        raw_data = self.get_raw_data()

        candle_list = []
        candle_time = raw_data[0]["Timestamp"]
        candle_open = raw_data[0]["Open"]
        candle_high = raw_data[0]["High"]
        candle_low = raw_data[0]["Low"]
        candle_vol = 0
        candle_list.append({"Timestamp": candle_time, "Open": candle_open})
        i = 0

        for id, item in enumerate(raw_data):
            candle_end_time = candle_time + self.interval * 60
            if item["Timestamp"] < candle_end_time and not item["Timestamp"] == raw_data[-1]["Timestamp"]:
                if item["High"] > candle_high:
                    candle_high = item["High"]
                if item["Low"] < candle_low:
                    candle_low = item["Low"]
                candle_vol += item["Volume"]
            elif item["Timestamp"] >= candle_end_time:
                candle_list[i].update(
                    {"Close": raw_data[id-1]["Close"], "High": candle_high, "Low": candle_low, "Volume": candle_vol})
                i += 1
                candle_time = item["Timestamp"]
                candle_open = item["Open"]
                candle_high = item["High"]
                candle_low = item["Low"]
                candle_vol = 0
                candle_list.append(
                    {"Timestamp": candle_time, "Open": candle_open})
            elif item["Timestamp"] == raw_data[-1]["Timestamp"]:
                candle_list[i].update(
                    {"Close": raw_data[id-1]["Close"], "High": candle_high, "Low": candle_low, "Volume": candle_vol})
        logging.info(f"Function make_new_candles_dict complete. candle_list consists of {len(candle_list)} elements")
        return candle_list

    # def __convert_timestamp__(self, timestamp_data: int):
    #     this_time = datetime.fromtimestamp(timestamp_data)
    #     if this_time.hour == 0 and this_time.minute == 0:
    #         new_time = this_time.strftime('%d-%m %H:%M')
    #     else:
    #         new_time = this_time.strftime('%H:%M')
    #     return new_time

    def __convert_timestamp__(self, timestamp_data: int):
        new_time = datetime.fromtimestamp(timestamp_data).strftime('%d-%m %H:%M')
        #logging.info(f"Function __convert_timestamp__ return new_time {new_time}")
        return new_time

    def data_for_plotly(self):
        raw_data = self.get_raw_data()

        plot_data = {}
        time_list = []
        open_list = []
        close_list = []
        high_list = []
        low_list = []
        vol_list = []

        candle_time = raw_data[0]["Timestamp"]
        candle_open = raw_data[0]["Open"]
        candle_high = raw_data[0]["High"]
        candle_low = raw_data[0]["Low"]
        candle_vol = 0

        time_list.append(self.__convert_timestamp__(candle_time))
        open_list.append(candle_open)

        for id, item in enumerate(raw_data):
            candle_end_time = candle_time + self.interval * 60

            if item["Timestamp"] < candle_end_time and not item["Timestamp"] == raw_data[-1]["Timestamp"]:
                if item["High"] > candle_high:
                    candle_high = item["High"]
                if item["Low"] < candle_low:
                    candle_low = item["Low"]
                candle_vol += item["Volume"]

            elif item["Timestamp"] >= candle_end_time:
                close_list.append(raw_data[id-1]["Close"])
                high_list.append(candle_high)
                low_list.append(candle_low)
                vol_list.append(candle_vol)

                candle_time = item["Timestamp"]
                candle_open = item["Open"]
                candle_high = item["High"]
                candle_low = item["Low"]
                candle_vol = 0

                time_list.append(self.__convert_timestamp__(candle_time))
                open_list.append(candle_open)

            elif item["Timestamp"] == raw_data[-1]["Timestamp"]:
                close_list.append(raw_data[id-1]["Close"])
                high_list.append(candle_high)
                low_list.append(candle_low)
                vol_list.append(candle_vol)

        plot_data = {"datetime": time_list, "open": open_list, "close": close_list,
                     "high": high_list, "low": low_list, "volume": vol_list}
        logging.info(f"Function data_for_plotly complete. plot_data consists of {len(plot_data['datetime'])} elements")
        return plot_data


if __name__ == "__main__":
    test = CryptoData("BTCUSD", 30, 50)
    raw_data = test.get_raw_data()
    candle_data = test.make_new_candles_dict()
    plot_data = test.data_for_plotly()

    with open(f"{now.strftime('%Y-%m-%d_%H_%M')}__{test.symbol}_raw_data.csv", "w", newline='') as out_file:
        writer = csv.DictWriter(out_file, delimiter='\t', fieldnames=[
                                "Timestamp", "Open", "Close", "High", "Low", "Volume"])
        writer.writeheader()
        for row in raw_data:
            writer.writerow(row)

    with open(f"{now.strftime('%Y-%m-%d_%H_%M')}__{test.symbol}_{test.interval}_new_candles_dict.csv", "w", newline='') as out_file:
        writer = csv.DictWriter(out_file, delimiter='\t', fieldnames=[
                                "Timestamp", "Open", "Close", "High", "Low", "Volume"])
        writer.writeheader()
        for row in candle_data:
            writer.writerow(row)
    
    with open(f"{now.strftime('%Y-%m-%d_%H_%M')}__{test.symbol}_{test.interval}_plot_data.csv", "w", newline='') as out_file:
        writer = csv.DictWriter(out_file, delimiter='\t', fieldnames=[
                                "datetime", "open", "close", "high", "low", "volume"])
        writer.writeheader()
        length = len(plot_data["datetime"])
        for i in range(0,length-1):
            row = {
                "datetime":plot_data["datetime"][i],
                "open": plot_data["open"][i],
                "close": plot_data["close"][i],
                "high": plot_data["high"][i],
                "low": plot_data["low"][i],
                "volume": plot_data["volume"][i],
            }
            writer.writerow(row)
    