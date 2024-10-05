from django.db import models
from datetime import timedelta

class APIKey(models.Model):
    api_key = models.CharField(max_length=255)
    def __str__(self):
        return self.api_key
class FineTunningModel(models.Model):
    model_name = models.CharField(max_length=255,null=True,blank=True)
    model_id = models.CharField(max_length=255,unique=True)
    output_model = models.CharField(max_length=255,null=True,blank=True)
    created_at = models.DateTimeField()
    selected = models.BooleanField(default=False)

class FineTuneExample(models.Model):
    user = models.TextField()
    system = models.TextField(null=True,blank=True)
    assistant = models.TextField()
