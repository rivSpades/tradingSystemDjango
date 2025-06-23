import requests
from symbols.models import Exchange,Symbols,Broker
class BrokerUtils:
    def __init__(self, broker_name, api_key, secret_key, use_paper=True):
        self.broker_name = broker_name
        self.api_key = api_key
        self.secret_key = secret_key
        self.use_paper = use_paper  # For Alpaca: True = paper trading; False = live
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

    def close_position(self, symbol):
        if self.broker_name == "Alpaca":
            symbol = symbol.replace("/", "")  # Sanitize symbol if needed
            url = f"https://paper-api.alpaca.markets/v2/positions/{symbol}"
            response = requests.delete(url, headers=self.headers)
            return response.json()
        raise NotImplementedError(f"close_position not implemented for {self.broker_name}")


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