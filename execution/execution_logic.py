import logging
from strategies.models import StrategySymbol,Strategy,CorrelatedPair
from strategies.strategy_logic import MeanRevertingStrategy,CoIntegrationStrategy
from symbols.models import Symbols,DailyPrice,Exchange,Broker
from django.db.models import Q
import pandas as pd
from datetime import date
from backtesting.models import BackTestingStrategy
from backtesting.utils import BackTestUtils
logger = logging.getLogger(__name__)

def execute_strategies(end_date=None, broker_name=None, exchange_name=None):
    """
    Execute strategies for active symbols
    
    Args:
        end_date: End date for strategy execution (default: today)
        broker_name: Filter by broker name (optional)
        exchange_name: Filter by exchange name (optional)
    """
    try:
        # Build base filter for symbols
        symbol_filter = Q(active=True)
        
        if broker_name:
            try:
                broker = Broker.objects.get(name=broker_name)
                symbol_filter &= Q(broker=broker)
                logger.info(f"Filtering by broker: {broker_name}")
            except Broker.DoesNotExist:
                logger.error(f"Broker '{broker_name}' not found")
                return {
                    'success': False,
                    'error': f"Broker '{broker_name}' not found",
                    'message': f"Failed to execute strategies: Broker '{broker_name}' not found"
                }
        
        if exchange_name:
            try:
                exchange = Exchange.objects.get(name=exchange_name)
                symbol_filter &= Q(exchange=exchange)
                logger.info(f"Filtering by exchange: {exchange_name}")
            except Exchange.DoesNotExist:
                logger.error(f"Exchange '{exchange_name}' not found")
                return {
                    'success': False,
                    'error': f"Exchange '{exchange_name}' not found",
                    'message': f"Failed to execute strategies: Exchange '{exchange_name}' not found"
                }
        
        # Execute Mean Reverting Strategy
        try:
            strategy = Strategy.objects.get(slug='mean-reverting')
            strategy_symbols = StrategySymbol.objects.filter(
                Q(is_active_long=True) | Q(is_active_short=True), 
                strategy=strategy,
                symbol__active=True
            ).filter(symbol__in=Symbols.objects.filter(symbol_filter))
            
            logger.info(f"Executing mean-reverting strategy for {strategy_symbols.count()} symbols")
            
            strategy_instance = MeanRevertingStrategy(strategy.parameters)
            for strategy_symbol in strategy_symbols:
                strategy_instance.execution(
                    strategy_symbol,
                    strategy_symbol.symbol,
                    strategy_symbol.is_active_long,
                    strategy_symbol.is_active_short,
                    start_date="2013-01-01",
                    end_date=end_date if end_date else date.today()
                )
        except Strategy.DoesNotExist:
            logger.warning("Mean-reverting strategy not found")
        except Exception as e:
            logger.error(f"Error executing mean-reverting strategy: {str(e)}")

        # Execute Cointegration Strategy
        try:
            strategy = Strategy.objects.get(slug='cointegration')
            correlated_pair_ids = StrategySymbol.objects.filter(
                Q(is_active_long=True) | Q(is_active_short=True),
                correlated_pair__isnull=False, 
                symbol__active=True,
                correlated_pair__symbol_1__active=True,
                correlated_pair__symbol_2__active=True
            ).filter(
                symbol__in=Symbols.objects.filter(symbol_filter)
            ).values_list('correlated_pair', flat=True).distinct()
            
            correlated_pairs = CorrelatedPair.objects.filter(id__in=correlated_pair_ids)
            
            logger.info(f"Executing cointegration strategy for {correlated_pairs.count()} correlated pairs")
            
            strategy_instance = CoIntegrationStrategy(strategy.parameters)
            for correlated_pair in correlated_pairs:
                strategy_instance.execution(
                    correlated_pair,
                    start_date="2013-01-01", 
                    end_date=end_date if end_date else date.today()
                )
        except Strategy.DoesNotExist:
            logger.warning("Cointegration strategy not found")
        except Exception as e:
            logger.error(f"Error executing cointegration strategy: {str(e)}")

        logger.info("Strategy execution completed successfully")
        return {
            'success': True,
            'message': 'Strategy execution completed successfully'
        }
        
    except Exception as e:
        logger.error(f"Error in execute_strategies: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'message': f"Failed to execute strategies: {str(e)}"
        }

    #backtest = BackTestingStrategy.objects.get(strategy=strategy)
    #BackTestUtils.calculate_symbol_statistics(backtest)     
