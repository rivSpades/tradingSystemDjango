#!/usr/bin/env python
"""
Standalone script to calculate strategy statistics for a specific backtest by ID
"""

import os
import sys
import django
import argparse

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trading_system.settings')
django.setup()

from backtesting.backtest_logic import calculate_strategy_statistics_by_id
from backtesting.models import BackTestingStrategy


def list_backtests():
    """List all available backtests with their IDs"""
    backtests = BackTestingStrategy.objects.all().select_related('strategy')
    
    if backtests:
        print('Available backtests:')
        print('ID  | Strategy Name          | Backtest Name')
        print('----|------------------------|----------------')
        for backtest in backtests:
            strategy_name = backtest.strategy.name[:20].ljust(20)
            backtest_name = (backtest.name or 'Unnamed')[:15].ljust(15)
            print(f'{backtest.id:3d} | {strategy_name} | {backtest_name}')
    else:
        print('No backtests found.')


def main():
    parser = argparse.ArgumentParser(description='Calculate strategy statistics for a specific backtest')
    parser.add_argument('backtest_id', type=int, nargs='?', help='ID of the backtest to calculate statistics for')
    parser.add_argument('--list-backtests', action='store_true', help='List all available backtests with their IDs')
    
    args = parser.parse_args()
    
    # Handle list option
    if args.list_backtests:
        list_backtests()
        return
    
    # Check if backtest_id is provided
    if args.backtest_id is None:
        print('Error: Please provide a backtest ID or use --list-backtests to see available backtests.')
        print('Usage: python calculate_strategy_stats_script.py <backtest_id>')
        print('   or: python calculate_strategy_stats_script.py --list-backtests')
        return
    
    backtest_id = args.backtest_id
    
    # Show backtest info before execution
    try:
        backtest = BackTestingStrategy.objects.get(id=backtest_id)
        print(f'Calculating strategy statistics for:')
        print(f'  Backtest ID: {backtest_id}')
        print(f'  Strategy: {backtest.strategy.name}')
        print(f'  Backtest Name: {backtest.name or "Unnamed"}')
        print('')
    except BackTestingStrategy.DoesNotExist:
        print(f'❌ Backtest with ID {backtest_id} not found.')
        return
    
    # Execute the calculation
    print('Calculating strategy statistics...')
    result = calculate_strategy_statistics_by_id(backtest_id)
    
    if result['success']:
        print(f"✅ {result['message']}")
    else:
        print(f"❌ {result['message']}")


if __name__ == '__main__':
    main()
