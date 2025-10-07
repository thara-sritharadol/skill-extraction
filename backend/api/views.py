from django.http import HttpResponse

from rest_framework import viewsets
from .serializers import PaperSerializer
from .models import Paper

class PaperViewSet(viewsets.ModelViewSet):
    queryset = Paper.objects.all().order_by('title')
    serializer_class = PaperSerializer

"""
def index(request):
    return HttpResponse("Hello. Welcome to my APIs")
"""