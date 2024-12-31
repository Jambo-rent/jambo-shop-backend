import logging
from django.shortcuts import render
from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry
from django.utils import timezone
from django.core.cache import cache
from django.db.models import Q, Count
from django.contrib.auth import get_user_model
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point

from rest_framework.decorators import action
from rest_framework.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_200_OK, HTTP_403_FORBIDDEN
from rest_framework.viewsets import mixins
from rest_framework import viewsets,status
from rest_framework.response import Response

from accounts.permissions import BaseAuthPermission
from shops.models import Stock
from shops.permissions import IsShoper
from shops.serializers import Stockserializer
from django.contrib.gis.measure import D
from utils.geo_location import point
# Create your views here.

logger = logging.getLogger(__name__)
# user account creation
User = get_user_model()


class StockViewset(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = Stockserializer
    permission_classes = [BaseAuthPermission]
    queryset = Stock.objects.all()
    
    def get_permissions(self):
        if self.request.method =="POST":
            self.permission_classes = [IsShoper]
        elif self.request.method =="PATCH":
            self.permission_classes = IsShoper
        elif self.request.method =="PUT":
            self.permission_classes = [IsShoper]
        elif self.request.method =="DELETE":
            self.permission_classes = IsShoper
        
        return super().get_permissions()
    
    def get_queryset(self):
        if self.request.user.user_type==User.SHOPER:
            return Stock.objects.filter(
                owner=self.request.user).select_related()
        return Stock.objects.all().select_related()
    
    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response({"stores": serializer.data}, status=status.HTTP_200_OK)
    
    @action(["get"], detail=False)
    def near_store(self, request, *args, **kwargs):
        lat = float(self.request.GET.get('lat') or 0)
        lng = float(self.request.GET.get('lng') or 0)
        user_location = Point(lng, lat, srid=4326)
    
        # Filter and annotate queryset with distance
        query_set = (
            Stock.objects.annotate(
                distance=Distance('location', user_location)
            )
            .filter(location__distance_lt=(user_location, D(km=settings.DISTANCE_KM)))
            .order_by('distance')  # Sort by distance (ascending)
        )
        serializer = self.get_serializer(query_set, many=True)
        return Response({"near_stores": serializer.data},status=status.HTTP_200_OK)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(owner=request.user)
        return Response(serializer.data, status=HTTP_201_CREATED)


