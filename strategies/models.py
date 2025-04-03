from django.db import models
from django.utils.text import slugify
from django.db.models.signals import pre_save
from django.utils import timezone
from symbols.models import Symbols,Exchange

class Strategy(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(unique=True, blank=True)  # Unique slug
    is_active = models.BooleanField(default=True)  # Boolean field for active/inactive status
    parameters = models.JSONField(default=dict, blank=True)  # Store params dynamically
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

# Auto-generate slug before saving
def generate_slug(instance, new_slug=None):
    slug = slugify(instance.name) if not new_slug else new_slug
    qs = Strategy.objects.filter(slug=slug).exclude(id=instance.id)
    if qs.exists():
        new_slug = f"{slug}-{qs.count()}"
        return generate_slug(instance, new_slug=new_slug)
    return slug

def pre_save_strategy_receiver(sender, instance, *args, **kwargs):
    if not instance.slug:
        instance.slug = generate_slug(instance)

pre_save.connect(pre_save_strategy_receiver, sender=Strategy)


class StrategySymbol(models.Model):
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE)
    symbol = models.ForeignKey(Symbols, on_delete=models.CASCADE)
    is_active_long = models.BooleanField(default=False)  # Active for LONG trades
    is_active_short = models.BooleanField(default=False)  # Active for SHORT trades
    slot_free = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('strategy', 'symbol')  # Prevent duplicate entries

    def __str__(self):
        return f"{self.strategy.name} - {self.symbol.ticker} (Long: {'Active' if self.is_active_long else 'Inactive'}, Short: {'Active' if self.is_active_short else 'Inactive'})"
    

class CorrelatedPair(models.Model):
    exchange = models.ForeignKey(Exchange, on_delete=models.CASCADE)  # The exchange this pair belongs to
    symbol_1 = models.ForeignKey(Symbols, related_name='correlation_first', on_delete=models.CASCADE)
    symbol_2 = models.ForeignKey(Symbols, related_name='correlation_second', on_delete=models.CASCADE)
    correlation = models.FloatField()  # Store the correlation coefficient
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('exchange', 'symbol_1', 'symbol_2')  # Prevent duplicate pairs

    def __str__(self):
        return f"{self.symbol_1.ticker} - {self.symbol_2.ticker}"    