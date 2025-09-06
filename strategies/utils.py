from symbols.models import DailyPrice, Symbols, Exchange
from symbols.utils import DailyPriceManager
from .models import CorrelatedPair
import pandas as pd
import numpy as np
import statsmodels.tsa.stattools as ts
from statsmodels.tsa.vector_ar.vecm import coint_johansen
from hurst import compute_Hc
from scipy.signal import argrelextrema
from scipy.signal import find_peaks

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

        df['MA_' + str(n)] = df['Close'].rolling(int(n), min_periods=int(n)).mean()
        return df
    @staticmethod
    def calculate_ratio(df):
        """ Calculate the ratio of close price to its 100-day moving average. """
        ma = 100
        df = StrategyUtils.moving_average(df, ma)
        
        # Ensure numeric conversion with error handling
        df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
        df[f'MA_{ma}'] = pd.to_numeric(df[f'MA_{ma}'], errors='coerce')

        # Add validation to prevent underflow
        # Check for zero or very small moving average values
        min_ma_threshold = 1e-10  # Minimum threshold to prevent underflow
        
        # Replace very small or zero MA values with a safe minimum
        df[f'MA_{ma}'] = df[f'MA_{ma}'].replace([0, np.inf, -np.inf], np.nan)
        df[f'MA_{ma}'] = df[f'MA_{ma}'].fillna(df['Close'].mean() if not df['Close'].isna().all() else 1.0)
        
        # Ensure MA values are not too small
        df[f'MA_{ma}'] = np.maximum(df[f'MA_{ma}'], min_ma_threshold)
        
        # Check for zero or very small close prices
        df['Close'] = df['Close'].replace([0, np.inf, -np.inf], np.nan)
        df['Close'] = df['Close'].fillna(df[f'MA_{ma}'].mean() if not df[f'MA_{ma}'].isna().all() else 1.0)
        df['Close'] = np.maximum(df['Close'], min_ma_threshold)

        # Calculate ratio with additional safety checks
        try:
            df['ratio'] = df['Close'] / df[f'MA_{ma}']
            
            # Handle any remaining problematic values
            df['ratio'] = df['ratio'].replace([np.inf, -np.inf], np.nan)
            df['ratio'] = df['ratio'].fillna(1.0)  # Default to 1.0 for problematic ratios
            
            # Clip extreme values to prevent overflow
            max_ratio = 1000  # Maximum reasonable ratio
            min_ratio = 0.001  # Minimum reasonable ratio
            df['ratio'] = np.clip(df['ratio'], min_ratio, max_ratio)
            
        except Exception as e:
            print(f"Error calculating ratio: {e}")
            # Fallback: set all ratios to 1.0
            df['ratio'] = 1.0
            
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
            print("not enough data")
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
    def find_highly_correlated_pairs(exchange_name=None, threshold=0.90):
        """
        Finds and saves highly correlated symbol pairs for each exchange.
        
        Args:
            exchange_name (str, optional): Name of specific exchange to process
            threshold (float): Correlation threshold (default: 0.90)
        """
        if exchange_name:
            exchanges = Exchange.objects.filter(name = exchange_name)  # Get all exchanges 
        else:               
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
            for symbol in symbols:
                #DailyPriceManager.insert_daily_price(symbol,"2013-01-01")
                prices = DailyPrice.objects.filter(symbol__ticker=symbol.ticker).order_by('price_date').values('price_date', 'close_price')
                price_data[symbol.ticker] = {price['price_date']: price['close_price'] for price in prices}

            # Convert to DataFrame
            data = pd.DataFrame(price_data)

            # Handle missing values
            data = data.ffill().bfill()

            # Calculate correlation matrix
            corr_matrix = data.corr()

            # Extract pairs with correlation above threshold
            high_corr_pairs = [(s1, s2, round(corr_matrix.loc[s1, s2], 2))
                               for s1 in symbol_tickers for s2 in symbol_tickers
                               if s1 != s2 and corr_matrix.loc[s1, s2] > threshold and corr_matrix.loc[s1, s2] < 1.00]

            # Remove duplicate pairs
            unique_pairs = list(set(tuple(sorted(pair[:2])) + (pair[2],) for pair in high_corr_pairs))

            pairs_found = len(unique_pairs)
            print(f"Found {pairs_found} correlated pairs with threshold > {threshold}")

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
                else:
                    print(f"Updated: {symbol1_ticker} & {symbol2_ticker} (Corr: {correlation})")
            
            return pairs_found

    @staticmethod
    def peak_finder(df, column, p=0.50):
        """
        Identifies peaks and valleys in the given DataFrame and adds 'peak_max' and 'peak_min' columns.

        Parameters:
        df (pd.DataFrame): DataFrame containing market data.
        column (str): The column name to analyze for peaks and valleys.
        p (float): Percentile threshold for filtering significant peaks and valleys.

        Returns:
        pd.DataFrame: Updated DataFrame with 'peak_max' and 'peak_min' columns.
        """
        # Identify local maxima (peaks)
        localmax = find_peaks(df[column].values)[0]

        # Identify local minima (valleys) by inverting the signal
        localmin = find_peaks(-df[column].values)[0]

        # Create DataFrames for peaks and valleys
        df_peaks = pd.DataFrame({'date': df.iloc[localmax]['Date'], 'zigzag_y': df.iloc[localmax][column]})
        df_valleys = pd.DataFrame({'date': df.iloc[localmin]['Date'], 'zigzag_y': df.iloc[localmin][column]})

        # Combine and sort by date
        df_peaks_valleys = pd.concat([df_peaks, df_valleys], ignore_index=True).sort_values(by='date')

        # Apply separate threshold filtering
        threshold_max = df_peaks['zigzag_y'].quantile(p)   # Top percentile for peaks
        threshold_min = df_valleys['zigzag_y'].quantile(1 - p)  # Bottom percentile for valleys

        # Filter significant peaks and valleys
        filtered_peaks = df_peaks[df_peaks['zigzag_y'] > threshold_max]
        filtered_valleys = df_valleys[df_valleys['zigzag_y'] < threshold_min]

        # Extract dates of significant peaks and valleys
        valuesmax_dates = filtered_peaks['date'].tolist()
        valuesmin_dates = filtered_valleys['date'].tolist()

        # Assign peak and valley indicators
        df['peak_max'] = df['Date'].apply(lambda x: 1 if x in valuesmax_dates else -1)  # 1 for peaks
        df['peak_min'] = df['Date'].apply(lambda x: 1 if x in valuesmin_dates else -1)  # -1 for valleys

        return df
    
    @staticmethod    
    def get_ma_slope(df, ma_column, window=5):
        """
        Calculates the slope of a moving average over a specified window.

        Parameters:
        - df: DataFrame containing the moving average column.
        - ma_column: Column name for the moving average (e.g., 'MA_60').
        - window: Number of periods over which to calculate the slope.

        Returns:
        - A Pandas Series of slope values.
        """
        # Ensure numeric
        df = df.copy()
        df[ma_column] = pd.to_numeric(df[ma_column], errors='coerce')

        # Calculate slope: (MA_now - MA_n_periods_ago) / window
        slope = df[ma_column].diff(periods=window) / window

        return slope 
       
    @staticmethod        
    def is_slope_strong(slope_series, lookback=5):
        """
        Flags True only if all recent slopes in the window are positive.
        
        Parameters:
        - slope_series: pd.Series of slope values (from get_ma_slope)
        - lookback: number of periods to look back
        
        Returns:
        - pd.Series of booleans (True = strong trend, False = weak/mixed)
        """
        return slope_series.rolling(window=lookback).apply(lambda x: (x > 0).all(), raw=True).astype(bool)    
