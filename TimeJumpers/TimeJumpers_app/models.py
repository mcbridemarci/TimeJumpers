from django.db import models

# Create your models here.

class User(models.Model):
    email = models.CharField(max_length=1000)
    password = models.CharField(max_length=1000)

class Video(models.Model):
    location = models.CharField(max_length=1000)
    transcriptID = models.CharField(max_length=80)
    userID = models.IntegerField(default=0)
