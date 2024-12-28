from django.shortcuts import render
from django.http import HttpResponse
from . import models
from django.views.generic import DetailView,ListView


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

class SymbolListView(ListView):
    model = models.Symbols
    template_name = 'symbols/symbol_list.html'
    context_object_name = 'symbols'
    paginate_by = 10  # Display 10 symbols per page	