from django.db import models
from django.contrib.auth.models import User
from time import time


# Create your models here.
class UserProfile(models.Model):
	user =  models.OneToOneField(User)
	contact_number = models.CharField(max_length=10)
	tag_id = models.CharField(max_length=20)
	# The device is on when this value is true
	on_or_off = models.BooleanField(default=True)

User.profile = property(lambda u: UserProfile.objects.get_or_create(user=u)[0])


class OutdoorPosition(models.Model):
	latitude = models.FloatField(default=0)   #float
	longitude = models.FloatField(default=0)
	timestamp = models.DateTimeField(auto_now_add=True)
	tag_id = models.CharField(max_length=8)			

class IndoorPosition(models.Model):
	indoorposition = models.IntegerField()
	tag_id = models.CharField(max_length=8)
	timestamp = models.DateTimeField(auto_now_add=True)
