from django.contrib import admin
from .models import Strategy,StrategySymbol,CorrelatedPair
from django.contrib.postgres.fields import JSONField
from django_json_widget.widgets import JSONEditorWidget  # Optional JSON widget

@admin.register(Strategy)
class StrategyAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "created_date")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)
    list_filter = ("is_active",)
    formfield_overrides = {JSONField: {"widget": JSONEditorWidget}}  # Pretty JSON editor


@admin.register(StrategySymbol)
class StrategySymbolAdmin(admin.ModelAdmin):
    list_display = ("strategy", "symbol","correlated_pair", "is_active_long","is_active_short", "created_at")
    list_filter = ("strategy", "is_active_long","is_active_short")
    search_fields = ("strategy__name", "symbol__ticker")


@admin.register(CorrelatedPair)
class CorrelatedPairAdmin(admin.ModelAdmin):
    list_display = ("exchange", "symbol_1", "symbol_2", "correlation", "created_at")
    list_filter = ("exchange",)
    search_fields = ("symbol_1__ticker", "symbol_2__ticker", "exchange__name")
    ordering = ("-correlation",)