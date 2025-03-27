from .strategy_logic import MeanRevertingStrategy
from symbols.models import DailyPrice
import pandas as pd
import numpy as np
import statsmodels.tsa.stattools as ts
from hurst import compute_Hc
STRATEGY_CLASSES = {
    "mean-reverting": MeanRevertingStrategy,

}

def get_strategy_executor(strategy):
    """Returns the correct strategy class based on slug."""
    strategy_class = STRATEGY_CLASSES.get(strategy.slug)
    if strategy_class:
        return strategy_class(strategy.parameters)
    raise ValueError(f"Unknown strategy slug: {strategy.slug}")




class StrategyUtils:
    """
    Utility class for strategy-related statistical functions.
    """


    @staticmethod
    def check_adf(df):
        """
        Perform the Augmented Dickey-Fuller test for stationarity.
        Returns True if the time series is stationary.
        """
        if df.empty or 'close_price' not in df.columns:
            return False

        df['close_price'] = df['close_price'].astype(float)

        if df['close_price'].std() == 0:
            return False  # No variance, can't be stationary

        try:
            results = ts.adfuller(df['close_price'], 1)
            critical_value = results[0]
            p_value = results[1]
            t_values = results[4]  # Critical values at different confidence levels

            return p_value < 0.05 and critical_value < t_values['1%'] and critical_value < t_values['5%'] and critical_value < t_values['10%']
        except:
            return False

    @staticmethod
    def check_hurst(df):
        """
        Calculate the Hurst exponent to check for mean-reverting behavior.
        Returns True if the exponent suggests mean reversion.
        """
        if df.empty or 'close_price' not in df.columns:
            return False

        asset_prices = np.array(df['close_price'].astype(float))

        if np.any(asset_prices == 0):
            asset_prices = asset_prices[asset_prices != 0]

        if len(asset_prices) < 100:
            return False  # Need at least 100 data points

        try:
            H, _, _ = compute_Hc(asset_prices, kind='price')
            return H < 0.5  # Mean-reverting if H < 0.5
        except:
            return False

    @staticmethod
    def check_stationary(df):
        """
        Check stationarity by combining ADF and Hurst tests.
        """
        adf_result = StrategyUtils.check_adf(df)

        if not adf_result:
            return False  # ADF test failed, not stationary

        return StrategyUtils.check_hurst(df)

    @staticmethod
    def moving_average(df, n):
        """
        Calculate a simple moving average.
        """
        if df.empty or 'close_price' not in df.columns:
            return df

        df['MA_' + str(n)] = df['close_price'].rolling(n, min_periods=n).mean()
        return df
    @staticmethod
    def calculate_ratio(df):
        """ Calculate the ratio of close price to its 100-day moving average. """
        ma = 100
        df = StrategyUtils.moving_average(df, ma)
        
        # Ensure numeric conversion
        df['close_price'] = pd.to_numeric(df['close_price'], errors='coerce')
        df[f'MA_{ma}'] = pd.to_numeric(df[f'MA_{ma}'], errors='coerce')

        # Calculate ratio and avoid division by zero
        df['ratio'] = df['close_price'] / df[f'MA_{ma}']
        df['ratio'].fillna(1, inplace=True)  # Fill NaN values with 1
        return df

    @staticmethod
    def train_test_split(df, split_ratio=0.5):
        """ Split dataset into training and testing sets. """
        split_index = int(len(df) * split_ratio)
        current_data = df.iloc[:split_index]
        future_data = df.iloc[split_index:]
        return current_data, future_data
        