from django.shortcuts import render
from django.http import HttpResponse
from . import models
from django.views.generic import DetailView,ListView
from django.db.models import Q,Subquery,OuterRef
from django.views import View
from django.shortcuts import redirect
from django.contrib import messages
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from .tasks  import update_symbols,update_daily_prices
from .serializers import SymbolSerializer
from .utils import DailyPriceManager
from celery.result import AsyncResult
from django.http import JsonResponse
from django.db.models import OuterRef, Subquery
from django.views.generic import ListView
from django.db.models import Q



class SymbolListView(ListAPIView):
    serializer_class = SymbolSerializer

    def get_queryset(self):
        keyword = self.request.query_params.get('search', None)  # Get 'search' query parameter

        latest_price_subquery = models.DailyPrice.objects.filter(
            symbol=OuterRef('pk')
        ).order_by('-price_date')

        queryset = models.Symbols.objects.all().annotate(
            last_close_price=Subquery(latest_price_subquery.values('close_price')[:1]),
            last_close_date=Subquery(latest_price_subquery.values('price_date')[:1])
        )

        # Apply filtering if a keyword is provided
        if keyword:
            queryset = queryset.filter(
                Q(ticker__icontains=keyword) | Q(name__icontains=keyword)
            )

        return queryset


class SymbolDetailView(DetailView):

	#by default  the context dictionary will be the name of the object lowercase school

	#but we will overwrite to school_detail
	context_object_name =  'symbol_detail'
	model = models.Symbols
	template_name = 'symbols/symbol_detail.html'
	slug_field = 'ticker'
	slug_url_kwarg = 'ticker'








class SymbolUpdateView(View):
    """Class-based view to update symbols asynchronously with progress tracking."""

    def post(self, request, *args, **kwargs):
        # Trigger the Celery task asynchronously
        task = update_symbols.delay()  # Start the task in the background

        # Return the task ID in the response so the frontend can track progress
        return JsonResponse({'task_id': task.id})
    

class SymbolDailyPriceUpdateView(View):
    """Class-based view to trigger the update of daily prices synchronously."""
    
    def post(self, request, *args, **kwargs):
        # Get broker name from request if provided
        broker_name = request.POST.get('broker_name', None)
        
        try:
            # Update daily prices synchronously
            if broker_name:
                result = DailyPriceManager.update_daily_prices_for_symbols(broker_name=broker_name)
                print(f"Completed daily price update for {broker_name} broker")
            else:
                result = DailyPriceManager.update_daily_prices_for_symbols()
                print("Completed daily price update for all brokers")

            # Return the results
            return JsonResponse({
                'success': True,
                'broker_name': broker_name,
                'message': f"Daily price update completed for {broker_name if broker_name else 'all brokers'}",
                'results': result
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'broker_name': broker_name,
                'message': f"Error updating daily prices: {str(e)}",
                'error': str(e)
            }, status=500)


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