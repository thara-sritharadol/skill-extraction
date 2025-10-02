from django.db import models

class Paper(models.Model):
    title = models.TextField()
    authors = models.TextField()
    year = models.IntegerField(null=True, blank=True)
    doi = models.CharField(max_length=255, unique=True)
    venue = models.CharField(max_length=255, null=True, blank=True)
    abstract = models.TextField(null=True, blank=True)
    fields_of_study = models.TextField(null=True, blank=True)
    citation_count = models.IntegerField(default=0)
    url = models.URLField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.title} ({self.year})"

    
