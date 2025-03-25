from celery import shared_task
from celery_progress.backend import ProgressRecorder
from .models import Symbols
from .utils import SymbolsManager,DailyPriceManager

@shared_task
def update_symbols(progress=0):
    """Async task for updating symbols with progress tracking."""
    progress_recorder = ProgressRecorder(update_symbols)  # Attach the progress recorder

    total_symbols = Symbols.objects.count()  # Get the real total number of symbols

    # Track progress for the symbols update task
    progress_recorder.set_progress(0, total_symbols)  # Initial progress (0%)
    
    # Insert the symbols (only once, not in a loop)
    SymbolsManager.insert_symbols()

    # Once the task is complete, mark the progress as 100%
    progress_recorder.set_progress(total_symbols, total_symbols)  # Final progress (100%)

    return "Update completed!"

@shared_task
def update_daily_prices(progress=0):
    """Async task for updating daily prices with progress tracking."""
    progress_recorder = ProgressRecorder(update_daily_prices)  # Attach the progress recorder

    total_symbols = Symbols.objects.count()  # Get the real total number of symbols

    # Track progress for the daily prices update task
    progress_recorder.set_progress(0, total_symbols)  # Initial progress (0%)
    
    # Loop through each symbol and update its daily prices
    symbols = Symbols.objects.all()
    for index, symbol in enumerate(symbols):
        # Update daily price for the current symbol
        DailyPriceManager.insert_daily_price(symbol.ticker, '2013-01-01')
        
        # Update progress after each symbol update
        progress_recorder.set_progress(index + 1, total_symbols)

    # Once the task is complete, mark the progress as 100%
    progress_recorder.set_progress(total_symbols, total_symbols)  # Final progress (100%)

    return "Daily Prices Update Completed!"
