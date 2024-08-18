from django.shortcuts import render
from django.http import HttpResponse

def symbols(request):
	return HttpResponse("Hello world from symbols") #also its possible o pass html inside the function

