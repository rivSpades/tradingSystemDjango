# admin.py

from django.contrib import admin
from .models import TradeHistoryExec

@admin.register(TradeHistoryExec)
class TradeHistoryAdmin(admin.ModelAdmin):
    list_display = (
        'symbol', 'strategy', 'correlated_pair', 'action', 
        'entry_date', 'exit_date', 'entry_price', 'exit_price', "bet_size",
        'quantity', 'profit_loss', 'created_at'
    )
    list_filter = ('strategy', 'action', 'entry_date', 'exit_date')
    search_fields = ('symbol__ticker', 'correlated_pair__symbol_1__ticker', 'correlated_pair__symbol_2__ticker')
    ordering = ('-created_at',)
