import requests
from symbols.models import Exchange,Symbols,Broker
import pandas as pd
from datetime import datetime, date,timedelta

class BrokerUtils:
    def __init__(self, broker_name, api_key, secret_key, use_paper=True):
        self.broker_name = broker_name
        self.api_key = api_key
        self.secret_key = secret_key
        self.use_paper = use_paper  # For Alpaca: True = paper trading; False = live
        self.base_url = "https://paper-api.alpaca.markets"
        self.headers = {
                        "accept": "application/json",
                        "APCA-API-KEY-ID": self.api_key,  # Replace with your Alpaca API Key ID
                        "APCA-API-SECRET-KEY": self.secret_key # Replace with your Alpaca API Secret Key
                        }

   


    def get_account_info(self):
        url = "https://paper-api.alpaca.markets/v2/account"



        response = requests.get(url, headers=self.headers)
        return response.json()

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
        raise NotImplementedError(f"create_order not implemented for {self.broker_name}")
    
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
        raise NotImplementedError(f"close_position not implemented for {self.broker_name}")
    
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

    def get_daily_price(self,ticker, start_date, end_date=None):

        
        if end_date is None:
            end_date = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
        

        url = f"https://data.alpaca.markets/v2/stocks/{ticker}/bars?timeframe=1D&start={start_date}&end={end_date}&limit=10000&adjustment=raw&feed=sip&sort=asc"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status() 

            data = response.json()
            
            bars_data = data.get("bars")
            
            if bars_data:
                df= self.bars_to_df(bars_data)
                return df
            else:
                print(f"No bars data found for ticker {ticker} in the specified date range.")
                return pd.DataFrame()

        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from Alpaca API: {e}")
            return pd.DataFrame()
        except Exception as e:
            print(f"An error occurred: {e}")
            return pd.DataFrame()

    def last_minute_bar(self,ticker):
        url = f"https://data.alpaca.markets/v2/stocks/{ticker}/bars/latest"
        response = requests.get(url, headers=self.headers)
        data = response.json()

        bars_data = data.get("bar")

        if bars_data:
            # Wrap the single bar dictionary in a list
            df = self.bars_to_df([bars_data])
            return df
        return pd.DataFrame()


    def enable_assets(self):


        url = f"{self.base_url}/v2/assets?status=active&asset_class=us_equity&attributes="
        response = requests.get(url, headers=self.headers)

        if response.status_code != 200:
            raise Exception(f"Failed to fetch assets from Alpaca: {response.text}")

        assets = response.json()
        broker = Broker.objects.get(name=self.broker_name)
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