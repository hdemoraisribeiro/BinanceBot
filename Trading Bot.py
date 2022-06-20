import time
import math
import sqlite3
import requests
import pandas as pd
import sqlalchemy, os
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

def extract_from_tuple(alldata, i = 0):
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
    
def delete_from_db(symbol,price,qty,profit):
    execute(f"DELETE FROM inventory WHERE symbol = '{symbol}'")
    print(f"Sold {qty} units of {symbol} at ${price:.2f}. Profit {profit:.2f}%")
    block(symbol)

def get_data(symbol,table='inventory'):
    db = sqlite3.connect('crypto.db')
    cursor = db.cursor()
    cursor.execute(f"SELECT * FROM {table} WHERE symbol = '{symbol}'")
    data = cursor.fetchone()
    db.commit()
    db.close()
    return data

def buy_symbol(symbol,fund):
    price = client.get_symbol_ticker(symbol=symbol)['price']
    fund = 10 if fund<10 else fund # $10 is minimum
    
    buy_quantity = fund / float(price) # How many coins for ${fund}
    minQty = float(client.get_symbol_info(symbol)['filters'][2]['minQty'])
    stepSize = float(client.get_symbol_info(symbol)['filters'][2]['stepSize'])

    # qty = minimum + stepSize x n, 
    qty = minQty + (stepSize*math.ceil((buy_quantity-minQty)/stepSize)) # Valid quantity value closest to buy_quantity
    
    try:
        order = client.create_order(symbol=symbol, side="BUY", type="MARKET", quantity=qty)
        print(order)
        add_to_db(symbol,price,qty)
    except Exception as e:
        print("Buy order failed")
        print(e)
    

def sell_symbol(symbol):
    qty=get_data(symbol)[2]
    price = client.get_symbol_ticker(symbol=symbol)['price']
    buy_price = get_data(symbol)[1]
    profit = float("{:.4f}".format(((price-buy_price)/buy_price)*100))
    try:
        order = client.create_test_order(symbol=symbol, side="SELL", type="MARKET", quantity=qty)
        print(order)
        delete_from_db(symbol,price,qty,profit)
    except Exception as e:
        print("Sell order failed")
        print(e)
    
def block(symbol):
    time = int((datetime.utcnow() + timedelta(hours=1)).strftime('%d%H%M%S'))
    execute(f"INSERT INTO block VALUES ('{symbol}',{time})")
    
def sell_all():
    inventory = extract_from_tuple(fetchall())
    for symbol in inventory:
        sell_symbol(symbol)

def start():
    inventory = extract_from_tuple(fetchall())
    with open('selected_symbols.txt','r') as file:
        file.seek(0) # Ensure you're at the start of the file..
        first_char = file.read(1) # Get the first character
        if not first_char:
            pass # The first character is the empty string..
        else:
            file.seek(0) # The first character wasn't empty. Return to the start of the file.
             # Use file now
            list_of_symbols = file.readline().split(',')
            with open('selected_symbols.txt','w') as f:
                f.write('')
            
            # Buying
            blocked = extract_from_tuple(fetchall('block'))
            for symbol in list_of_symbols:
                if (symbol not in inventory) & (symbol not in blocked):
                    # Minimum funds $10
                    buy_symbol(symbol,10)
            
    # Selling
    for symbol in inventory:
        buy_time = get_data(symbol)[3]
        time = int(datetime.utcnow().strftime('%d%H%M%S'))
        # If more than 15 minutes have passed
        if(time >= buy_time + 1500):
            sell_symbol(symbol)
            
    # Unblocking
    blocked = fetchall('block')
    time = int(datetime.utcnow().strftime('%d%H%M%S'))
    for item in blocked:
        if item[1] <= time:
            execute(f"DELETE FROM block WHERE symbol = '{item[0]}'")

print("Program starts")

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
except KeyboardInterrupt:
    print("KeyboardInterrupt occured")
# Run this to sell all symbols in the inventory
# sell_all()