from django import forms
from models import UserProfile

class UserProfileForm(forms.ModelForm):
	
	class Meta:
		model = UserProfile
		fields = ('contact_number','tag_id', 'on_or_off')