import json
import math
import pandas as pd
import requests
import time
from datetime import datetime


# Класс для выгрузки данных с биржи 

class DataCrypto:

    # ТИП: Спот (можно добавить фьючерсы)
    MARKET = {
        "SPOT": "https://api.binance.com/api/v3"
    }

    # ТАЙМФРЕЙМ
    TF = {
        "1m": 1,
        "5m": 5,
        "15m": 15,
        "30m": 30,
        "1h": 60,
        "4h": 240,
        "1d": 1440
    }

    # Переменные для работы
    _limit = None
    _limit_max = None
    _request_count = None
    _market = None
    _t_d, _f_d = None, None
    _t, _f, _tf, _sym = None, None, None, None

   
    def __init__(self, market, sym, tf, f, t):
        self._sym = sym
        self._tf = tf
        self._market = market

        # Максимальное кол-во баров
        self._limit_max = 1000

        # Обрабатываем и конвертируем дату начала
        self._t = datetime.strptime(t, '%Y-%m-%d %H:%M:%S')
        self._t_d = str(datetime.strftime(self._t, '_%Y%m%d_%H%M_'))
        self._t = int(datetime.timestamp(self._t))

        # Обрабатываем и конвертируем дату окончания
        self._f = datetime.strptime(f, '%Y-%m-%d %H:%M:%S')
        self._f_d = str(datetime.strftime(self._f, '_%Y%m%d_%H%M'))
        self._f = int(datetime.timestamp(self._f))

        # Рассчитываем кол-во баров необходимых для закрытия переданных дат
        self._limit = int((self._t - self._f) / (self.TF[self._tf] * 60))

        # Рассчитывем кол-во запросов исходя из максимального кол-ва баров
        self._request_count =  math.ceil(self._limit / self._limit_max)

    # Функция загрузки данных
    def load(self):
        payload={}
        headers = {'Content-Type': 'application/json'}
        data = list()
        cur_limit = self._limit_max if self._request_count > 1 else self._limit
        cur_f = self._f
        cur_t = self._f + cur_limit * (self.TF[self._tf] * 60)
        for r in range(0, self._request_count):
            url = "{}/klines?symbol={}&interval={}&limit={}&startTime={}&endTime={}".format(
                self.MARKET[self._market], 
                self._sym, 
                self._tf, 
                cur_limit, 
                "{}000".format(cur_f), 
                "{}000".format(cur_t)
                )
            self._limit -= self._limit_max
            cur_limit = cur_limit if self._limit >= self._limit_max else self._limit
            cur_f = cur_t
            cur_t = cur_t + cur_limit * (self.TF[self._tf] * 60)
            response = requests.request("GET", url, headers=headers, data=payload)
            if response.status_code == 200:
                d = json.loads(response.text)
                data.extend(d)
            # Сделаем паузу, чтобы не грузить биржу
            time.sleep(1.5)

        # Произведем постобработку списка
        for item in data:
            item[0] = int(str(item[0])[:-3])
            item.pop(11)
            item.pop(6)
    
        # Сформируем датафрейм и присвоим имена колонок
        df = pd.DataFrame(data, columns=[
            'Open time', 
            'Open', 
            'High', 
            'Low', 
            'Close', 
            'Volume', 
            'Quote asset volume',
            'Number of trades',
            'Taker buy base asset volume',
            'Taker buy quote asset volume'
        ])