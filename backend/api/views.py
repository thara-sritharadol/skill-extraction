#from django.http import HttpResponse

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .serializers import PaperSerializer
from .models import Paper
#from .services.skill_matcher import load_skills, extract_skills

from rest_framework.permissions import AllowAny

class PaperViewSet(viewsets.ModelViewSet):
    queryset = Paper.objects.all().order_by('title')
    serializer_class = PaperSerializer
    
    #For Development
    #permission_classes = [AllowAny]
    
    
    @action(detail=False, methods=['get'])
    def by_author(self, request):
        author = request.query_params.get('author', None)
        if author is not None:
            papers = Paper.objects.filter(authors__icontains=author)
            serializer = self.get_serializer(papers, many=True)
            return Response(serializer.data)
        return Response({"error": "No author specified."}, status=400)
    
    """
    @action(detail=True, methods=['post'])
    def extract_skills(self, request, pk=None):
        paper = self.get_object()
        text = f"{paper.title}. {paper.abstract or ''}"

        skills = load_skills()  # โหลด ESCO dataset
        matched = extract_skills(text, skills, threshold=0.7)

        return Response({
            "paper_id": paper.id,
            "title": paper.title,
            "matched_skills": matched
        })
    """
    
    

        

"""
def index(request):
    return HttpResponse("Hello. Welcome to my APIs")
"""