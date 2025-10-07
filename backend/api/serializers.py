from rest_framework import serializers
from .models import Paper

class PaperSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Paper
        fields = ('title', 'authors', 'year', 'doi', 'venue', 'abstract', 'fields_of_study', 'citation_count', 'url')