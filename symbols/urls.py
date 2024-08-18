from django.urls import path
from . import views

urlpatterns = [
    path('', views.symbols, name='symbols'),  # Example URL pattern for the index view
]
