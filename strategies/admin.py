from django.contrib import admin
from .models import Strategy,StrategySymbol
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
    list_display = ("strategy", "symbol", "is_active", "created_at")
    list_filter = ("strategy", "is_active")
    search_fields = ("strategy__name", "symbol__ticker")
