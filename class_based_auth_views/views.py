#-*- coding: utf-8 -*-
import urlparse
from class_based_auth_views.utils import default_redirect
from django.contrib import auth
from django.contrib.auth import REDIRECT_FIELD_NAME, login
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.generic import View
from django.views.generic.base import TemplateResponseMixin
from django.views.generic.edit import FormView
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.core.context_processors import csrf
from fileupload.models import Picture, WifiPosition
from django.contrib.auth.forms import UserCreationForm

from django.views.generic.base import View
from django.views.decorators.csrf import csrf_exempt
import json
from django.core import serializers
from django.core.cache import cache
#call "OutdoorPosition" from models.py 
from userprofile.models import OutdoorPosition
from userprofile.models import UserProfile , IndoorPosition

from datetime import datetime, timedelta
import datetime


'''------------------------RESTful apis-----------------------------
'''

class WifiPositionView(View):
    """Set and Delete wifi position"""
    def post(self, request):
        position = request.raw_post_data

        pos=json.loads(position)
        print pos

        p = WifiPosition()
        p.x = pos['x']
        p.y = pos['y']
        p.user = request.user
        p.save()

        return HttpResponse('{saved wifi position}')

    def delete(self, request):
        user = request.user
        WifiPosition.objects.filter(user=user).delete()
        return HttpResponse('{delete wifi position}')

    def get(self, request):
        poss = WifiPosition.objects.filter(user=request.user).order_by('-pk')

        data = serializers.serialize('json', poss)

        return HttpResponse(data , content_type="application/json")

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(WifiPositionView, self).dispatch(*args, **kwargs)


class GPSPositionView(View):
    """Set and Get GPS Position"""
    def post(self, request):
        response_data = {}

        try:

            request_data = request.raw_post_data
            pos = json.loads(request_data)

            #key = pos['key']
            key = request.META['HTTP_X_APIKEY']
            cache_key = pos['tag_id']

            position_latitude = pos['position_latitude']
            position_longitude = pos['position_longitude']
			

            if key == "set_gps_position_key_2014":
                

                if cache_key is None:
                    raise Exception('tag id can not be none')

                if position_latitude is None:
                    raise Exception('latitude can not be none')

                if position_longitude is None:
                    raise Exception('longitude can not be none')

                # position will be updated for 30 sec
                cache_time = 30
                cache.set(cache_key+'latitude', position_latitude, cache_time)
                cache.set(cache_key+'longitude', position_longitude, cache_time)
                response_data['latitude'] = position_latitude
                response_data['longitude'] = position_longitude
				
				#saving the latitude and longitude values to the table
                s = OutdoorPosition()
				#List down all the defined from "OutdoorPosition()"
                s.latitude = position_latitude	
                s.longitude = position_longitude
                s.tag_id= cache_key
                s.save()

            else:
                raise Exception('key can not be empty')

        except Exception, e:
            response_data['errors'] = []
            response_data['errors'].append(str(e))
        else:
            pass
        finally:
            pass


        return HttpResponse(json.dumps(response_data), content_type="application/json")
        
    def get(self, request):
        user = request.user

        # get tag id from User table
        profile = UserProfile.objects.filter(user=user)[0]
        cache_key = profile.tag_id
		#UNCOMMENT to see all the data in db
        outp = OutdoorPosition.objects.all()
		
		#timestamp
        from datetime import datetime, timedelta
        current_time = datetime.now()
        timewant = current_time - timedelta(days=1)

		
		
		#UNCOMMENT to see all data from db, GOOGLE for more info on 'serializers' DATA is here
        from django.core import serializers
        data = serializers.serialize("json", OutdoorPosition.objects.all().filter(timestamp__range=(timewant,current_time)).order_by('-timestamp'))
		
		#//
        #record = OutdoorPosition.objects.filter(id=6)[0]
        #outp2 = outp.filter(tag_id=cache_key).order_by('-timestamp')     -----xWRONG
		#.get(id=5)     -----xWRONG
		#//
        #position_latitude = record.latitude
        #position_longitude=record.longitude
		#//
        #position_latitude= data.latitude
        #position_longitude= data.longitude
        #time_stamp= data.timestamp
	
        #position_latitude = OutdoorPosition.objects.get(latitude)  -----xWRONG
        #position_longitude =  OutdoorPosition.objects.get(longitude)   -----xWRONG

        #print position_latitude-------------------------------------
        #response_data = {}
		#Nest 2 lines to see individual data according to 'id' needed from 'record'
        #response_data['gps_position_latitude'] = position_latitude
        #response_data['gps_position_longitude'] = position_longitude
		#// IMPORTANT
        #data_response={}
        #data_response['gps_position_latitude']= position_latitude
        #data_response['gps_position_longitude']= position_longitude
        #data_response['past24']= time_stamp

        #response_data['all'] = outp
		#UNCOMMENT NEXT 2 LINES to see all data from db 
        #if position_latitude is None or position_longitude is None:
        #    response_data['status'] = 'lost'

        #if cache_key is None:
        #    response_data['error'] = 'User has no tag attached'
        #return HttpResponse(json.dumps(response_data), content_type="application/json")
		#UNCOMMENT to see 'data'
        return HttpResponse(data, content_type="application/json")

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(GPSPositionView, self).dispatch(*args, **kwargs)


class IndoorPositionView(View):
    """indoor position"""


    def get(self, request):
        user = request.user
        user_profile = UserProfile.objects.filter(user=user)[0]
        tag_id = user_profile.tag_id	
        idpo = IndoorPosition.objects.all()															#get all the objects in IndoorPosition
        #list = idpo.filter(tag_id = tag_id).order_by('-timestamp')[0]								#filter it by the tag_id and sort it by the timestamp and get the first arrary
        #wifi_pos_index = list.indoorposition														#call the indoorpositon object
       	   
        now = datetime.datetime.now()
        newtime = now - timedelta(hours=24)
		
        get24 = idpo.filter(timestamp__range=(newtime,now)).order_by('timestamp')					#filter the time to get the time within alst 24 hours
        list24 = get24.values_list()																#make a queryset to a list 
        wifi_positions = []				 															#make a list to add many dictionary data in 
        for idp in list24:
            wifi_post = {}
            wifi_post['indoorposition'] = idp[1]													#get the indoorposition from the list 
            wifi_positions.append(wifi_post)														#and add it to the list 
        
        if wifi_positions is not None:

            
            list48 = []																				
            for i in wifi_positions:																#i is the dictionary 
                indoor = i['indoorposition']														#to get the indoorposition number from the list 
                wifi = WifiPosition.objects.filter(user=user).order_by('pk')[int(indoor)]
                data = {}   
                data['x'] = wifi.x
                data['y'] = wifi.y
                list48.append(data)
		
            return HttpResponse(json.dumps(list48), content_type="application/json")
           
		
        #if wifi_pos_index is not None:
            
            #wifi_position = WifiPosition.objects.filter(user=user).order_by('pk')[int(wifi_pos_index)]
        #    print wifi_position

        #    data = {}
        #    data['x'] = wifi_position.x
        #    data['y'] = wifi_position.y
        #   return HttpResponse(json.dumps(data), content_type="application/json")

        else:
            response_data = {}
            response_data['status'] = 'lost'
            return HttpResponse(json.dumps(response_data), content_type="application/json")

    def post(self, request):

		response_data = {}
		p = IndoorPosition()										#as cache_key/wifi_position are unicode object, it cannot be save so it need equate it to IndoorPosition to be saved 

		try:
			request_data = request.raw_post_data
			pos = json.loads(request_data)


			#key = pos['key']
			key = request.META['HTTP_X_APIKEY']

			if key == "set_indoor_position_key_2014":
				cache_key = pos['tag_id']
				p.tag_id = cache_key
					
				if cache_key is None:
					raise Exception('user has no tag attached')
				else:
					wifi_position = pos['wifi_position']
					p.indoorposition = wifi_position
					p.save()
					cache_time = 30
					cache.set(cache_key+'wifi_position', wifi_position, cache_time)							
					
			else:
				raise Exception('wrong key')
		except Exception, e:
			response_data['errors'] = []
			response_data['errors'].append(str(e))
		else:
			pass
		finally:
			pass

		return HttpResponse(json.dumps(response_data), content_type="application/json")
          

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(IndoorPositionView, self).dispatch(*args, **kwargs)     
'''--------------------------------------------------------------------
'''



class IndoorTrackingView(View):
    def get(self, request):
        user = request.user
        pic = Picture.objects.filter(user=user).order_by('-pk')
        args = {}
        args['username'] = request.user.username
        args['STATIC_URL'] = '/static/'
        if pic is not None:
            args['layout'] =  pic[0].file
        return render_to_response("indoor_tracking.html", args)

class OutdoorTrackingView(View):
    def get(self, request):
        user = request.user
        args = {}
        args['username'] = request.user.username
        args['STATIC_URL'] = '/static/'
        return render_to_response("outdoor_tracking.html", args)

class RegisterView(View):
    """docstring for RegisterView"""
    def get(self, request):
        args = {}
        args.update(csrf(request))
        args['STATIC_URL'] = '/static/'
        args['form'] = UserCreationForm()
        return render_to_response("register.html", args)

    def post(self, request):
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = self.request.POST.get('username', '')
            password = self.request.POST.get('password1', '')
            user = auth.authenticate(username=username, password=password)
    
            if user is not None:
                auth.login(self.request, user)
                return HttpResponseRedirect('/upload/basic/')
            else:
                return HttpResponse('register failed')
        else:
            return HttpResponse('form is not valid')
        
class LoginView(FormView):
    """
    This is a class based version of django.contrib.auth.views.login.

    Usage:
        in urls.py:
            url(r'^login/$',
                LoginView.as_view(
                    form_class=MyCustomAuthFormClass,
                    success_url='/my/custom/success/url/),
                name="login"),

    """
    form_class = AuthenticationForm
    redirect_field_name = REDIRECT_FIELD_NAME
    template_name = 'index.html'

    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        return super(LoginView, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        """
        The user has provided valid credentials (this was checked in AuthenticationForm.is_valid()). So now we
        can check the test cookie stuff and log him in.
        """
        self.check_and_delete_test_cookie()
        login(self.request, form.get_user())
        return super(LoginView, self).form_valid(form)

    def form_invalid(self, form):
        """
        The user has provided invalid credentials (this was checked in AuthenticationForm.is_valid()). So now we
        set the test cookie again and re-render the form with errors.
        """
        self.set_test_cookie()
        return super(LoginView, self).form_invalid(form)

    def get_success_url(self):
        if self.success_url:
            redirect_to = self.success_url
        else:
            redirect_to = self.request.REQUEST.get(self.redirect_field_name, '')

        netloc = urlparse.urlparse(redirect_to)[1]
        if not redirect_to:
            redirect_to = settings.LOGIN_REDIRECT_URL
        # Security check -- don't allow redirection to a different host.
        elif netloc and netloc != self.request.get_host():
            redirect_to = settings.LOGIN_REDIRECT_URL
        return redirect_to

    def set_test_cookie(self):
        self.request.session.set_test_cookie()

    def check_and_delete_test_cookie(self):
        if self.request.session.test_cookie_worked():
            self.request.session.delete_test_cookie()
            return True
        return False

    def get(self, request, *args, **kwargs):
        """
        Same as django.views.generic.edit.ProcessFormView.get(), but adds test cookie stuff
        """
        self.set_test_cookie()
        return super(LoginView, self).get(request, *args, **kwargs)

    def post(self, *args, **kwargs):
        username = self.request.POST.get('username', '')
        password = self.request.POST.get('password', '')
        user = auth.authenticate(username=username, password=password)
    
        if user is not None:
            auth.login(self.request, user)
            return HttpResponseRedirect('/upload/basic/')
        else:
            args = {}
            args['invalid'] = True
            args['STATIC_URL'] = 'static/'
            args.update(csrf(self.request))
            return render_to_response('index.html', args) # our template can detect this variable


class LogoutView(TemplateResponseMixin, View):
    template_name = "index.html"
    redirect_field_name = "next"

    def get(self, *args, **kwargs):
        if not self.request.user.is_authenticated():
            return redirect(self.get_redirect_url())
        context = self.get_context_data()
        return self.render_to_response(context)

    def post(self, *args, **kwargs):
        if self.request.user.is_authenticated():
            auth.logout(self.request)
        return redirect(self.get_redirect_url())

    def get_context_data(self, **kwargs):
        context = kwargs
        redirect_field_name = self.get_redirect_field_name()
        context.update({
            "redirect_field_name": redirect_field_name,
            "redirect_field_value": self.request.REQUEST.get(redirect_field_name),
            })
        return context

    def get_redirect_field_name(self):
        return self.redirect_field_name

    def get_redirect_url(self, fallback_url=None, **kwargs):
        if fallback_url is None:
            fallback_url = settings.LOGIN_URL
        kwargs.setdefault("redirect_field_name", self.get_redirect_field_name())
        return default_redirect(self.request, fallback_url, **kwargs)
		

class ContactNumber(View):
    def get(self,request,tag_id):
		response_data = {}
		#security-like feature, X-Apikey in postman 
		key = request.META['HTTP_X_APIKEY']
		
		#"key" is similar to a password
		if key == "contact_number_2014":
		
		
			if tag_id is not None:
				#data from the "forms" stored
				query = UserProfile.objects.filter(tag_id = tag_id)
			if len(query) == 0:
				response_data['errors'] = []
				response_data['errors'].append("Can not find contact number for this device")
			if len(query) == 1:
				#display "contact_number" as from "tag_id"
				response_data['contact_number'] = query[0].contact_number
			if len(query) > 1:
				response_data['errors'] = []
				response_data['errors'].append("more than one contact number were found")
		#if the key is wrong, display error message	
		else:
			response_data['errors'] = []
			response_data['errors'].append("error: enter the key")


			
		return HttpResponse(json.dumps(response_data), content_type="application/json")

class On_or_Off(View):
    def get (self, request, tag_id):
		response_data = {}
	
		try:
			#tag_id = request.get('tag_id') #no need this line as it has alrdy gotten the tag_id 	
			#pos = json.dumps(tag_id)	
			#key = pos['key']
			
			key = request.META['HTTP_X_APIKEY']
			
			if key == "1234567890":
				if tag_id is not None:
					query = UserProfile.objects.filter(tag_id = tag_id)		#search the database
					if len(query) == 0:										#if there is no set of models for the userprofile
						response_data['errors'] = []						#before append data we will need a blank 
						response_data['errors'].append("Can not find on/off for this device")
					if len(query) == 1:
						on_off = query[0].on_or_off							#get the first set of data and call the on_or_off and store it to a variable 
						response_data['on_off'] = on_off					#show the data
					if len(query) > 1:
						response_data['errors'] = []
						response_data['errors'].append("more than one on/off were found")
			#else:	
			#	response_data['errors'].append("There's no tag id")
			#	query.tag_id
			else:
				response_data['errors'] = []
				response_data['errors'].append("key cannot be empty")
				
		except Exception, e:
			response_data['errors'] = []
			response_data['errors'].append(e)
		else:
			pass
		finally:
			pass
	
		return HttpResponse(json.dumps(response_data), content_type="application/json")
   
