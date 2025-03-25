from django.shortcuts import render
from django.http import HttpResponse
from . import models
from django.views.generic import DetailView,ListView
from django.db.models import Q,Subquery,OuterRef
from django.views import View
from django.shortcuts import redirect
from django.contrib import messages

from .tasks  import update_symbols,update_daily_prices
from celery.result import AsyncResult
from django.http import JsonResponse
def symbols(request):
	return HttpResponse("Hello world from symbols") #also its possible o pass html inside the function

class SymbolDetailView(DetailView):

	#by default  the context dictionary will be the name of the object lowercase school

	#but we will overwrite to school_detail
	context_object_name =  'symbol_detail'
	model = models.Symbols
	template_name = 'symbols/symbol_detail.html'
	slug_field = 'ticker'
	slug_url_kwarg = 'ticker'

from django.db.models import OuterRef, Subquery
from django.views.generic import ListView
from django.db.models import Q

class SymbolListView(ListView):
    model = models.Symbols
    template_name = 'symbols/symbols_list.html'
    context_object_name = 'symbols'
    paginate_by = 10  # Display 10 symbols per page

    def get_queryset(self):
        # Subquery for the latest close price and date
        latest_price_subquery = models.DailyPrice.objects.filter(
            symbol=OuterRef('pk')
        ).order_by('-price_date')

        queryset = models.Symbols.objects.all().annotate(
            last_close_price=Subquery(latest_price_subquery.values('close_price')[:1]),
            last_close_date=Subquery(latest_price_subquery.values('price_date')[:1])
        )

        # Get search and filter parameters
        search_query = self.request.GET.get('search', None)
        exchange_filter = self.request.GET.get('exchange', None)

        if search_query:
            queryset = queryset.filter(
                Q(ticker__icontains=search_query) | Q(name__icontains=search_query)
            )

        if exchange_filter:
            queryset = queryset.filter(exchange__name=exchange_filter)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['exchanges'] = models.Exchange.objects.all()  # Fetch all available exchanges for the filter tabs
        return context


class SymbolUpdateView(View):
    """Class-based view to update symbols asynchronously with progress tracking."""

    def post(self, request, *args, **kwargs):
        # Trigger the Celery task asynchronously
        task = update_symbols.delay()  # Start the task in the background

        # Return the task ID in the response so the frontend can track progress
        return JsonResponse({'task_id': task.id})
    

class SymbolDailyPriceUpdateView(View):
    """Class-based view to trigger the update of daily prices asynchronously."""
    
    def post(self, request, *args, **kwargs):
        # Trigger the Celery task asynchronously
        task = update_daily_prices.delay()  # Start the task in the background

        # Return the task ID in the response so the frontend can track progress
        return JsonResponse({'task_id': task.id})


class SymbolTaskProgressView(View):
    """Class-based view to track the progress of the symbol update task."""

    def get(self, request, *args, **kwargs):
        task_id = request.GET.get('task_id')  # Get the task ID from the query parameter
        
        if task_id:
            task_result = AsyncResult(task_id)  # Get the Celery task result by ID

            # Check the state of the task and return the progress information
            if task_result.state == 'PENDING':
                return JsonResponse({'state': 'PENDING', 'progress': 0})
            elif task_result.state == 'SUCCESS':
                return JsonResponse({'state': 'SUCCESS', 'result': task_result.result})
            elif task_result.state == 'FAILURE':
                return JsonResponse({'state': 'FAILURE'})
            else:
                # Task is in progress, return the current progress
                progress = task_result.info.get('progress', 0)  # Get the progress (if available)
                return JsonResponse({'state': task_result.state, 'progress': progress})

        return JsonResponse({'state': 'No task running'})