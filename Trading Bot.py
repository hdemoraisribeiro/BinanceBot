import time
import math
import sqlite3
import requests
import pandas as pd
import sqlalchemy
import os
from dotenv import load_dotenv
from binance.client import Client
from datetime import datetime, timedelta

load_dotenv()

API_KEY = os.environ.get("API_KEY")
API_SECRET = os.environ.get("API_SECRET")
client = Client(API_KEY, API_SECRET)

db = sqlite3.connect('crypto.db')
try:
    db.cursor().execute("""
        CREATE TABLE inventory (
            symbol TEXT,
            avg_price REAL,
            qty REAL,
            buy_time REAL
        )""")
except:
    print("Table 'inventory' already exists")

try:
    db.cursor().execute("""
        CREATE TABLE block (
            symbol TEXT,
            unblocktime REAL
        )""")
except:
    print("Table 'block' already exists")

try:
    db.cursor().execute("""
        CREATE TABLE history (
            symbol TEXT,
            avg_price REAL,
            qty REAL,
            buy_time REAL,
            sell_time REAL,
            profit REAL
        )""")
except:
    print("Table 'history' already exists")

db.commit()
db.close()

def fetchall(table='inventory'):
    db = sqlite3.connect('crypto.db')
    cursor = db.cursor()
    cursor.execute(f"SELECT * FROM {table}")
    alldata = cursor.fetchall()
    db.commit()
    db.close()
    return alldata

def extract_from_tuple(alldata, i=0):
    symbols = [x[i] for x in alldata]
    return symbols

def execute(command):
    db = sqlite3.connect('crypto.db')
    cursor = db.cursor()
    cursor.execute(command)
    db.commit()
    db.close()

def add_to_db(symbol, price, qty):
    time = int(datetime.utcnow().strftime('%d%H%M%S'))
    execute(f"INSERT INTO inventory VALUES ('{symbol}',{price},{qty},{time})")
    print(f"Bought {qty} units of {symbol} at ${price:.2f}")

def delete_from_db(symbol, price, qty, profit):
    execute(f"DELETE FROM inventory WHERE symbol = '{symbol}'")
    print(f"Sold {qty} units of {symbol} at ${price:.2f}. Profit {profit:.2f}%")
    block(symbol)

def get_data(symbol, table='inventory'):
    db = sqlite3.connect('crypto.db')
    cursor = db.cursor()
    cursor.execute(f"SELECT * FROM {table} WHERE symbol = '{symbol}'")
    data = cursor.fetchone()
    db.commit()
    db.close()
    return data

def buy_symbol(symbol, fund):
    price = float(client.get_symbol_ticker(symbol=symbol)['price'])
    fund = 10 if fund < 10 else fund  # $10 is minimum

    buy_quantity = fund / price # How many coins for ${fund}
    details = client.get_symbol_info(symbol)['filters'][2]
    minQty = float(details['minQty'])
    stepSize = float(details['stepSize'])

    # qty = minimum + stepSize x n,
    # Valid quantity value closest to buy_quantity
    qty = float(round(minQty + (stepSize*math.ceil((buy_quantity-minQty)/stepSize)),8))

    try:
        order = client.create_order(
            symbol=symbol, side="BUY", type="MARKET", quantity=qty)
        print(order)
        add_to_db(symbol, price, qty)
    except Exception as e:
        print("Buy order error")
        print(e)


def sell_symbol(symbol):
    qty = get_data(symbol)[2]
    price = float(client.get_symbol_ticker(symbol=symbol)['price'])
    buy_price = get_data(symbol)[1]
    profit = float("{:.4f}".format(((price-buy_price)/buy_price)*100))
    try:
        order = client.create_order(
            symbol=symbol, side="SELL", type="MARKET", quantity=qty)
        print(order)
        delete_from_db(symbol, price, qty, profit)
    except Exception as e:
        print("Sell order error")
        print(e)


def block(symbol):
    time = int((datetime.utcnow() + timedelta(hours=1)).strftime('%d%H%M%S'))
    execute(f"INSERT INTO block VALUES ('{symbol}',{time})")


def sell_all():
    inventory = extract_from_tuple(fetchall())
    for symbol in inventory:
        sell_symbol(symbol)

def spot_balance():
    sum_btc = 0.0
    while(True):
        try:
            balances = client.get_account()["balances"]
            break
        except:
            pass
    for _balance in balances:
        asset = _balance["asset"]
        if float(_balance["free"]) != 0.0 or float(_balance["locked"]) != 0.0:
            balance = float(_balance["free"]) + float(_balance["locked"])
            if asset == "BTC":
                sum_btc += balance
            else:
                symbol = asset + "BTC"
                while(True):
                    try:
                        _price = client.get_symbol_ticker(symbol=symbol)
                        sum_btc += balance * float(_price["price"])
                        break
                    except Exception as e:
                        if 'Invalid symbol' in str(e):
                            _price = client.get_symbol_ticker(symbol='BTC'+asset)
                            sum_btc += balance / float(_price["price"])

    while(True):
        try:
            current_btc_price_USD = client.get_symbol_ticker(symbol="BTCUSDT")["price"]
            break
        except Exception as e:
            print(e)
    own_usd = sum_btc * float(current_btc_price_USD)
    return own_usd

def start():
    inventory = extract_from_tuple(fetchall())
    with open('output/selected_symbols.txt', 'r') as file:
        file.seek(0)  # Ensure you're at the start of the file..
        first_char = file.read(1)  # Get the first character
        if not first_char:
            pass  # The first character is the empty string..
        else:
            # The first character wasn't empty. Return to the start of the file.
            file.seek(0)
            # Use file now
            list_of_symbols = file.readline().split(',')
            with open('output/selected_symbols.txt', 'w') as f:
                f.write('')

            # Buying
            blocked = extract_from_tuple(fetchall('block'))
            for symbol in list_of_symbols:
                if (symbol not in inventory) & (symbol not in blocked):
                    # Minimum funds $10
                    buy_symbol(symbol, 15)

    # Selling
    for symbol in inventory:
        buy_time = get_data(symbol)[3]
        time = int((datetime.utcnow()-timedelta(minutes=15)).strftime('%d%H%M%S'))
        # If more than 15 minutes have passed
        if(time >= buy_time):
            sell_symbol(symbol)

    # Unblocking
    blocked = fetchall('block')
    time = int(datetime.utcnow().strftime('%d%H%M%S'))
    for item in blocked:
        if item[1] <= time:
            execute(f"DELETE FROM block WHERE symbol = '{item[0]}'")


print("Program starts")

balance = spot_balance()

try:
    while(True):
        time.sleep(5)
        try:
            start()
        except requests.exceptions.ReadTimeout:
            print("Timeout occured")
        except requests.exceptions.ConnectionError:
            print("ConnectionError occured")
            time.sleep(10)
            
        if balance*1.02 <= spot_balance():
            sell_all()
            print("Target acheived")
            break
except KeyboardInterrupt:
    print("KeyboardInterrupt occured")
# Run this to sell all symbols in the inventory
# sell_all()
