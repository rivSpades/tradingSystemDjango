from django.urls import path
from .views import SymbolListView, SymbolDetailView

urlpatterns = [
    path('', SymbolListView.as_view(), name='symbols'),  # Example URL pattern for the index view
    path('<str:ticker>/', SymbolDetailView.as_view(), name='symbol_detail'),
]
