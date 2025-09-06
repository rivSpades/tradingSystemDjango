#!/usr/bin/env python
"""
Standalone script to execute trading strategies with optional broker and exchange filtering
"""

import os
import sys
import django
import argparse
from datetime import datetime

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trading_system.settings')
django.setup()

from execution.execution_logic import execute_strategies
from symbols.models import Broker, Exchange


def list_brokers():
    """List all available brokers"""
    brokers = Broker.objects.all()
    if brokers:
        print('Available brokers:')
        for broker in brokers:
            print(f'  - {broker.name}')
    else:
        print('No brokers found.')


def list_exchanges():
    """List all available exchanges"""
    exchanges = Exchange.objects.all()
    if exchanges:
        print('Available exchanges:')
        for exchange in exchanges:
            print(f'  - {exchange.name}')
    else:
        print('No exchanges found.')


def main():
    parser = argparse.ArgumentParser(description='Execute trading strategies with optional filtering')
    parser.add_argument('--end-date', type=str, help='End date for strategy execution (YYYY-MM-DD format, default: today)')
    parser.add_argument('--broker', type=str, help='Filter by broker name')
    parser.add_argument('--exchange', type=str, help='Filter by exchange name')
    parser.add_argument('--list-brokers', action='store_true', help='List available brokers')
    parser.add_argument('--list-exchanges', action='store_true', help='List available exchanges')
    
    args = parser.parse_args()
    
    # Handle list options
    if args.list_brokers:
        list_brokers()
        return
    
    if args.list_exchanges:
        list_exchanges()
        return
    
    # Parse end date if provided
    end_date = None
    if args.end_date:
        try:
            end_date = datetime.strptime(args.end_date, '%Y-%m-%d').date()
        except ValueError:
            print('Error: Invalid date format. Use YYYY-MM-DD format.')
            return
    
    # Get broker and exchange names
    broker_name = args.broker
    exchange_name = args.exchange
    
    # Show execution parameters
    print('Strategy Execution Parameters:')
    print(f'  End Date: {end_date or "Today"}')
    print(f'  Broker Filter: {broker_name or "All"}')
    print(f'  Exchange Filter: {exchange_name or "All"}')
    print('')
    
    # Execute strategies
    print('Executing strategies...')
    result = execute_strategies(
        end_date=end_date,
        broker_name=broker_name,
        exchange_name=exchange_name
    )
    
    if result['success']:
        print(f"✅ {result['message']}")
    else:
        print(f"❌ {result['message']}")


if __name__ == '__main__':
    main()
