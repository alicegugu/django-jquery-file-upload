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
from userprofile.models import UserProfile

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

            key = pos['key']
            #key = request.META['HTTP_X_APIKEY']
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

        position_latitude = cache.get(cache_key+'latitude')
        position_longitude =  cache.get(cache_key+'longitude')

        response_data = {}
        response_data['gps_position_latitude'] = position_latitude
        response_data['gps_position_longitude'] = position_longitude

        if position_latitude is None or position_longitude is None:
            response_data['status'] = 'lost'

        if cache_key is None:
            response_data['error'] = 'User has no tag attached'
        return HttpResponse(json.dumps(response_data), content_type="application/json")

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(GPSPositionView, self).dispatch(*args, **kwargs)


class IndoorPositionView(View):
    """indoor position"""


    def get(self, request):
        user = request.user
        user_profile = UserProfile.objects.filter(user=user)[0]
        tag_id = user_profile.tag_id
        wifi_pos_index = cache.get(tag_id+'wifi_position')

        if wifi_pos_index is not None:

            wifi_position = WifiPosition.objects.filter(user =user).order_by('pk')[int(wifi_pos_index)]

            data = {}
            data['x'] = wifi_position.x
            data['y'] = wifi_position.y
            return HttpResponse(json.dumps(data), content_type="application/json")

        else:
            response_data = {}
            response_data['status'] = 'lost'
            return HttpResponse(json.dumps(response_data), content_type="application/json")

    def post(self, request):

        response_data = {}
        try:
            key = request.POST.get('key')
            if key == "set_indoor_position_key_2014":
                cache_key = request.POST.get('tag_id')

                if cache_key is None:
                    raise Exception('user has no tag attached')
                else:
                    wifi_position = request.POST.get('wifi_position')
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
    def get(self,request,contact_id=12345678):
        return HttpResponse('{hello world %s}' %contact_id)
