from rest_framework import serializers
from .models import Symbols, DailyPrice

class SymbolSerializer(serializers.ModelSerializer):
    exchange_name = serializers.CharField(source="exchange.name", read_only=True)
    last_close_price = serializers.SerializerMethodField()
    last_close_date = serializers.SerializerMethodField()

    class Meta:
        model = Symbols
        fields = ['id', 'ticker', 'name', 'exchange_name', 'last_close_price', 'last_close_date']

    def get_last_close_price(self, obj):
        last_price = DailyPrice.objects.filter(symbol=obj).order_by('-price_date').first()
        if last_price:
            return round(last_price.close_price, 2)  # Round to 2 decimal places
        return None

    def get_last_close_date(self, obj):
        last_price = DailyPrice.objects.filter(symbol=obj).order_by('-price_date').first()
        return last_price.price_date if last_price else None
