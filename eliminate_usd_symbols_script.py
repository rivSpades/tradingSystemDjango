#!/usr/bin/env python
"""
Standalone script to eliminate all StrategySymbols where the symbol ticker ends with 'USD'
"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trading_system.settings')
django.setup()

from strategies.models import StrategySymbol


def eliminate_usd_strategy_symbols():
    """
    Eliminate all StrategySymbols where the symbol ticker ends with 'USD'
    """
    try:
        # Find all StrategySymbols where the symbol ticker ends with 'USD'
        usd_strategy_symbols = StrategySymbol.objects.filter(
            symbol__ticker__endswith='USD'
        )
        
        # Count before deletion
        count = usd_strategy_symbols.count()
        
        if count == 0:
            print("No StrategySymbols with USD symbols found.")
            return
        
        print(f"Found {count} StrategySymbols with USD symbols:")
        
        # Show some examples
        for ss in usd_strategy_symbols[:10]:  # Show first 10
            print(f"  - {ss.strategy.name} - {ss.symbol.ticker}")
        
        if count > 10:
            print(f"  ... and {count - 10} more")
        
        # Ask for confirmation
        response = input(f"\nDo you want to eliminate all {count} StrategySymbols? (yes/no): ")
        
        if response.lower() in ['yes', 'y']:
            # Delete the StrategySymbols
            deleted_count = usd_strategy_symbols.delete()[0]
            print(f"Successfully eliminated {deleted_count} StrategySymbols with USD symbols")
        else:
            print("Operation cancelled.")
            
    except Exception as e:
        print(f"Error eliminating USD StrategySymbols: {str(e)}")


if __name__ == '__main__':
    eliminate_usd_strategy_symbols()
