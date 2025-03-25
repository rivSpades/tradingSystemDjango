from django.contrib import admin
from .models import Symbols,Exchange,DailyPrice  # Import your model

# Register your model with the admin site
admin.site.register(Symbols)
admin.site.register(Exchange)
admin.site.register(DailyPrice)
