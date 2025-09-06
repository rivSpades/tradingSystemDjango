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
def update_daily_prices(progress=0, broker_name=None):
    """Async task for updating daily prices with progress tracking."""
    progress_recorder = ProgressRecorder(update_daily_prices)  # Attach the progress recorder

    # Filter symbols by broker if specified
    if broker_name:
        symbols = Symbols.objects.filter(broker__name=broker_name)
        print(f"Updating daily prices for {broker_name} broker")
    else:
        symbols = Symbols.objects.all()
        print("Updating daily prices for all brokers")

    total_symbols = symbols.count()  # Get the real total number of symbols

    # Track progress for the daily prices update task
    progress_recorder.set_progress(0, total_symbols)  # Initial progress (0%)
    
    success_count = 0
    error_count = 0
    
    # Loop through each symbol and update its daily prices
    for index, symbol in enumerate(symbols):
        try:
            print(f"Processing {symbol.ticker} ({symbol.broker.name if symbol.broker else 'No broker'})")
            
            # Update daily price for the current symbol
            success = DailyPriceManager.insert_daily_price(symbol, '2013-01-01')
            
            if success:
                success_count += 1
            else:
                error_count += 1
                
        except Exception as e:
            print(f"Error updating {symbol.ticker}: {str(e)}")
            error_count += 1
        
        # Update progress after each symbol update
        progress_recorder.set_progress(index + 1, total_symbols)

    # Once the task is complete, mark the progress as 100%
    progress_recorder.set_progress(total_symbols, total_symbols)  # Final progress (100%)

    result_message = f"Daily Prices Update Completed! Success: {success_count}, Errors: {error_count}"
    if broker_name:
        result_message += f" for {broker_name} broker"
    
    return result_message
