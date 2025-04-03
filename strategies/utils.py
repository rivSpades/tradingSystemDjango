from symbols.models import DailyPrice, Symbols, Exchange
from .models import CorrelatedPair
import pandas as pd
import numpy as np
import statsmodels.tsa.stattools as ts
from statsmodels.tsa.vector_ar.vecm import coint_johansen
from hurst import compute_Hc

# STRATEGY_CLASSES = {
#     "mean-reverting": MeanRevertingStrategy,

# }

# def get_strategy_executor(strategy):
#     """Returns the correct strategy class based on slug."""
#     strategy_class = STRATEGY_CLASSES.get(strategy.slug)
#     if strategy_class:
#         return strategy_class(strategy.parameters)
#     raise ValueError(f"Unknown strategy slug: {strategy.slug}")




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
        if df.empty or 'Close' not in df.columns:
            return False

        df['Close'] = df['Close'].astype(float)

        if df['Close'].std() == 0:
            return False  # No variance, can't be stationary

        try:
            results = ts.adfuller(df['Close'], 1)
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
        if df.empty or 'Close' not in df.columns:
            return False

        asset_prices = np.array(df['Close'].astype(float))

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
        if df.empty or 'Close' not in df.columns:
            return df

        df['MA_' + str(n)] = df['Close'].rolling(n, min_periods=n).mean()
        return df
    @staticmethod
    def calculate_ratio(df):
        """ Calculate the ratio of close price to its 100-day moving average. """
        ma = 100
        df = StrategyUtils.moving_average(df, ma)
        
        # Ensure numeric conversion
        df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
        df[f'MA_{ma}'] = pd.to_numeric(df[f'MA_{ma}'], errors='coerce')

        # Calculate ratio and avoid division by zero
        df['ratio'] = df['Close'] / df[f'MA_{ma}']
        df['ratio'] = df['ratio'].fillna(1)
        return df

    @staticmethod
    def train_test_split(df, split_ratio=0.5):
        """ Split dataset into training and testing sets. """
        split_index = int(len(df) * split_ratio)
        current_data = df.iloc[:split_index]
        future_data = df.iloc[split_index:]
        return current_data, future_data
    
    @staticmethod
    def zscore(series):
        """Calculate the z-score of a given series."""
        return (series - series.mean()) / np.std(series)    

    @staticmethod
    def check_johansen_test(df1, df2):
        """
        Perform the Johansen test to check for cointegration between two time series.
        Returns True if cointegration is detected.
        """
        # Merge data on the index (assumes both have a date index)
        df_combined = pd.merge(
            df1[['Close']], df2[['Close']],
            left_index=True, right_index=True,
            suffixes=('_1', '_2')
        ).dropna()

        if df_combined.empty or len(df_combined) < 50:
            return False  # Not enough data for a valid test
        df_combined['Close_1'] = pd.to_numeric(df_combined['Close_1'], errors='coerce')
        df_combined['Close_2'] = pd.to_numeric(df_combined['Close_2'], errors='coerce')
        # Perform Johansen cointegration test
        johansen_result = coint_johansen(df_combined, det_order=0, k_ar_diff=1)

        # Extract Trace Statistic and Critical Values
        trace_stat = johansen_result.lr1
        crit_values = johansen_result.cvt

        # Check if Trace Statistic exceeds the 5% critical value
        cointegrated = any(trace_stat[i] > crit_values[i, 1] for i in range(len(crit_values[:, 1])))

        return cointegrated


    @staticmethod
    def find_highly_correlated_pairs():
        """
        Finds and saves highly correlated symbol pairs (corr > 0.98) for each exchange.
        """
        exchanges = Exchange.objects.all()  # Get all exchanges

        for exchange in exchanges:
            print(f"Processing exchange: {exchange.name}")

            symbols = Symbols.objects.filter(exchange=exchange)  # Get symbols for the exchange
            symbol_tickers = [symbol.ticker for symbol in symbols]

            if not symbol_tickers:
                print(f"No symbols found for {exchange.name}, skipping.")
                continue

            # Fetch daily close prices
            price_data = {}
            for ticker in symbol_tickers:
                prices = DailyPrice.objects.filter(symbol__ticker=ticker).order_by('price_date').values('price_date', 'close_price')
                price_data[ticker] = {price['price_date']: price['close_price'] for price in prices}

            # Convert to DataFrame
            data = pd.DataFrame(price_data)

            # Handle missing values
            data = data.ffill().bfill()

            # Calculate correlation matrix
            corr_matrix = data.corr()

            # Extract pairs with correlation > 0.98
            threshold = 0.90
            high_corr_pairs = [(s1, s2, round(corr_matrix.loc[s1, s2], 2))
                               for s1 in symbol_tickers for s2 in symbol_tickers
                               if s1 != s2 and corr_matrix.loc[s1, s2] > threshold and corr_matrix.loc[s1, s2] < 1.00]

            # Remove duplicate pairs
            unique_pairs = list(set(tuple(sorted(pair[:2])) + (pair[2],) for pair in high_corr_pairs))

            # Save results to database
            for symbol1_ticker, symbol2_ticker, correlation in unique_pairs:
                symbol1 = Symbols.objects.get(ticker=symbol1_ticker, exchange=exchange)
                symbol2 = Symbols.objects.get(ticker=symbol2_ticker, exchange=exchange)

                # Avoid duplicates
                _, created = CorrelatedPair.objects.update_or_create(
                    exchange=exchange,
                    symbol_1=symbol1,
                    symbol_2=symbol2,
                    defaults={"correlation": correlation}
                )

                if created:
                    print(f"Saved: {symbol1_ticker} & {symbol2_ticker} (Corr: {correlation})")
