"""remote_control URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from django.http import StreamingHttpResponse
from django.urls import path
from . import views, settings
from .driver.stream import VideoCamera, gen
            
urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', views.home),
    url(r'^run/$', views.run),
    url(r'^cali/$', views.cali),
    url(r'^connection_test/$', views.connection_test),
    url(r'^monitor/$', views.monitor),
    url(r'^monitor2/$', views.monitor2),
]         
