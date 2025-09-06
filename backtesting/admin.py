from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import path
from django.contrib import messages
from django.shortcuts import render
from django import forms
from .models import BackTestingStrategy, TradeHistory, StrategyStatistics, SymbolStatistics
from .backtest_logic import calculate_strategy_statistics_by_id
from symbols.models import Exchange, Broker
from strategies.models import Strategy
from backtesting.backtest_logic import execute_backtest
from datetime import date


class ExecuteBacktestForm(forms.Form):
    """Form for executing backtests"""
    strategy = forms.ModelChoiceField(
        queryset=Strategy.objects.all(),
        label="Strategy",
        help_text="Select the strategy to execute"
    )
    broker = forms.ModelChoiceField(
        queryset=Broker.objects.all(),
        required=False,
        label="Broker (Optional)",
        help_text="Filter by specific broker"
    )
    exchange = forms.ModelChoiceField(
        queryset=Exchange.objects.all(),
        required=False,
        label="Exchange (Optional)",
        help_text="Filter by specific exchange"
    )
    start_date = forms.DateField(
        initial=date(2013, 1, 1),
        label="Start Date",
        help_text="Start date for the backtest"
    )
    end_date = forms.DateField(
        initial=date.today(),
        label="End Date",
        help_text="End date for the backtest"
    )
    symbols = forms.CharField(
        required=False,
        max_length=500,
        label="Specific Symbols (Optional)",
        help_text="Comma-separated list of symbols (e.g., AAPL,MSFT,GOOGL)"
    )


@admin.register(BackTestingStrategy)
class BackTestingStrategyAdmin(admin.ModelAdmin):
    list_display = ("id", "strategy", "name", "broker", "exchange", "get_backtest_info", "get_stats_status", "created_at")
    list_display_links = ("id", "strategy", "name")
    search_fields = ("strategy__name", "name", "id")
    list_filter = ("created_at", "strategy", "broker", "exchange")
    readonly_fields = ("id", "created_at")
    ordering = ("-created_at",)
    
    def get_stats_status(self, obj):
        """Show if strategy statistics exist for this backtest"""
        stats_count = StrategyStatistics.objects.filter(backtest=obj).count()
        trade_count = TradeHistory.objects.filter(backtest=obj).count()
        
        if stats_count > 0:
            return f"✅ Stats ({stats_count})"
        elif trade_count > 0:
            return f"⚠️ Trades ({trade_count})"
        else:
            return "❌ No Data"
    get_stats_status.short_description = "Statistics Status"
    
    def get_backtest_info(self, obj):
        """Show detailed information about the backtest"""
        trade_count = TradeHistory.objects.filter(backtest=obj).count()
        completed_trades = TradeHistory.objects.filter(backtest=obj, exit_price__isnull=False).count()
        stats_count = StrategyStatistics.objects.filter(backtest=obj).count()
        
        info_parts = []
        if trade_count > 0:
            info_parts.append(f"Trades: {trade_count}")
        if completed_trades > 0:
            info_parts.append(f"Completed: {completed_trades}")
        if stats_count > 0:
            info_parts.append(f"Stats: {stats_count}")
        
        return " | ".join(info_parts) if info_parts else "No data"
    get_backtest_info.short_description = "Backtest Info"
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:backtest_id>/calculate-stats/',
                self.admin_site.admin_view(self.calculate_stats_view),
                name='backtesting_backtestingstrategy_calculate_stats',
            ),
            path(
                'execute-backtest/',
                self.admin_site.admin_view(self.execute_backtest_view),
                name='backtesting_backtestingstrategy_execute_backtest',
            ),
        ]
        return custom_urls + urls
    
    def calculate_stats_view(self, request, backtest_id):
        """Admin view to calculate strategy statistics"""
        try:
            # Log the request
            self.message_user(request, f"Starting calculation for backtest ID: {backtest_id}", level=messages.INFO)
            
            # Get backtest info before calculation
            backtest = BackTestingStrategy.objects.get(id=backtest_id)
            trade_count = TradeHistory.objects.filter(backtest=backtest).count()
            completed_trades = TradeHistory.objects.filter(backtest=backtest, exit_price__isnull=False).count()
            
            if trade_count == 0:
                messages.warning(request, f"No trades found for backtest ID {backtest_id}. Statistics calculation requires trade data.")
                return HttpResponseRedirect("../")
            
            if completed_trades == 0:
                messages.warning(request, f"No completed trades found for backtest ID {backtest_id}. All trades must have exit prices for statistics calculation.")
                return HttpResponseRedirect("../")
            
            result = calculate_strategy_statistics_by_id(backtest_id)
            
            if result['success']:
                messages.success(request, result['message'])
                if 'stats_count' in result:
                    if result['stats_count'] == 0:
                        messages.warning(request, "Calculation completed but no statistics records were created. This might be due to:")
                        messages.warning(request, "- No active strategy symbols for LONG/SHORT actions")
                        messages.warning(request, "- No trades matching the active symbol criteria")
                        messages.warning(request, "- Strategy type not supported (only 'mean-reverting' and 'cointegration' are supported)")
                    else:
                        messages.info(request, f"Created {result['stats_count']} strategy statistics records")
            else:
                messages.error(request, result['message'])
                if 'error' in result:
                    messages.error(request, f"Error details: {result['error']}")
                    
        except BackTestingStrategy.DoesNotExist:
            messages.error(request, f"Backtest with ID {backtest_id} not found")
        except Exception as e:
            import traceback
            error_details = f"Unexpected error: {str(e)}\nTraceback: {traceback.format_exc()}"
            messages.error(request, f"Error calculating statistics: {str(e)}")
            # Log the full error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(error_details)
        
        return HttpResponseRedirect("../")
    
    def execute_backtest_view(self, request):
        """Admin view to execute backtests"""
        if request.method == 'POST':
            form = ExecuteBacktestForm(request.POST)
            if form.is_valid():
                try:
                    # Get form data
                    strategy = form.cleaned_data['strategy']
                    broker = form.cleaned_data['broker']
                    exchange = form.cleaned_data['exchange']
                    start_date = form.cleaned_data['start_date']
                    end_date = form.cleaned_data['end_date']
                    symbols = form.cleaned_data['symbols']
                    
                    # Prepare parameters for execute_backtest
                    symbol_list = None
                    if symbols:
                        symbol_list = [s.strip().upper() for s in symbols.split(',')]
                    
                    exchange_name = None
                    if exchange:
                        exchange_name = exchange.name
                    
                    # Execute the backtest
                    result = execute_backtest(
                        strategy_id=strategy.slug,
                        start_date=start_date,
                        end_date=end_date,
                        symbol_list=symbol_list,
                        exchange_name=exchange_name
                    )
                    
                    if isinstance(result, str) and "Error" in result:
                        messages.error(request, f"Backtest execution failed: {result}")
                    else:
                        messages.success(request, f"Backtest executed successfully! Backtest ID: {result.id if hasattr(result, 'id') else 'N/A'}")
                        messages.info(request, f"Strategy: {strategy.name}")
                        if exchange:
                            messages.info(request, f"Exchange: {exchange.name}")
                        if broker:
                            messages.info(request, f"Broker: {broker.name}")
                    
                    return HttpResponseRedirect("../")
                    
                except Exception as e:
                    messages.error(request, f"Error executing backtest: {str(e)}")
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Backtest execution error: {str(e)}")
        else:
            form = ExecuteBacktestForm()
        
        # Render the form
        context = {
            'title': 'Execute Backtest',
            'form': form,
            'opts': self.model._meta,
            'has_change_permission': True,
        }
        return render(request, 'admin/backtesting/backtestingstrategy/execute_backtest.html', context)
    
    def calculate_strategy_statistics(self, request, queryset):
        """Admin action to calculate strategy statistics for selected backtests"""
        success_count = 0
        error_count = 0
        
        for backtest in queryset:
            result = calculate_strategy_statistics_by_id(backtest.id)
            if result['success']:
                success_count += 1
            else:
                error_count += 1
        
        if success_count > 0:
            messages.success(request, f"Successfully calculated statistics for {success_count} backtest(s)")
        if error_count > 0:
            messages.error(request, f"Failed to calculate statistics for {error_count} backtest(s)")
    
    calculate_strategy_statistics.short_description = "Calculate strategy statistics for selected backtests"
    
    actions = ['calculate_strategy_statistics']
    
    def changelist_view(self, request, extra_context=None):
        """Override changelist view to add execute backtest button"""
        extra_context = extra_context or {}
        extra_context['show_execute_backtest_button'] = True
        return super().changelist_view(request, extra_context)


@admin.register(TradeHistory)
class TradeHistoryAdmin(admin.ModelAdmin):
    list_display = ("id", "symbol", "correlated_pair", "backtest", "backtest_id", "action", "entry_price", "exit_price", "quantity", "max_drawdown", "profit_loss", "entry_date", "exit_date", "created_at")
    list_display_links = ("id", "symbol", "backtest")
    search_fields = ("symbol__ticker", "backtest__strategy__name", "correlated_pair__symbol_1__ticker", "correlated_pair__symbol_2__ticker", "backtest__id")
    list_filter = ("action", "entry_date", "exit_date", "created_at", "backtest")
    readonly_fields = ("id", "created_at")
    ordering = ("-created_at",)
    
    def backtest_id(self, obj):
        """Display backtest ID for easy reference"""
        return obj.backtest.id if obj.backtest else "-"
    backtest_id.short_description = "Backtest ID"


@admin.register(StrategyStatistics)
class StrategyStatisticsAdmin(admin.ModelAdmin):
    list_display = ("id", "strategy", "action", "backtest", "backtest_id", "total_trades", "average_holding_period", "win_rate", "total_profit_loss", "total_roi", "average_max_drawdown", "created_at")
    list_display_links = ("id", "strategy", "backtest")
    search_fields = ("strategy__name", "backtest__name", "backtest__id")
    list_filter = ("created_at", "strategy", "action", "backtest")
    readonly_fields = ("id", "created_at")
    ordering = ("-created_at",)
    
    def backtest_id(self, obj):
        """Display backtest ID for easy reference"""
        return obj.backtest.id if obj.backtest else "-"
    backtest_id.short_description = "Backtest ID"


@admin.register(SymbolStatistics)
class SymbolStatisticsAdmin(admin.ModelAdmin):
    list_display = ("id", "symbol", "correlated_pair", "strategy", "action", "backtest", "backtest_id", "total_trades", "average_holding_period", "win_rate", "profit_loss", "total_roi", "average_max_drawdown", "created_at")
    list_display_links = ("id", "symbol", "strategy", "backtest")
    search_fields = ("symbol__ticker", "strategy__name", "correlated_pair__symbol_1__ticker", "correlated_pair__symbol_2__ticker", "backtest__id")
    list_filter = ("created_at", "strategy", "action", "backtest")
    readonly_fields = ("id", "created_at")
    ordering = ("-created_at",)
    
    def backtest_id(self, obj):
        """Display backtest ID for easy reference"""
        return obj.backtest.id if obj.backtest else "-"
    backtest_id.short_description = "Backtest ID"
