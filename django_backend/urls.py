"""django_backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
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
from django.urls import path,re_path
from django.urls import include, path
from rest_framework import routers
from django_backend.api import views
router = routers.DefaultRouter()
router.register(r'blocks', views.blocksViewSet)
router.register(r'outputplot', views.outputplotViewSet)
router.register(r'NgspiceCode', views.NgspiceCodeViewSet)
router.register(r'Users', views.UsersViewSet)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(router.urls)),
    #url(r'^users/(?P<user_id>\d+)/$', 'viewname', name='urlname')
    re_path(r'^senddata_topython/(?P<user_id>\w+)/(?P<circuit_name>\w+)/$', views.senddata_topython),
    re_path(r'^delete/(?P<blocks_id>\w+\;\w+)/$', views.delete),
    re_path(r'^mail/(?P<user_id>\w+)/$', views.mail),
    #path('mail',views.mail),
    #re_path(r'^getprofile/(?P<user_id>\w+)/$', views.getprofile),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
    
]


