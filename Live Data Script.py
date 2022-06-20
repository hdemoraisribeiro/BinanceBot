# Function for printing to files
def print_file(ls, file):
    with open(str(file)+'.txt','w') as file:
        file.write(str(ls)[1:-1].replace(' ','').replace('\'',''))
        
# Function for getting price
def get_price(ls):
    avg = (float(ls[1]) + float(ls[4])) / 2
    return avg

# Function for getting percent change in 6 hour
def get_percent_change(ls_1, ls_2):
    change = (get_price(ls_2) - get_price(ls_1)) / get_price(ls_1) * 100
    return float("{:.4f}".format(change))

# Function for flitering symbols using threshold
def filter_symbol(level, list_of_symbols, threshold, time):
    now_time = datetime.now()
    prev_time = now_time - time
    selected_symbols = []

    for symbol in list_of_symbols:
        klines = client.get_historical_klines(symbol, Client.KLINE_INTERVAL_1MINUTE, str(prev_time), str(now_time))

        percent_change = get_percent_change(klines[0], klines[-1])

        if percent_change > threshold:
            selected_symbols.append(symbol)
            if(level==4):
                print(f"{symbol}: {percent_change}% ${get_price(klines[0])}")
    print_file(selected_symbols,'pairs_level_'+str(level))
    if(level==4) & (len(selected_symbols)>0):
        print('---------------------------\n')
    return selected_symbols

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

list_symbols_USDT = [item["symbol"] for item in client.get_exchange_info()["symbols"] if ("USDT" in item["symbol"]) & ("DOWN" not in item["symbol"])]
print_file(list_symbols_USDT,'pairs')

print("Live Data Script starts")

# ### Main Code
def start():
    level1 = [item for item in [item['symbol'] for item in client.get_ticker() if float(item['priceChangePercent'])>10.0] if ('USDT' in item) & ('DOWN' not in item)]
    print_file(level1,'pairs_level_1')
    
    if(len(level1)>0):
        
        # print("Level 2 - 6hrs window")
        level2 = filter_symbol(2, level1, 6, timedelta(hours=12)) #filter_symbol (level, list_of_symbols, threshold, timedelta)
        
        if(len(level2)>0):
            # print("\nLevel 3 - 1hrs window") 
            level3 = filter_symbol(3, level2, 3, timedelta(hours=7))
            
            if(len(level3)>0):
                # print('\nLevel 4 - 30min window')
                level4 = filter_symbol(4, level3, 1, timedelta(minutes=390))
                # print('\n Finish iteration\n')

while(True):
    time.sleep(5)
    try:
        start()
    except requests.exceptions.ReadTimeout:
        print("Timeout occured")
    except requests.exceptions.ConnectionError:
        print("ConnectionError occured")
        time.sleep(10)