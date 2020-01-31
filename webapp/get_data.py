import csv
import logging
import os
from datetime import datetime as dt

import psycopg2
import requests

from webapp.config import dbsettings, pair_table

now = dt.now()
bigline = "\n\n______________________________________________________________"
logging.basicConfig(
    filename=f"{os.getcwd()}/logs/{now.strftime('%Y-%m-%d_%H_%M_%S_%f')}.log",
    level=logging.INFO,
    filemode="w",
    format='%(levelname)s %(asctime)s : %(message)s'
    )


class CryptoData:
    """
        symbol:тикет криптовалюты. Запись вида: BTCUSD

        interval:размер свечи в минутах,
        например 4-х часовая свеча - 240 минут

        depth:глубина выдаваемых данных, например, 50 свечей

        Класс CryptoData предназначен для формирования данных,
        пригодных для использования с библиотекой plotly.
        Схема работы:
            1) через метод __get_previous_candle_time__() или
            __get_last_time__() определяется timestamp предыдущей минуты.
            2) затем через __get_last_interval__() определяется
            опорная точка последнего временного интервала
            ( больше информации в описании метода )
            3) От опорной точки с помощью заданых interval и depth
            высчитываются границы запрашиваемых данных через метод
            __get_data_edges__(). Данный метод возращает словарь
            с timestamp начала и конца требуемого временного отрезка
            4) Метод get_raw_data() подключается к базе через метод
            __connection_to_base__() и запрашивает данные через SQL.
            Возращает список необработанных минутных котировок,
            ограниченных пределами из __get_data_edges__().
            5) Эти сырые данные используются методами
            make_new_candles_dict() и data_for_plotly() для формирования из
            минутных интервалов новых свечей с требуемым интервалом.
            6) Метод make_new_candles_dict() возращает списки словарей,
            содержащих парамерты свечей нового интервала
            7) Метод data_for_plotly() возращает словарь, содержащий
            данные, подготовленные для отображения через
            библиотеку plotly
    """

    def __init__(self, symbol: str, interval: int, depth: int):
        self.symbol = symbol.lower()
        self.interval = interval
        self.depth = depth
        self.table_name = pair_table[self.symbol]
        logging.info(bigline)
        logging.info(f'''_init_ :
                        Symbol : {self.symbol}
                        Interval : {self.interval}
                        Depth : {self.depth}
                        Table name: {self.table_name}''')

    def __get_previous_candle_time__(self):
        '''
        Метод запрашивает время у сервера яндекса,
        который возращает ответ в виде json.
        По ключу ["time"] забирает timestamp текущей
        минуты и возращает timestamp предыдущей минуты.
        '''
        try:
            get_utc_time = requests.get("https://yandex.com/time/sync.json")
            get_utc_time.raise_for_status()
        except (requests.exceptions.RequestException,
                requests.exceptions.HTTPError) as err:
            logging.error(f"GET TIME ERROR: {err}")
            return False
        get_utc_time = get_utc_time.json()
        # Забираем и форматируем Timestamp (отбрасываем милисекунды)
        utc_ts = int(str(get_utc_time["time"])[:-3])
        # Получаем текущую минуту
        this_minute = dt.fromtimestamp(utc_ts).strftime("%Y-%m-%d %H:%M")
        # Получаем timestamp предыдущей минуты
        ts = int(
            dt.strptime(this_minute, "%Y-%m-%d %H:%M").timestamp() - 60
            )
        logging.info(f"Formed candle time: {ts}")
        return ts

    def __connection_to_base__(self):
        '''
        Метод, для соединения с базой.
        Использует параметры подключения,
        прописанные в файле конфигурации.
        Возращает connector в случае успешного соединения
        '''
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
            logging.error(f"__connection_to_base__ Error\n{e}")
            return False

    def __get_last_time__(self):
        '''
        Резервный метод определения времени последней
        сформировавшейся минутной свечи.
        Подключается к базе и забирает из последней записи
        timestamp
        '''
        try:
            with self.__connection_to_base__() as conn:
                with conn.cursor() as curs:
                    # забираем таймштамп последней записи
                    curs.execute(
                        f'SELECT "Timestamp" FROM {self.table_name} '
                        f'WHERE id=(SELECT max(id) FROM {self.table_name})'
                    )
                    timestamp = curs.fetchone()[0]
                    logging.info(
                        f"Function __get_last_time__ :"
                        f"return timestamp {timestamp}")
                    return timestamp
        except psycopg2.Error as e:
            logging.error(f"get_last_time Error\n{e}")
            return False

    def __get_last_interval__(self):
        '''
        Функция определяет время начала последнего интервала.
        Это время является опорной точкой.
        Например, в 14.49 пришел запрос на отображение 15-ти минутных свечей.
        Отображение свечи нужно начинать не с произвольного места,
        а привязывать к известным временным делениям.
        То есть,для нашего примера крайний интервал начинается в 14.45,
        а для 30-ти минутной свечи - 14.30, часовой свечи - 14.00 и т.д.
        Возвращает словарь с timestamp начала и конца последней
        свечи заданного интервала, как правило еще не сформированной.
        '''
        interval = self.interval
        # Определим текущий timestamp и заберем значение минуты и часа
        this_ts = (
            self.__get_last_time__() or self.__get_previous_candle_time__()
            )

        if this_ts:
            current_minute = int(
                dt.fromtimestamp(this_ts).strftime("%M"))
            current_hour = int(
                dt.fromtimestamp(this_ts).strftime("%H"))
            logging.info(
                f"Function __get_last_interval__ :\n"
                f"interval :\t{interval} min\n"
                f"current_timestamp :\t{this_ts} "
                f"({dt.fromtimestamp(this_ts).strftime('%d-%m %H:%M')})\n"
                f"current_hour :\t{current_hour}\n"
                f"current_minute :\t{current_minute}"
                )

            # Если интервал - минутный, то достаточно вернуть текущее время
            if interval == 1:
                difference = 0
            elif interval in (2, 3, 5, 10, 15, 20, 30):
                difference = (current_minute % interval)*60
            elif interval in (60, 120, 180, 240, 360, 720):
                difference = (
                    ((current_hour % (interval/60)) * 60 + current_minute) * 60
                )
            else:
                return False

            start_ts = this_ts - difference
            last_interval = {
                "begin": start_ts,
                "end": this_ts
                }
            logging.info(
                f"Function __get_last_interval__ :\n"
                f"difference :\t{difference} \t({difference/60})\n"
                f"start_timestamp :\t{start_ts} "
                f"({dt.fromtimestamp(start_ts).strftime('%d-%m %H:%M')})\n"
                f"last_interval :\t{last_interval}")

            return last_interval
        else:
            return False

    def __get_data_edges__(self):
        '''
        Метод возращает границы запрашиваемых данных.
        Границы определяются как timestamp последней минутной свечи
        и timestamp свечи, находящейся от опорной точки
        на временном расстоянии, равном произведению
        запрашиваемых глубины и интервала
        '''
        last_interval = self.__get_last_interval__()
        if last_interval:
            first_edge = (
                last_interval['begin'] - self.interval*self.depth * 60
                )
            last_edge = last_interval['end']
            data_edges = {"begin": first_edge, "end": last_edge}
            logging.info(
                f"Function __get_data_edges__ :\n"
                f"last_interval {last_interval}\n"
                f"first_edge_data {first_edge} "
                f"({dt.fromtimestamp(first_edge).strftime('%d-%m %H:%M')})\n"
                f"last_edge_data {last_edge} "
                f"({dt.fromtimestamp(last_edge).strftime('%d-%m %H:%M')})\n"
                f"data_edges {data_edges}"
                )
            return data_edges
        else:
            return False

    def get_raw_data(self):
        '''
        Метод возращает сырые данные из базы данных.
        Тип возвращаемых данных - список сло словарями,
        содержащими параметры минутных свечей.
        Начало и конец данных определяются методом
        __get_data_edges__()
        '''
        data_edges = self.__get_data_edges__()
        if data_edges:
            raw_data_list = []
            logging.info(
                f"Function get_raw_data :\n"
                f"data_edges {data_edges}\n"
                f"raw_data_list {raw_data_list}"
                )
            try:
                with self.__connection_to_base__() as conn:
                    with conn.cursor() as curs:
                        curs.execute(
                            f'SELECT * FROM {self.table_name} '
                            f'WHERE "Timestamp" >= {data_edges["begin"]} '
                            f'ORDER BY "Timestamp"'
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
                logging.info(
                    f"Function get_raw_data complete. "
                    f"raw_data_list consists of "
                    f"{len(raw_data_list)} elements"
                    )
                return raw_data_list
            except psycopg2.Error as e:
                logging.error(f"get_raw_data Error\n{e}")
                return False
        else:
            return False

    def __check_raw_data__(self): pass

    def get_new_candles_sql(self): pass

    def make_new_candles_dict(self):
        '''
        Метод из полученных через get_raw_data()
        минутных свечей собирает свечи с заданным интервалом
        и возращает список словарей с параметрами новых свечей.
        '''
        raw_data = self.get_raw_data()

        if raw_data:
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
                if (item["Timestamp"] < candle_end_time and not
                        item["Timestamp"] == raw_data[-1]["Timestamp"]):
                    if item["High"] > candle_high:
                        candle_high = item["High"]
                    if item["Low"] < candle_low:
                        candle_low = item["Low"]
                    candle_vol += item["Volume"]
                elif item["Timestamp"] >= candle_end_time:
                    candle_list[i].update({
                        "Close": raw_data[id-1]["Close"],
                        "High": candle_high,
                        "Low": candle_low,
                        "Volume": candle_vol})
                    i += 1
                    candle_time = item["Timestamp"]
                    candle_open = item["Open"]
                    candle_high = item["High"]
                    candle_low = item["Low"]
                    candle_vol = 0
                    candle_list.append(
                        {"Timestamp": candle_time, "Open": candle_open})
                elif item["Timestamp"] == raw_data[-1]["Timestamp"]:
                    candle_list[i].update({
                        "Close": raw_data[id-1]["Close"],
                        "High": candle_high,
                        "Low": candle_low,
                        "Volume": candle_vol})
            logging.info(
                f"Function make_new_candles_dict complete."
                f"candle_list consists of "
                f"{len(candle_list)} elements"
                )
            return candle_list
        else:
            return False

    # def __convert_timestamp__(self, timestamp_data: int):
    #     this_time = dt.fromtimestamp(timestamp_data)
    #     if this_time.hour == 0 and this_time.minute == 0:
    #         new_time = this_time.strftime('%d-%m %H:%M')
    #     else:
    #         new_time = this_time.strftime('%H:%M')
    #     return new_time

    def __convert_timestamp__(self, timestamp_data: int):
        new_time = dt.fromtimestamp(timestamp_data)
        return new_time

    def data_for_plotly(self):
        '''
        Метод из полученных через get_raw_data()
        минутных свечей собирает свечи с заданным интервалом
        и возращает словарь с параметрами новых свечей.
        Данный словарь будет пригоден для использования
        в библиотеке plotly
        '''
        raw_data = self.get_raw_data()

        if raw_data:
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

                if (item["Timestamp"] < candle_end_time and
                        not item["Timestamp"] == raw_data[-1]["Timestamp"]):
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

            plot_data = {
                "datetime": time_list,
                "open": open_list,
                "close": close_list,
                "high": high_list,
                "low": low_list,
                "volume": vol_list
                }
            logging.info(
                f"Function data_for_plotly complete."
                f"Plot_data consists of {len(plot_data['datetime'])} elements"
                )
            return plot_data
        else:
            return False


if __name__ == "__main__":
    test = CryptoData("BTCUSD", 30, 50)
    raw_data = test.get_raw_data()
    candle_data = test.make_new_candles_dict()
    plot_data = test.data_for_plotly()
    time_now = now.strftime('%Y-%m-%d_%H_%M')
    fname = f"{os.getcwd()}/logs/csv/{time_now}__{test.symbol}_{test.interval}"

    def csv_writer(f_name, data, data_name):
        file_name = f"{f_name}_{data_name}.csv"
        with open(file_name, "w", newline='') as out_file:
            writer = csv.DictWriter(out_file, delimiter='\t', fieldnames=[
                        "Timestamp", "Open", "Close", "High", "Low", "Volume"])
            writer.writeheader()
            for row in data:
                writer.writerow(row)

    csv_writer(fname, raw_data, "raw_data")
    csv_writer(fname, candle_data, "candle_data")

    with open(f"{fname}_plot_data.csv", "w", newline='') as out_file:
        writer = csv.DictWriter(out_file, delimiter='\t', fieldnames=[
                        "datetime", "open", "close", "high", "low", "volume"])
        writer.writeheader()
        length = len(plot_data["datetime"])
        for i in range(0, length-1):
            row = {
                "datetime": plot_data["datetime"][i],
                "open": plot_data["open"][i],
                "close": plot_data["close"][i],
                "high": plot_data["high"][i],
                "low": plot_data["low"][i],
                "volume": plot_data["volume"][i],
            }
            writer.writerow(row)
