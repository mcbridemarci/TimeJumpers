from django.db import models

# Create your models here.

class Video(models.Model):
    location = models.CharField(max_length=1000)
    transcriptID = models.CharField(max_length=80)
