import requests
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views import View
from django.views.generic.edit import FormView

from todolist.authentication.forms import SignupForm, LoginForm
from ..settings import APIserver, domain
from ..models import UserToken


class SignupView(FormView):
    template_name = 'signup.html'
    form_class = SignupForm
    success_url = '.'

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = False
        user.save()
        send_confirmation_email(user)
        return HttpResponse('Please confirm your email.')


class ActivateView(View):
    def get(self, request, **kwargs):
        uidb64 = kwargs.get('uidb64', None)
        token = kwargs.get('token', None)
        uid = force_text(urlsafe_base64_decode(uidb64))
        try:
            user = User.objects.get(pk=uid)
        except(TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
        if user and token:
            if default_token_generator.check_token(user, token)\
                    and not user.is_active:
                try:
                    r = requests.post(APIserver.format('users/'), data={
                        "username": user.username,
                        "password": user.password
                    })
                except ConnectionError:
                    return HttpResponse('Failed to connect to API server')
                except:
                    return HttpResponse('Something is wrong!')
                if r.ok:
                    user.is_active = True
                    user.save()
                    obtain_auth_token(user)
                    login(request, user)
                    return redirect('/todolists/')
                elif r.status_code == 400:
                    return HttpResponse('User with this name already exists')
                else:
                    return HttpResponse('Server error ' + str(r.status_code))
        return HttpResponse('Activation link is invalid!')


class LoginView(FormView):
    template_name = 'login.html'
    form_class = LoginForm
    success_url = '/todolists/'

    def form_valid(self, form):
        user = form.get_user()
        if user.is_active:
            check_auth_token(user)
            login(self.request, user)
            return redirect('/todolists/')
        send_confirmation_email(user)
        return HttpResponse('Please confirm your email.'
                            ' A link has been sent to {}.'
                            .format(user.email))


def send_confirmation_email(user):
    message = render_to_string('activation_email.html', {
        'user': user,
        'domain': domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': default_token_generator.make_token(user),
    })
    mail_subject = 'Todolist account activation'
    email = EmailMessage(mail_subject, message, to=[user.email])
    email.send()


def obtain_auth_token(user):
    try:
        response = requests.post(APIserver.format('api-token-auth/'), data={
            'username': user.username,
            'password': user.password
        })
        print(response.text)
    except:
        return None
    if response.ok:
        token = response.json().get('token', None)
        UserToken.objects.create(user=user, token=token)
        return token
    return None


def check_auth_token(user):
    try:
        token = user.usertoken.token
    except:
        token = obtain_auth_token(user)
    return token
