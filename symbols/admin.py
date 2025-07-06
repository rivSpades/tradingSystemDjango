from django.contrib import admin
from .models import Symbols, Exchange, DailyPrice, Broker

@admin.register(Symbols)
class SymbolsAdmin(admin.ModelAdmin):
    search_fields = ['ticker']  # Enables search by ticker in admin

@admin.register(DailyPrice)
class DailyPriceAdmin(admin.ModelAdmin):
    search_fields = ['symbol__ticker']  # Enables search by symbol's ticker
    list_display = ['symbol', 'price_date', 'close_price']  # Optional: show more info in list view
    list_filter = ['symbol', 'price_date']  # Optional: filter options in admin

admin.site.register(Exchange)
admin.site.register(Broker)
