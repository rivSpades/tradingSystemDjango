from django.contrib import admin
from .models import Strategy
from django.contrib.postgres.fields import JSONField
from django_json_widget.widgets import JSONEditorWidget  # Optional JSON widget

@admin.register(Strategy)
class StrategyAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "created_date")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)
    list_filter = ("is_active",)
    formfield_overrides = {JSONField: {"widget": JSONEditorWidget}}  # Pretty JSON editor
