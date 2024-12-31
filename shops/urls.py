from django.urls import path,include

from rest_framework import routers

from shops.views import StockViewset


route = routers.DefaultRouter()


route.register('stock',StockViewset,basename="stock-set")
# route.register('login',LoginMixin,basename="login")



urlpatterns = [
     path("", include(route.urls)),
    
]