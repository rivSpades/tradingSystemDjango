from datetime import date
import numpy as np
import pandas as pd
from django.db import models
from .utils import StrategyUtils
from backtesting.models import TradeHistory
from symbols.models import Symbols, DailyPrice

class MeanRevertingStrategy:
    def __init__(self, parameters):
        self.parameters = parameters

    def execute(self, df, buy=False, last_action=""):
        """
        Executes the mean-reverting strategy on the given DataFrame.
        Determines whether to go LONG, SHORT, or EXIT.
        """
        df = StrategyUtils.calculate_ratio(df)

        if df["ratio"].dropna().empty:
            return "None"

        percentiles = [5, 10, 50, 90, 95]
        p = np.percentile(df["ratio"].dropna(), percentiles)

        if not StrategyUtils.check_stationary(df):
            return "None"  # Only trade if stationary

        if not buy and df["ratio"].iloc[-1] <= p[0]:
            return "Long"

        elif not buy and df["ratio"].iloc[-1] >= p[-1]:
            return "Short"

        elif buy and df["ratio"].iloc[-1] >= p[2] and last_action == "Long":
            return "Exit"

        elif buy and df["ratio"].iloc[-1] <= p[2] and last_action == "Short":
            return "Exit"

        return "None"

    def backtest(self, backtest, ticker, start_date, end_date=date.today()):
        """
        Simulates market data updates by looping through future data,
        making trade decisions at each step.
        """
        buy = False
        last_action = ""

        # Fetch symbol
        try:
            symbol = Symbols.objects.get(ticker=ticker)
        except Symbols.DoesNotExist:
            return f"Symbol {ticker} not found in database."

        # Fetch historical price data
        historical_data = DailyPrice.objects.filter(
            symbol=symbol, price_date__range=[start_date, end_date]
        ).order_by("price_date")

        if not historical_data.exists():
            return f"No data found for {ticker} between {start_date} and {end_date}."

        # Convert to DataFrame
        df = pd.DataFrame.from_records(
            historical_data.values(
                "price_date", "open_price", "high_price", "low_price", "close_price", "volume"
            )
        )
        df.rename(
            columns={
                "price_date": "Date",
                "open_price": "Open",
                "high_price": "High",
                "low_price": "Low",
                "close_price": "Close",
                "volume": "Volume",
            },
            inplace=True,
        )

        # Split Data
        current_data, future_data = StrategyUtils.train_test_split(df, split_ratio=0.5)

        # Backtest loop
        for i in range(len(future_data.index)):
            # Append new data
            current_data = pd.concat([current_data, pd.DataFrame(future_data.iloc[i]).transpose()], axis=0)

            # Check for signals
            signal = self.execute(current_data, buy, last_action)

            if signal == "Long" and not buy:
                buy = True
                last_action = "Long"
                TradeHistory.objects.create(
                    backtest=backtest,
                    symbol=symbol,
                    entry_date=future_data["Date"].iloc[i],
                    action="Long",
                    entry_price=future_data["Close"].iloc[i],
                    quantity=100,
                )

            elif signal == "Short" and not buy:
                buy = True
                last_action = "Short"
                TradeHistory.objects.create(
                    backtest=backtest,
                    symbol=symbol,
                    entry_date=future_data["Date"].iloc[i],
                    action="Short",
                    entry_price=future_data["Close"].iloc[i],
                    quantity=100,
                )

            elif signal == "Exit" and buy:
                # Fetch the last open trade from the database
                last_trade = TradeHistory.objects.filter(
                    backtest=backtest, symbol=symbol, exit_date__isnull=True
                ).order_by("-entry_date").first()

                if last_trade:
                    exit_price = future_data["Close"].iloc[i]
                    profit_loss = (
                        (exit_price - last_trade.entry_price) * last_trade.quantity
                        if last_trade.action == "Long"
                        else (last_trade.entry_price - exit_price) * last_trade.quantity
                    )

                    # Update last trade with exit details
                    last_trade.exit_date = future_data["Date"].iloc[i]
                    last_trade.exit_price = exit_price
                    last_trade.profit_loss = profit_loss
                    last_trade.save()

                    # Create a new record for the exit action
                    TradeHistory.objects.create(
                        backtest=backtest,
                        symbol=symbol,
                        entry_date=last_trade.entry_date,
                        exit_date=future_data["Date"].iloc[i],
                        action="Exit",
                        entry_price=last_trade.entry_price,
                        exit_price=exit_price,
                        quantity=last_trade.quantity,
                        profit_loss=profit_loss,
                    )

                buy = False
                last_action = ""

        return f"Backtest completed for {ticker} ({start_date} - {end_date})."
