{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": 1,
   "id": "b6a137f8-bdb6-4956-8c37-eac26f135e3c",
   "metadata": {},
   "outputs": [],
   "source": [
    "import pandas as pd\n",
    "import sqlalchemy, os\n",
    "import requests\n",
    "from binance import BinanceSocketManager\n",
    "from binance.client import Client\n",
    "from dotenv import load_dotenv\n",
    "from datetime import datetime, timedelta\n",
    "\n",
    "load_dotenv()\n",
    "\n",
    "API_KEY = os.environ.get(\"API_KEY\")\n",
    "API_SECRET = os.environ.get(\"API_SECRET\")\n",
    "\n",
    "client = Client(API_KEY, API_SECRET)\n",
    "# client = Client()"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 2,
   "id": "e31e217c-66c3-4940-a302-b1885d46ad08",
   "metadata": {},
   "outputs": [],
   "source": [
    "import sqlite3\n",
    "\n",
    "db = sqlite3.connect('crypto.db')\n",
    "\n",
    "cursor = db.cursor()\n",
    "\n",
    "try:\n",
    "    cursor.execute(\"\"\"\n",
    "        CREATE TABLE test (\n",
    "            symbol TEXT,\n",
    "            avg_price REAL,\n",
    "            qty INTEGER,\n",
    "            buy_time REAL\n",
    "        )\"\"\")\n",
    "except:\n",
    "    print(\"Table test already exists\")\n",
    "\n",
    "try:\n",
    "    cursor.execute(\"\"\"\n",
    "        CREATE TABLE test2 (\n",
    "            symbol TEXT,\n",
    "            unblocktime REAL\n",
    "        )\"\"\")\n",
    "except:\n",
    "    print(\"Table test2 already exists\")\n",
    "\n",
    "db.commit()\n",
    "db.close()"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 3,
   "id": "9b14d654-cb97-48f5-b227-f5c643170a16",
   "metadata": {},
   "outputs": [],
   "source": [
    "# Function for printing to files\n",
    "def print_file(ls, file):\n",
    "    with open(str(file)+'.txt','w') as file:\n",
    "        file.write(str(ls)[1:-1].replace(' ','').replace('\\'',''))\n",
    "        \n",
    "# Function for getting price\n",
    "def get_price(ls):\n",
    "    avg = (float(ls[1]) + float(ls[4])) / 2\n",
    "    return avg\n",
    "\n",
    "# Function for getting percent change in 6 hour\n",
    "def get_percent_change(ls_1, ls_2):\n",
    "    change = (get_price(ls_2) - get_price(ls_1)) / get_price(ls_1) * 100\n",
    "    return float(\"{:.4f}\".format(change))\n",
    "\n",
    "# Function for flitering symbols using threshold\n",
    "def filter_symbol(level, list_of_symbols, threshold, time):\n",
    "    now_time = datetime.now()\n",
    "    prev_time = now_time - time\n",
    "    selected_symbols = []\n",
    "\n",
    "    for symbol in list_of_symbols:\n",
    "        klines = client.get_historical_klines(symbol, Client.KLINE_INTERVAL_1MINUTE, str(prev_time), str(now_time))\n",
    "\n",
    "        percent_change = get_percent_change(klines[0], klines[-1])\n",
    "\n",
    "        if percent_change > threshold:\n",
    "            selected_symbols.append(symbol)\n",
    "            if(level==4):\n",
    "                print(f\"{symbol}: {percent_change}% ${get_price(klines[0])}\")\n",
    "    print_file(selected_symbols,'pairs_level_'+str(level))\n",
    "    if(level==4) & (len(selected_symbols)>0):\n",
    "        print_file(selected_symbols,'selected_symbols')\n",
    "        print('---------------------------\\n')\n",
    "    return selected_symbols"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 4,
   "id": "228745ec-d569-4b9c-9cae-a5b9e9a6c210",
   "metadata": {},
   "outputs": [],
   "source": [
    "def fetchall(table='test'):\n",
    "    db = sqlite3.connect('crypto.db')\n",
    "    cursor = db.cursor()\n",
    "    cursor.execute(f\"SELECT * FROM {table}\")\n",
    "    alldata = cursor.fetchall()\n",
    "    db.commit()\n",
    "    db.close()\n",
    "    return alldata\n",
    "\n",
    "def extract_from_tuple(alldata, i = 0):\n",
    "    symbols = [x[i] for x in alldata]\n",
    "    return symbols\n",
    "\n",
    "def execute(command):\n",
    "    db = sqlite3.connect('crypto.db')\n",
    "    cursor = db.cursor()\n",
    "    cursor.execute(command)\n",
    "    db.commit()\n",
    "    db.close()\n",
    "    \n",
    "def add_to_db(symbol, price, qty):\n",
    "    time = int(datetime.utcnow().strftime('%d%H%M%S'))\n",
    "    execute(f\"INSERT INTO test VALUES ('{symbol}',{price},{qty},{time})\")\n",
    "    print(f\"Bought {qty} units of {symbol} at ${price:.2f}\")\n",
    "\n",
    "def delete_from_db(symbol,price,qty,profit):\n",
    "    # execute(f\"DELETE FROM test WHERE symbol = '{symbol}'\")\n",
    "    print(f\"Sold {qty} units of {symbol} at ${price:.2f}. Profit {profit:.2f}%\")\n",
    "    \n",
    "def get_data(symbol,table='test'):\n",
    "    db = sqlite3.connect('crypto.db')\n",
    "    cursor = db.cursor()\n",
    "    cursor.execute(f\"SELECT * FROM {table} WHERE symbol = '{symbol}'\")\n",
    "    data = cursor.fetchone()\n",
    "    db.commit()\n",
    "    db.close()\n",
    "    return data\n",
    "\n",
    "def extract_from_tuple(alldata, i = 0):\n",
    "    symbols = [x[i] for x in alldata]\n",
    "    return symbols\n",
    "\n",
    "def block(symbol):\n",
    "    time = int((datetime.utcnow() + timedelta(hours=1)).strftime('%d%H%M%S'))\n",
    "    execute(f\"INSERT INTO block VALUES ('{symbol}',{time})\")"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "9ea76f80-51de-4670-b278-c3f637a33618",
   "metadata": {},
   "outputs": [],
   "source": [
    "# date_1 = datetime.utcnow().strftime('%y %m %d %H:%M:%S.%f')\n",
    "# date_2 = datetime.utcnow().strftime('%d%H%M%S%f')\n",
    "date_1 = datetime.utcnow().strftime('%y %m %d %H:%M:%S')\n",
    "date_2 = datetime.utcnow().strftime('%d%H%M%S')\n",
    "print(date_1)\n",
    "print(int(date_2))"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 9,
   "id": "5ec267ab-2d5c-427f-8d51-d9c8e50ac1bf",
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "13\n"
     ]
    }
   ],
   "source": [
    "#First get ETH price\n",
    "eth_price = client.get_symbol_ticker(symbol=\"ETHUSDT\")\n",
    "\n",
    "# Calculate how much ETH $200 can buy\n",
    "buy_quantity = round(200 / float(eth_price['price']))\n",
    "\n",
    "# Create test order\n",
    "order = client.create_test_order(\n",
    "        symbol='ETHUSDT',\n",
    "        side=Client.SIDE_BUY,\n",
    "        type=Client.ORDER_TYPE_MARKET,\n",
    "        quantity=buy_quantity\n",
    "    )\n",
    "\n",
    " # The 200 in buy_quantity is the amount of money you want to spend on ETH.\n"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 61,
   "id": "1f8e26c3-2b78-4073-8b82-21832672a014",
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "448.70000000\n",
      "1196.29800688\n"
     ]
    }
   ],
   "source": [
    "price = client.get_symbol_ticker(symbol=\"BCCUSDT\")['price']\n",
    "print(price)\n",
    "price = float(client.get_avg_price(symbol=\"ETHUSDT\")['price'])\n",
    "print(price)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 7,
   "id": "d32f5c0d-aa21-4125-bdc6-3282ef246f9a",
   "metadata": {
    "scrolled": true,
    "tags": []
   },
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "symbol DOGEUSDT\n",
      "status TRADING\n",
      "baseAsset DOGE\n",
      "baseAssetPrecision 8\n",
      "quoteAsset USDT\n",
      "quotePrecision 8\n",
      "quoteAssetPrecision 8\n",
      "baseCommissionPrecision 8\n",
      "quoteCommissionPrecision 8\n",
      "orderTypes ['LIMIT', 'LIMIT_MAKER', 'MARKET', 'STOP_LOSS_LIMIT', 'TAKE_PROFIT_LIMIT']\n",
      "icebergAllowed True\n",
      "ocoAllowed True\n",
      "quoteOrderQtyMarketAllowed True\n",
      "allowTrailingStop True\n",
      "cancelReplaceAllowed False\n",
      "isSpotTradingAllowed True\n",
      "isMarginTradingAllowed True\n",
      "filters [{'filterType': 'PRICE_FILTER', 'minPrice': '0.00001000', 'maxPrice': '1000.00000000', 'tickSize': '0.00001000'}, {'filterType': 'PERCENT_PRICE', 'multiplierUp': '5', 'multiplierDown': '0.2', 'avgPriceMins': 5}, {'filterType': 'LOT_SIZE', 'minQty': '1.00000000', 'maxQty': '9000000.00000000', 'stepSize': '1.00000000'}, {'filterType': 'MIN_NOTIONAL', 'minNotional': '10.00000000', 'applyToMarket': True, 'avgPriceMins': 5}, {'filterType': 'ICEBERG_PARTS', 'limit': 10}, {'filterType': 'MARKET_LOT_SIZE', 'minQty': '0.00000000', 'maxQty': '16552468.66597222', 'stepSize': '0.00000000'}, {'filterType': 'TRAILING_DELTA', 'minTrailingAboveDelta': 10, 'maxTrailingAboveDelta': 2000, 'minTrailingBelowDelta': 10, 'maxTrailingBelowDelta': 2000}, {'filterType': 'MAX_NUM_ORDERS', 'maxNumOrders': 200}, {'filterType': 'MAX_NUM_ALGO_ORDERS', 'maxNumAlgoOrders': 5}]\n",
      "permissions ['SPOT', 'MARGIN']\n",
      "\n",
      "\n",
      "{'filterType': 'PRICE_FILTER', 'minPrice': '0.00001000', 'maxPrice': '1000.00000000', 'tickSize': '0.00001000'}\n",
      "{'filterType': 'PERCENT_PRICE', 'multiplierUp': '5', 'multiplierDown': '0.2', 'avgPriceMins': 5}\n",
      "{'filterType': 'LOT_SIZE', 'minQty': '1.00000000', 'maxQty': '9000000.00000000', 'stepSize': '1.00000000'}\n",
      "{'filterType': 'MIN_NOTIONAL', 'minNotional': '10.00000000', 'applyToMarket': True, 'avgPriceMins': 5}\n",
      "{'filterType': 'ICEBERG_PARTS', 'limit': 10}\n",
      "{'filterType': 'MARKET_LOT_SIZE', 'minQty': '0.00000000', 'maxQty': '16552468.66597222', 'stepSize': '0.00000000'}\n",
      "{'filterType': 'TRAILING_DELTA', 'minTrailingAboveDelta': 10, 'maxTrailingAboveDelta': 2000, 'minTrailingBelowDelta': 10, 'maxTrailingBelowDelta': 2000}\n",
      "{'filterType': 'MAX_NUM_ORDERS', 'maxNumOrders': 200}\n",
      "{'filterType': 'MAX_NUM_ALGO_ORDERS', 'maxNumAlgoOrders': 5}\n",
      "------------------------------------------------------------------------------------------------\n",
      "{'filterType': 'LOT_SIZE', 'minQty': '1.00000000', 'maxQty': '9000000.00000000', 'stepSize': '1.00000000'}\n"
     ]
    }
   ],
   "source": [
    "info = client.get_exchange_info()['symbols']\n",
    "for symbol in info:\n",
    "    if 'DOGEUSDT' in symbol['symbol']:\n",
    "        for j in symbol:\n",
    "            print(j,symbol[j])\n",
    "        print('\\n')\n",
    "        for item in symbol['filters']:\n",
    "            print(item)\n",
    "# pricePrecision = info['symbols'][0]['pricePrecision']\n",
    "# print(pricePrecision)\n",
    "print(\"------------------------------------------------------------------------------------------------\")\n",
    "ticker = client.get_symbol_info(\"DOGEUSDT\")['filters'][2]\n",
    "print(ticker)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 19,
   "id": "ef5efcca-75a3-472a-ba86-48cd995f563c",
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "{'symbol': 'CHRUSDT', 'orderId': 728550331, 'orderListId': -1, 'clientOrderId': 'hupXWtikPkFksvnXZE770i', 'transactTime': 1655715199569, 'price': '0.00000000', 'origQty': '57.00000000', 'executedQty': '57.00000000', 'cummulativeQuoteQty': '10.07190000', 'status': 'FILLED', 'timeInForce': 'GTC', 'type': 'MARKET', 'side': 'SELL', 'fills': [{'price': '0.17670000', 'qty': '57.00000000', 'commission': '0.00003588', 'commissionAsset': 'BNB', 'tradeId': 65667100}]}\n"
     ]
    }
   ],
   "source": [
    "order = client.create_order(symbol=\"CHRUSDT\", side=\"SELL\", type=\"MARKET\", quantity=57)\n",
    "print(order)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 97,
   "id": "3bb35205-ddeb-415d-8925-720b632825a6",
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "1970-01-20 10:02:59\n",
      "2022-06-25 23:48:58.906508\n"
     ]
    }
   ],
   "source": [
    "import time\n",
    "real_time(time.time())\n",
    "print((datetime.now()))"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 93,
   "id": "f6609c80-af12-4e59-8031-cc3224b4208b",
   "metadata": {},
   "outputs": [],
   "source": [
    "def real_time(epoch):\n",
    "    epoch = int(epoch/1000)\n",
    "    print(datetime.fromtimestamp(epoch).strftime('%Y-%m-%d %H:%M:%S'))"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 11,
   "id": "bf3e3a4c-4296-4924-bd85-4ecfb75e4413",
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "5.6e-05\n"
     ]
    }
   ],
   "source": [
    "start_time = datetime.utcnow()\n",
    "end_time = datetime.utcnow()\n",
    "print(float(str(end_time - start_time)[5:]))"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 5,
   "id": "8783db42-9417-470e-9ff3-79899778a53c",
   "metadata": {},
   "outputs": [],
   "source": [
    "data1 = client.get_symbol_ticker(symbol=\"BTCUSDT\")\n",
    "data2 = client.get_symbol_info(\"BTCUSDT\")"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 6,
   "id": "96d8eb07-2f51-4508-81f0-fef8730dca97",
   "metadata": {},
   "outputs": [
    {
     "data": {
      "text/plain": [
       "{'symbol': 'BTCUSDT', 'price': '20684.50000000'}"
      ]
     },
     "execution_count": 6,
     "metadata": {},
     "output_type": "execute_result"
    }
   ],
   "source": [
    "data1"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 7,
   "id": "beac42ae-c77b-4047-b2f6-9f180e8b18bd",
   "metadata": {},
   "outputs": [
    {
     "data": {
      "text/plain": [
       "{'symbol': 'BTCUSDT',\n",
       " 'status': 'TRADING',\n",
       " 'baseAsset': 'BTC',\n",
       " 'baseAssetPrecision': 8,\n",
       " 'quoteAsset': 'USDT',\n",
       " 'quotePrecision': 8,\n",
       " 'quoteAssetPrecision': 8,\n",
       " 'baseCommissionPrecision': 8,\n",
       " 'quoteCommissionPrecision': 8,\n",
       " 'orderTypes': ['LIMIT',\n",
       "  'LIMIT_MAKER',\n",
       "  'MARKET',\n",
       "  'STOP_LOSS_LIMIT',\n",
       "  'TAKE_PROFIT_LIMIT'],\n",
       " 'icebergAllowed': True,\n",
       " 'ocoAllowed': True,\n",
       " 'quoteOrderQtyMarketAllowed': True,\n",
       " 'allowTrailingStop': True,\n",
       " 'cancelReplaceAllowed': False,\n",
       " 'isSpotTradingAllowed': True,\n",
       " 'isMarginTradingAllowed': True,\n",
       " 'filters': [{'filterType': 'PRICE_FILTER',\n",
       "   'minPrice': '0.01000000',\n",
       "   'maxPrice': '1000000.00000000',\n",
       "   'tickSize': '0.01000000'},\n",
       "  {'filterType': 'PERCENT_PRICE',\n",
       "   'multiplierUp': '5',\n",
       "   'multiplierDown': '0.2',\n",
       "   'avgPriceMins': 5},\n",
       "  {'filterType': 'LOT_SIZE',\n",
       "   'minQty': '0.00001000',\n",
       "   'maxQty': '9000.00000000',\n",
       "   'stepSize': '0.00001000'},\n",
       "  {'filterType': 'MIN_NOTIONAL',\n",
       "   'minNotional': '10.00000000',\n",
       "   'applyToMarket': True,\n",
       "   'avgPriceMins': 5},\n",
       "  {'filterType': 'ICEBERG_PARTS', 'limit': 10},\n",
       "  {'filterType': 'MARKET_LOT_SIZE',\n",
       "   'minQty': '0.00000000',\n",
       "   'maxQty': '376.81848788',\n",
       "   'stepSize': '0.00000000'},\n",
       "  {'filterType': 'TRAILING_DELTA',\n",
       "   'minTrailingAboveDelta': 10,\n",
       "   'maxTrailingAboveDelta': 2000,\n",
       "   'minTrailingBelowDelta': 10,\n",
       "   'maxTrailingBelowDelta': 2000},\n",
       "  {'filterType': 'MAX_NUM_ORDERS', 'maxNumOrders': 200},\n",
       "  {'filterType': 'MAX_NUM_ALGO_ORDERS', 'maxNumAlgoOrders': 5}],\n",
       " 'permissions': ['SPOT', 'MARGIN']}"
      ]
     },
     "execution_count": 7,
     "metadata": {},
     "output_type": "execute_result"
    }
   ],
   "source": [
    "data2"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 1,
   "id": "7c08c68a-17d0-4025-a2b5-4d5d4cf0a49d",
   "metadata": {},
   "outputs": [],
   "source": [
    "import string\n",
    "import random"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 3,
   "id": "42510e33-042d-408e-a8ac-a66f7f411ab3",
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "U5r9N7mwmgjBLb11YWTv\n"
     ]
    }
   ],
   "source": [
    "s = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(20))\n",
    "\n",
    "print(s)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 4,
   "id": "a34fb947-842e-4da9-917b-abdddabf9d35",
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "1.32578935\n"
     ]
    }
   ],
   "source": [
    "num = 1.32578935487532098325\n",
    "print(float(round(num,8)))"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3 (ipykernel)",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.8.10"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 5
}
