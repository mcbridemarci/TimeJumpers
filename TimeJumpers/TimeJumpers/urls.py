"""TimeJumpers URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from TimeJumpers_app import views
#from .dajaxice.core import dajaxice_autodiscover, dajaxice_config
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name="Homepage"),
    path('specify/', views.specify, name="Specify"),
    path('login/', views.login, name="Login"),
    path('query/', views.query_video, name="Query"),
    path('queryLocal/', views.query_local, name="Query"),
    path('testDBWrite/', views.testDBWrite, name="testDBWrite"),
    path('testTimeJump/', views.testTimeJump, name="testTimeJump"),
    path('testLocalVideo/', views.testLocalVideo, name="testLocalVideo"),
    path('getJSONTranscripts/', views.getJSONTranscripts, name="(none)")
]

#urlpatterns += patterns('',
#   url(r'^%s/' % settings.DAJAXICE_MEDIA_PREFIX, include('dajaxice.urls')),)
    
urlpatterns += staticfiles_urlpatterns()
