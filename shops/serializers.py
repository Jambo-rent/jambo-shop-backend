
from rest_framework import serializers
# settings messages
from django.conf import settings

from accounts.serializers import UserInfoSerializer
from shops.models import Stock

class Stockserializer(serializers.ModelSerializer):
    owner_detail=UserInfoSerializer(
        source='owner', read_only=True)
    class Meta:
        model = Stock
        fields = fields = [
            'id',
            'stock_name',
            'owner',
            'owner_detail',
            'village',
            'lng',
            'lat',
            'location',
            'is_close',
            'type',
            'phone_number',
            'created_on',
        ]
