from django.urls import path
from .views import SymbolListView, SymbolDetailView, SymbolUpdateView, SymbolTaskProgressView,SymbolDailyPriceUpdateView

urlpatterns = [
    path('', SymbolListView.as_view(), name='symbols'),
    path('update-symbols/', SymbolUpdateView.as_view(), name='update_symbols'),
    path('update-daily-prices/', SymbolDailyPriceUpdateView.as_view(), name='update_daily_prices'),
    path('task-progress/', SymbolTaskProgressView.as_view(), name='task_progress'),  # URL for tracking progress
    path('<str:ticker>/', SymbolDetailView.as_view(), name='symbol_detail'),
]
