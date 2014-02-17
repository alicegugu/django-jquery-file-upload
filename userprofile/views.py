from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.core.context_processors import csrf
from forms import UserProfileForm
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from models import UserProfile
import json
import pika
import logging

@login_required
def user_profile(request):
	if request.method == 'POST' and request.is_ajax():
		form = UserProfileForm(request.POST, request.FILES,instance=request.user.profile)
		if form.is_valid():
			form.save()
			#return HttpResponseRedirect('/accounts/loggedin')
			return HttpResponse("Update success")
		else:
			#return HttpResponseRedirect('/accounts/loggedin')
			return HttpResponse("Update error")
			
	else:
		user = request.user
		profile = user.profile
		form = UserProfileForm(instance=profile)
		
	args = {}
	args.update(csrf(request))
	args['form'] = form
	args['username'] = request.user.username
	args['STATIC_URL'] = '/static/'
	return render_to_response('profile.html', args)

def alert_api(request):
	if request.method == 'GET':
		response_data = {}
		response_data['errors'] = []
		try:
			tag_id = request.GET.get('tag_id')
			key =  request.GET.get('key')

			if tag_id is None:
				response_data['errors'].append("tag_id is None")
			else:
				if key == 'alert_key_2014':

					#Find the contact number according to the tag
					query = UserProfile.objects.filter(tag_id = tag_id)
					if len(query) == 0:
						response_data['errors'].append("Can not find contact number for this device")
					if len(query) == 1:
						contact_number = query[0].contact_number

						connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
						channel = connection.channel()
						channel.queue_declare(queue='alert')
						channel.basic_publish(exchange='',
		                      routing_key='alert',
		                      body=contact_number)
						response_data['contact_number'] = contact_number
					if len(query) > 1:
						response_data['errors'].append("more than one contact number were found")
				else:
					response_data['errors'].append("wrong key")


		except Exception, e:
			response_data['errors'].append(e)
		else:
			pass
		finally:
			pass

		return HttpResponse(json.dumps(response_data), content_type="application/json")

def end_api(request):
	if request.method == 'GET':
		response_data = {}
		connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
		channel = connection.channel()
		channel.queue_declare(queue='alert')

		message = "end"
		channel.basic_publish(exchange='',
                      routing_key='alert',
                      body=message)

		response_data['message'] = message
		return HttpResponse(json.dumps(response_data), content_type="application/json")	