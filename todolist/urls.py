from django.conf.urls import url
from django.contrib.auth.views import logout
from .authentication import views as auth_views
from . import views

urlpatterns = [
    url(r'^todolists/$', views.TasklistCreate.as_view(), name='lists'),
    url(r'^todolists/([0-9]+)/$', views.TasklistDetail.as_view(),
        name='list_detail'),
    url(r'^todolists/([0-9]+)/task/create/$',
        views.TaskCreate.as_view(), name='task_create'),
    url(r'^todolists/([0-9]+)/task/([0-9]+)/$',
        views.TaskDetail.as_view(), name='task_detail'),
    url(r'^signup/$', auth_views.SignupView.as_view(), name='signup'),
    url(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        auth_views.ActivateView.as_view(), name='activate'),
    url(r'^login/$', auth_views.LoginView.as_view(), name='login'),
    url(r'^logout/$', logout, {'next_page': '/login/'}, name='logout'),
]
