from django.urls import path,include

from accounts.views import LoginMixin, UserViewSet
from rest_framework import routers


route = routers.DefaultRouter()


route.register('users',UserViewSet,basename="account")
route.register('login',LoginMixin,basename="login")



urlpatterns = [
     path("", include(route.urls)),
    
]