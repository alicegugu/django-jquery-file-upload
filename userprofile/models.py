from django.db import models
from django.contrib.auth.models import User
from time import time


# Create your models here.
class UserProfile(models.Model):
	user =  models.OneToOneField(User)
	contact_number = models.CharField(max_length=10)
	tag_id = models.CharField(max_length=20)
	
User.profile = property(lambda u: UserProfile.objects.get_or_create(user=u)[0])		