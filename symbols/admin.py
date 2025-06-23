from django.contrib import admin
from .models import Symbols, Exchange, DailyPrice,Broker

@admin.register(Symbols)
class SymbolsAdmin(admin.ModelAdmin):
    search_fields = ['ticker']  # Enables search by ticker in admin

admin.site.register(Exchange)
admin.site.register(DailyPrice)
admin.site.register(Broker)
