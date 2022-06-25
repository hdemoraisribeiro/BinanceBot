# Function for printing to files
def print_file(ls, file):
    with open(f'output/{file}.txt','w') as file:
        file.write(str(ls)[1:-1].replace(' ','').replace('\'',''))
        
def get_price(ls):
    return ((float(ls[1]) + float(ls[4])) / 2)

# Function for getting percent change
def get_percent_change(ls_1, ls_2):
    change = (get_price(ls_2) - get_price(ls_1)) / get_price(ls_1) * 100
    return float("{:.4f}".format(change))

# Function for flitering symbols
def filter_symbol(list_of_symbols):
    selected_symbols = []
    calls=0
    for symbol in list_of_symbols:
        while True:
            try:
                now_time = datetime.now()
                prev_time = now_time - timedelta(hours=12)
                klines = client.get_historical_klines(symbol, Client.KLINE_INTERVAL_1MINUTE, str(prev_time), str(now_time))

                _6hrs, _1hr, _30mins = get_percent_change(klines[0], klines[-1]), get_percent_change(klines[299], klines[-1]), get_percent_change(klines[329], klines[-1])

                if (_6hrs > 6) & (_1hr > 3) & (_30mins > 1):
                    selected_symbols.append(symbol)
                    print(f"{symbol}->\t6hrs: {_6hrs:.2f}%\t1hr: {_1hr:.2f}%\t30min: {_30mins:.2f}%")
                calls+=1
                break
                
            except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
                print(e)
                time.sleep(5)
                pass
    print(f"{calls} API calls made")
    print_file(selected_symbols,'filtered')
    
    if(len(selected_symbols)>0):
        print_file(selected_symbols,'selected_symbols')

# Import Libraries & Load Environment Variables
import time
import requests
import pandas as pd
import sqlalchemy, os
from binance import BinanceSocketManager
from binance.client import Client
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("API_KEY")
API_SECRET = os.environ.get("API_SECRET")

# Binance Client
client = Client(API_KEY, API_SECRET)

with open('output/pairs.txt','r') as file:
    list_of_symbols = file.readline().split(',')
    
print("Live Data Script starts")

def start():
    while True:
        try:
            _24hrs = [item for item in [item['symbol'] for item in client.get_ticker() if float(item['priceChangePercent'])>10.0] if (item in list_of_symbols)] # CALL
            break
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
            print(e)
            pass
    
    if(len(_24hrs)>0):
        filter_symbol(_24hrs)
try:
    while(True):
        start_time = datetime.utcnow()
        start()
        # time.sleep(5)
        end_time = datetime.utcnow()
        print(end_time - start_time)
        print('')
except KeyboardInterrupt:
    print("KeyboardInterrupt occured")