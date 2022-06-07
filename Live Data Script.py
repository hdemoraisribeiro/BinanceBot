# Getting symbols (Level 1)
def get_all_pairs():
    try:
        exchange_info = client.get_exchange_info()["symbols"]
    except:
        return None

    # This'll contain all symbols in Binance that has USDT
    list_symbols_USDT = []
    symbols_USDT = ""

    for item in exchange_info:
        symbol = item["symbol"]

        if "USDT" in symbol:
            symbols_USDT += symbol + ","
            list_symbols_USDT.append(symbol)

    symbols_USDT = symbols_USDT[:-1]

    with open("pairs.txt", "w") as file:
        file.write(symbols_USDT.replace('\'','').replace(' ',''))
    
    return list_symbols_USDT


# Filter - percent change in 24hrs
def filter1(symbols):
    try:
        info = client.get_ticker()
    except:
        return None
    
    all_change_pair = {} # All symbols paired with corresponding 24hrs change percentile
    USDT_change_pair = {} # All symbols with USDT paired with corresponding 24hrs change percentile
    level1 = [] # List of symbols with more than x% change within 24hrs

    for item in info:
        all_change_pair[item["symbol"]] = float(item["priceChangePercent"])

    for item in all_change_pair:
        if item in symbols:
            USDT_change_pair[item] = all_change_pair[item]

    # Sort by 24hrs change percentage
    sorted_USDT_change_pair = {
        pair[0]: pair[1]
        for pair in sorted(USDT_change_pair.items(), key=lambda x: x[1], reverse=True)
    }

    for item in sorted_USDT_change_pair.items():
        
        if item[1] > 10.0:
            level1.append(item[0])
            print(item[0],item[1])

    with open("pairs_level_1.txt", "w") as file:
        file.write(str(level1)[1:-1].replace('\'','').replace(' ',''))

    # level1 contains the list of symbols that pass the first criteria
    return level1

# Function for getting price
def get_price(ls):
    avg = (float(ls[1]) + float(ls[4])) / 2
    price = float("{:.4f}".format(avg))
    return price


# Function for getting percent change in 6 hour
def get_percent_change(ls_1, ls_2):
    price_1 = get_price(ls_1)
    price_2 = get_price(ls_2)

    change = (price_2 - price_1) / price_1

    change_in_percent = float("{:.4f}".format(change * 100))

    return change_in_percent

# Function for flitering symbols using threshold
def filter_symbol(level, list_of_symbols, threshold, window):
    from datetime import datetime, timedelta

    selected_symbols = []

    for symbol in list_of_symbols:
        try:
            klines = client.get_historical_klines(
                symbol,
                Client.KLINE_INTERVAL_1MINUTE,
                str(datetime.now() - timedelta(hours=window)),
                str(datetime.now()),
            )
        except:
            continue

        percent_change = get_percent_change(klines[0], klines[-1])

        if percent_change > threshold:
            selected_symbols.append(symbol)
            print(symbol, percent_change)
            
    with open("pairs_level_"+str(level)+".txt", "w") as file:
        file.write(str(selected_symbols)[1:-1].replace('\'','').replace(' ',''))
        
    return selected_symbols


# Import Libraries & Load Environment Variables
import time
import pandas as pd
import sqlalchemy, os
from binance import BinanceSocketManager
from binance.client import Client
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("API_KEY")
API_SECRET = os.environ.get("API_SECRET")

# Binance Client
client = Client(API_KEY, API_SECRET)

# Main Code
def start():
    list_symbols_USDT = get_all_pairs()
    print("Level 1 - 24hrs window")
    level1 = filter1(list_symbols_USDT)
    print("\nLevel 2 - 6hrs window")
    level2 = filter_symbol(2, level1, 6, 12) #filter_symbol (level, list_of_symbols, threshold, window)
    print("\nLevel 3 - 1hrs window")
    level3 = filter_symbol(3, level2, 3, 7)
    print('\n Finish iteration\n')

while(True):
    start()