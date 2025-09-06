import requests
from symbols.models import Exchange,Symbols,Broker
import pandas as pd
from datetime import datetime, date,timedelta
import hmac
import hashlib
import time
from urllib.parse import urlencode

class BrokerUtils:
    def __init__(self, broker_name, api_key, secret_key, use_paper=True):
        self.broker_name = broker_name
        self.api_key = api_key
        self.secret_key = secret_key
        self.use_paper = use_paper  # For Alpaca: True = paper trading; False = live
        
        # Set up headers based on broker
        if self.broker_name == "Alpaca":
            self.base_url = "https://paper-api.alpaca.markets"
            self.headers = {
                "accept": "application/json",
                "APCA-API-KEY-ID": self.api_key,
                "APCA-API-SECRET-KEY": self.secret_key
            }
        elif self.broker_name == "Binance":
            self.base_url = "https://api.binance.com"
            self.headers = {
                "X-MBX-APIKEY": self.api_key
            }
        else:
            self.base_url = ""
            self.headers = {}

    def _generate_binance_signature(self, params):
        """Generate signature for Binance API requests"""
        query_string = urlencode(params)
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature

    def _get_binance_headers(self, params=None):
        """Get headers for Binance API requests"""
        headers = {"X-MBX-APIKEY": self.api_key}
        if params and self.secret_key:
            signature = self._generate_binance_signature(params)
            params['signature'] = signature
        return headers

   


    def get_account_info(self):
        if self.broker_name == "Alpaca":
            url = "https://paper-api.alpaca.markets/v2/account"
            response = requests.get(url, headers=self.headers)
            return response.json()
        elif self.broker_name == "Binance":
            return self._get_binance_account_info()
        else:
            raise NotImplementedError(f"get_account_info not implemented for {self.broker_name}")

    def _get_binance_account_info(self):
        """Get account information from Binance"""
        try:
            params = {
                'timestamp': int(time.time() * 1000)
            }

            signature = self._generate_binance_signature(params)
            params['signature'] = signature

            url = f"{self.base_url}/api/v3/account"
            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()

            account_data = response.json()
            
            # Convert Binance account format to match Alpaca format
            total_balance = 0
            for balance in account_data.get('balances', []):
                if float(balance['free']) > 0 or float(balance['locked']) > 0:
                    # You might want to get current prices to calculate total value
                    total_balance += float(balance['free']) + float(balance['locked'])

            return {
                'account_number': account_data.get('accountType', 'SPOT'),
                'status': 'ACTIVE' if account_data.get('permissions') else 'INACTIVE',
                'currency': 'USDT',
                'buying_power': str(total_balance),
                'regt_buying_power': str(total_balance),
                'daytrading_buying_power': str(total_balance),
                'non_marginable_buying_power': str(total_balance),
                'cash': str(total_balance),
                'accrued_fees': '0',
                'pending_transfer_out': '0',
                'pending_transfer_in': '0',
                'portfolio_value': str(total_balance),
                'pattern_day_trader': False,
                'trading_blocked': False,
                'transfers_blocked': False,
                'account_blocked': False,
                'created_at': account_data.get('updateTime'),
                'trade_suspended_by_user': False,
                'multiplier': '1',
                'shorting_enabled': True,
                'equity': str(total_balance),
                'last_equity': str(total_balance),
                'long_market_value': str(total_balance),
                'short_market_value': '0',
                'initial_margin': '0',
                'maintenance_margin': '0',
                'last_maintenance_margin': '0',
                'sma': '0',
                'daytrade_count': 0
            }

        except requests.exceptions.RequestException as e:
            print(f"Error fetching account info from Binance: {e}")
            return {"error": str(e)}
        except Exception as e:
            print(f"An error occurred while fetching Binance account info: {e}")
            return {"error": str(e)}

    def create_order(self, symbol, qty, side, type_order="market", time_in_force="gtc"):
        print(self.broker_name)
        print(self.headers)
        print(symbol)
        if self.broker_name == "Alpaca":
           
            if side=="LONG":
                side="buy"
            elif side=="SHORT":
                side="sell" 

            payload = {
                "symbol": symbol,
                "qty": qty,
                "side": side,
                "type": type_order,
                "time_in_force": time_in_force
            }

            url = "https://paper-api.alpaca.markets/v2/orders"

            response = requests.post(url, json=payload, headers=self.headers)
            return response.json()
        elif self.broker_name == "Binance":
            return self._create_binance_order(symbol, qty, side, type_order, time_in_force)
        else:
            raise NotImplementedError(f"create_order not implemented for {self.broker_name}")

    def _create_binance_order(self, symbol, qty, side, type_order="MARKET", time_in_force="GTC"):
        """Create order on Binance"""
        try:
            # Convert symbol format for Binance API
            symbol_pair = self._convert_symbol_for_binance(symbol)
            
            print(f"Converting symbol {symbol} to {symbol_pair} for Binance order")

            # Convert side to Binance format
            if side == "LONG":
                side = "BUY"
            elif side == "SHORT":
                side = "SELL"

            # Prepare parameters
            params = {
                'symbol': symbol_pair,
                'side': side,
                'type': type_order,
                'quantity': qty,
                'timestamp': int(time.time() * 1000)
            }

            if type_order == "LIMIT":
                params['timeInForce'] = time_in_force

            # Generate signature
            signature = self._generate_binance_signature(params)
            params['signature'] = signature

            # Make request
            url = f"{self.base_url}/api/v3/order"
            response = requests.post(url, params=params, headers=self.headers)
            response.raise_for_status()

            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"Error creating order on Binance: {e}")
            return {"error": str(e)}
        except Exception as e:
            print(f"An error occurred while creating Binance order: {e}")
            return {"error": str(e)}
    
    def create_order_pair(self, symbol_1,symbol_2, qty_1,qty_2, side, type_order="market", time_in_force="gtc"):

        if self.broker_name == "Alpaca":
            qty_1=int(round(qty_1,0))
            qty_2=int(round(qty_2,0))

            if qty_1==0 or qty_2==0:
                raise NotImplementedError(f"create_order not implemented for {self.broker_name}. Quantities not valid")    
            
            if side=="LONG":

                self.create_order(symbol_1,qty_1,"SHORT")
                self.create_order(symbol_2,qty_2,"LONG")
                
            elif side=="SHORT": 

                self.create_order(symbol_1,qty_1,"LONG")
                self.create_order(symbol_2,qty_2,"SHORT")

        

    def close_position(self, symbol):
        if self.broker_name == "Alpaca":
            symbol = symbol.replace("/", "")  # Sanitize symbol if needed
            url = f"https://paper-api.alpaca.markets/v2/positions/{symbol}"
            response = requests.delete(url, headers=self.headers)
            return response.json()
        elif self.broker_name == "Binance":
            return self._close_binance_position(symbol)
        else:
            raise NotImplementedError(f"close_position not implemented for {self.broker_name}")

    def _close_binance_position(self, symbol):
        """Close position on Binance"""
        try:
            # Convert symbol format for Binance API
            symbol_pair = self._convert_symbol_for_binance(symbol)
            
            print(f"Converting symbol {symbol} to {symbol_pair} for Binance position close")

            # First, get current position
            params = {
                'symbol': symbol_pair,
                'timestamp': int(time.time() * 1000)
            }

            signature = self._generate_binance_signature(params)
            params['signature'] = signature

            # Get account info to find position
            url = f"{self.base_url}/api/v3/account"
            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()

            account_info = response.json()
            
            # Find the position for this symbol
            for balance in account_info.get('balances', []):
                if balance['asset'] in symbol_pair and float(balance['free']) > 0:
                    # Create a market sell order to close position
                    close_params = {
                        'symbol': symbol_pair,
                        'side': 'SELL',
                        'type': 'MARKET',
                        'quantity': balance['free'],
                        'timestamp': int(time.time() * 1000)
                    }

                    close_signature = self._generate_binance_signature(close_params)
                    close_params['signature'] = close_signature

                    close_url = f"{self.base_url}/api/v3/order"
                    close_response = requests.post(close_url, params=close_params, headers=self.headers)
                    close_response.raise_for_status()

                    return close_response.json()

            return {"message": "No position found to close"}

        except requests.exceptions.RequestException as e:
            print(f"Error closing position on Binance: {e}")
            return {"error": str(e)}
        except Exception as e:
            print(f"An error occurred while closing Binance position: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def bars_to_df(bars):
        
        df = pd.DataFrame(bars)
        
        # Rename the columns
        df.rename(
            columns={
                "t": "Date",
                "o": "Open",
                "h": "High",
                "l": "Low",
                "c": "Close",
                "v": "Volume",
            },
            inplace=True,
        )

        # Convert 'Date' column to datetime objects
        df["Date"] = pd.to_datetime(df["Date"])

        # Set the 'Date' column as the index
        
        df.reset_index(inplace=True)

        return df

    def get_daily_price(self,symbol, start_date, end_date=None):
        
        if end_date is None:
            end_date = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')

        if self.broker_name == "Binance":
            return self._get_binance_daily_price(symbol, start_date, end_date)
        elif self.broker_name == "Alpaca":
            return self._get_alpaca_daily_price(symbol, start_date, end_date)
        else:
            # Fallback to CryptoCompare for crypto symbols
            return self._get_cryptocompare_daily_price(symbol, start_date, end_date)

    def _convert_symbol_for_binance(self, ticker):
        """Convert ticker format to Binance API format"""
        # Remove any hyphens and convert to uppercase
        symbol_pair = ticker.replace('-', '').upper()
        
     
        
        return symbol_pair

    def _get_binance_daily_price(self, symbol, start_date, end_date):
        """Get daily price data from CryptoCompare API for Binance symbols"""
        try:
            # Use CryptoCompare API for Binance symbols
            api_key_crypto = '22a78314e3f7625b24ea2f67cf802d28cae94db3bbaf61cf0c3437ff0df8f97e'
            
            # Parse the symbol to get base and quote currencies
            if '-' in symbol.ticker:
                fsym, tsym = symbol.ticker.split('-')
           
            
            print(f"Fetching data for {fsym}-{tsym} from CryptoCompare API")
            
            # CryptoCompare API endpoint for daily historical data
            url = f'https://min-api.cryptocompare.com/data/v2/histoday'
            params = {
                'fsym': fsym,
                'tsym': tsym,
                'limit': 2000,  # Maximum limit for daily data
                'api_key': api_key_crypto
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            
            if data.get('Response') == 'Error':
                print(f"CryptoCompare API error: {data.get('Message', 'Unknown error')}")
                return pd.DataFrame()
            
            if not data.get('Data', {}).get('Data'):
                print(f"No data found for {symbol.ticker} in the specified date range.")
                return pd.DataFrame()

            # Convert CryptoCompare data to DataFrame
            prices = pd.DataFrame(data['Data']['Data'])
            
            # Convert timestamp to datetime
            prices['Date'] = pd.to_datetime(prices['time'], unit='s')
            
            # Rename columns to match expected format
            prices.rename(columns={
                'open': 'Open',
                'high': 'High', 
                'low': 'Low',
                'close': 'Close',
                'volumeto': 'Volume'
            }, inplace=True)
            
            # Add Adj Close column (same as Close for crypto)
            prices['Adj Close'] = prices['Close']
            
            # Filter by date range if specified
            if start_date:
                start_dt = pd.to_datetime(start_date)
                prices = prices[prices['Date'] >= start_dt]
            
            if end_date:
                end_dt = pd.to_datetime(end_date)
                prices = prices[prices['Date'] <= end_dt]
            
            # Select and reorder columns to match expected format
            result_df = prices[['Date', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']]
            
            print(f"Retrieved {len(result_df)} daily price records for {symbol.ticker}")
            return result_df

        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from CryptoCompare API: {e}")
            return pd.DataFrame()
        except Exception as e:
            print(f"An error occurred while fetching CryptoCompare data: {e}")
            return pd.DataFrame()

    def _get_alpaca_daily_price(self, symbol, start_date, end_date):
        """Get daily price data from Alpaca API"""
        url = f"https://data.alpaca.markets/v2/stocks/{symbol.ticker}/bars?timeframe=1D&start={start_date}&end={end_date}&limit=10000&adjustment=raw&feed=sip&sort=asc"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status() 

            data = response.json()
            
            bars_data = data.get("bars")
            
            if bars_data:
                df = self.bars_to_df(bars_data)
                return df
            else:
                print(f"No bars data found for ticker {symbol.ticker} in the specified date range.")
                return pd.DataFrame()

        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from Alpaca API: {e}")
            return pd.DataFrame()
        except Exception as e:
            print(f"An error occurred: {e}")
            return pd.DataFrame()

    def _get_cryptocompare_daily_price(self, symbol, start_date, end_date):
        """Get daily price data from CryptoCompare API (fallback)"""
        api_key_crypto = '22a78314e3f7625b24ea2f67cf802d28cae94db3bbaf61cf0c3437ff0df8f97e' 
        if symbol.instrument == "CRYPTO":
            fsym, tsym = symbol.ticker.split('-')
            url = f'https://min-api.cryptocompare.com/data/v2/histoday?fsym={fsym}&tsym={tsym}&limit=2000&api_key={api_key_crypto}'
            response = requests.get(url)

            if response.status_code == 200:
                try:
                    data = response.json()['Data']['Data']
                except:
                    print(f"Failed to fetch daily prices for {symbol} from CryptoCompare")
                    return pd.DataFrame() 
                prices = pd.DataFrame(data)
                prices['time'] = pd.to_datetime(prices['time'], unit='s')
                prices.rename(columns={'time': 'Date', 'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volumeto': 'Volume'}, inplace=True)
                prices['Adj Close'] = prices['Close']  # For cryptocurrencies, adjusted close is typically the same as close
                return prices[['Date', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']][:-1]
            else:
                print(f"Failed to fetch daily prices for {symbol} from CryptoCompare")
                return pd.DataFrame()
        else:
            return pd.DataFrame()

    def last_minute_bar(self,ticker):
        if self.broker_name == "Alpaca":
            url = f"https://data.alpaca.markets/v2/stocks/{ticker}/bars/latest"
            response = requests.get(url, headers=self.headers)
            data = response.json()

            bars_data = data.get("bar")

            if bars_data:
                # Wrap the single bar dictionary in a list
                df = self.bars_to_df([bars_data])
                return df
            return pd.DataFrame()
        elif self.broker_name == "Binance":
            return self._get_binance_last_minute_bar(ticker)
        else:
            return pd.DataFrame()

    def _get_binance_last_minute_bar(self, ticker):
        """Get the latest minute bar from Binance API"""
        try:
            # Convert symbol format for Binance API
            symbol_pair = self._convert_symbol_for_binance(ticker)
            
            print(f"Converting symbol {ticker} to {symbol_pair} for Binance latest minute bar")

            # Get the latest kline (1 minute interval)
            url = f"{self.base_url}/api/v3/klines"
            params = {
                'symbol': symbol_pair,
                'interval': '1m',  # 1 minute candles
                'limit': 1
            }

            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()

            data = response.json()
            
            if not data:
                return pd.DataFrame()

            # Convert Binance klines data to DataFrame
            df = pd.DataFrame(data, columns=[
                'open_time', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])

            # Convert timestamp to datetime
            df['Date'] = pd.to_datetime(df['open_time'], unit='ms')
            
            # Convert string values to float
            df['Open'] = df['open'].astype(float)
            df['High'] = df['high'].astype(float)
            df['Low'] = df['low'].astype(float)
            df['Close'] = df['close'].astype(float)
            df['Volume'] = df['volume'].astype(float)

            # Select and reorder columns to match expected format
            result_df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
            
            return result_df

        except requests.exceptions.RequestException as e:
            print(f"Error fetching latest minute bar from Binance API: {e}")
            return pd.DataFrame()
        except Exception as e:
            print(f"An error occurred while fetching Binance latest minute bar: {e}")
            return pd.DataFrame()


    def enable_assets(self):
        broker = Broker.objects.get(name=self.broker_name)
        if self.broker_name =="Alpaca":
            url = f"{self.base_url}/v2/assets?status=active&asset_class=us_equity&attributes="
            response = requests.get(url, headers=self.headers)

            if response.status_code != 200:
                raise Exception(f"Failed to fetch assets from Alpaca: {response.text}")

            assets = response.json()
            
            for asset in assets:
                if asset.get("tradable", False):
                    symbol = asset.get("symbol")
                    name = asset.get("name", "")
                    print(symbol)
                    exchange_name = asset.get("exchange", "UNKNOWN")
                    shortable = asset.get("shortable", False)
                    # Get or create Exchange
                    exchange, _ = Exchange.objects.get_or_create(name=exchange_name)

                    # Update or create Symbol
                    symbol_obj, created = Symbols.objects.get_or_create(
                        ticker=symbol,
                        defaults={
                            "instrument": "stock",
                            "name": name,
                            "ticker":symbol,
                            "exchange": exchange,
                            "active": True,
                            "slot_free": True,
                            "long":True,
                            "short":shortable,
                            "broker":broker,
                        }
                    )

                    if not created: #means already exists
                        symbol_obj.active = True
                        symbol_obj.broker = broker
                        symbol_obj.long  = True
                        symbol_obj.short = shortable
                        symbol_obj.save()

        elif self.broker_name=="Binance":
            url = "https://data-api.binance.vision/api/v3/exchangeInfo"
            response = requests.get(url, headers=self.headers)
            data = response.json()
            
            for symbol in data["symbols"]:

                exchange_name = "CRYPTO "+symbol["quoteAsset"]
                exchange, _ = Exchange.objects.get_or_create(name=exchange_name)   

                ticker=symbol["baseAsset"]+"-"+symbol["quoteAsset"]
                symbol_obj, created = Symbols.objects.get_or_create(
                ticker=ticker,
                defaults={
                    "instrument": "CRYPTO",
                    "name": ticker,
                    "ticker":ticker,
                    "exchange": exchange,
                    "active": (symbol["isSpotTradingAllowed"] or symbol["isMarginTradingAllowed"]) and symbol["status"] == "TRADING",
                    "slot_free": True,
                    "long":True,
                    "short":symbol["isMarginTradingAllowed"],
                    "broker":broker,
                }
            )

            if not created: #means already exists
                symbol_obj.active = True
                symbol_obj.broker = broker
                symbol_obj.long  = True
                symbol_obj.short = symbol["isMarginTradingAllowed"]
                symbol_obj.save()               
          
         