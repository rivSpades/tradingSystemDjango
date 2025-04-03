from django.contrib import admin
from .models import BackTestingStrategy, TradeHistory, StrategyStatistics, SymbolStatistics

@admin.register(BackTestingStrategy)
class BackTestingStrategyAdmin(admin.ModelAdmin):
    list_display = ("strategy", "name","created_at")
    search_fields = ("strategy__name",)
    list_filter = ("created_at",)

@admin.register(TradeHistory)
class TradeHistoryAdmin(admin.ModelAdmin):
    list_display = ("symbol","correlated_pair", "backtest", "action", "entry_price", "exit_price", "quantity", "max_drawdown","profit_loss","entry_date","exit_date","created_at")
    search_fields = ("symbol__ticker", "backtest__strategy__name")
    list_filter = ("action", "entry_date", "exit_date","created_at")

@admin.register(StrategyStatistics)
class StrategyStatisticsAdmin(admin.ModelAdmin):
    list_display = ("strategy", "action", "backtest", "total_trades","average_holding_period", "win_rate", "total_profit_loss","total_roi", "average_max_drawdown", "created_at")
    search_fields = ("strategy__name",)
    list_filter = ("created_at",)

@admin.register(SymbolStatistics)
class SymbolStatisticsAdmin(admin.ModelAdmin):
    list_display = ("symbol","correlated_pair", "strategy","action", "backtest", "total_trades", "average_holding_period","win_rate", "profit_loss","total_roi", "average_max_drawdown", "created_at")
    search_fields = ("symbol__ticker", "strategy__name")
    list_filter = ("created_at",)
