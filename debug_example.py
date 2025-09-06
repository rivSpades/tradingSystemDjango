#!/usr/bin/env python
"""
Example of using Python's built-in debugger (pdb)
This is the simplest way to debug Django code
"""

import pdb
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trading_system.settings')
django.setup()

from backtesting.models import BackTestingStrategy
from backtesting.backtest_logic import calculate_strategy_statistics_by_id

def debug_example():
    """Example function showing how to use pdb"""
    print("Starting debug example...")
    
    # Set a breakpoint - code will stop here
    pdb.set_trace()
    
    # This code will only run after you continue from the breakpoint
    backtest = BackTestingStrategy.objects.get(id=66)
    print(f"Found backtest: {backtest.strategy.name}")
    
    # Another breakpoint
    pdb.set_trace()
    
    result = calculate_strategy_statistics_by_id(66)
    print(f"Result: {result}")

if __name__ == '__main__':
    debug_example()
