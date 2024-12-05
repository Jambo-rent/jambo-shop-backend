import datetime
from accounts.models import ProfilePicture, UserAddress
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from django.contrib.auth import get_user_model

from utils.geo_location import point


User = get_user_model()


class UserCreationSerializer(UserCreateSerializer):
    email=serializers.EmailField(required=True)
    class Meta(UserCreateSerializer.Meta):
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "user_type",
            'phone_number',
            "password",
        )
   
    
    def validate(self, attrs):
        # if username is not one word raise an error
        username = attrs.get('username')
        if username and len(username.split()) > 1:
            raise serializers.ValidationError(
                {"username": "username must be one word"})
        
        email = attrs.get("email")
        # check if this email exists in DB irregardeless of the case sensitivness all converted to lower case before chacking and raise error if it exists
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError(
                {"email": "user with this email address already exists."}
            )
        return attrs


class ProfilePictureSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    
    class Meta:
        model = ProfilePicture
        fields = ["user", "high_res", "medium_res", "low_res"]
        read_only_fields = ["medium_res", "low_res"]
    
    def create(self, validated_data):
        has_prof, create = ProfilePicture.objects.get_or_create(
            user=validated_data['user'])
        has_prof.high_res = validated_data['high_res']
        has_prof.save()
        return has_prof

class GetUserLocationSerializer(serializers.ModelSerializer):
    """
    This serializer represents User location 
    """
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    
    class Meta:
        model = UserAddress
        fields = [
            "user",
            "village",
            "lng",
            "lat",
        
        ]
    
    def create(self, validated_data):
        instance, _ = UserAddress.objects.update_or_create(village=validated_data.get("village"),user=validated_data.get('user'), defaults={'location': point(validated_data.get("lng"), validated_data.get(
            "lat")), 'lat': validated_data.get("lat"), 'lng': validated_data.get("lng")})
        return instance




class UserAccountSerializer(UserSerializer):
    
    profile_image = ProfilePictureSerializer(
        source='user_address', read_only=True)
    user_location = GetUserLocationSerializer(
        source="my_settings", read_only=True)
   
    
    class Meta(UserSerializer.Meta):
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "user_type",
            "phone_number",
            "user_location"
        )



class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

        

    @classmethod
    def get_token(cls, user):
        User.objects.filter(id=user.id).update(
            last_login=datetime.datetime.now())
        # user.save()
        token = super().get_token(user)
        # Add custom claims
        token["username"] = user.username
        token["email"] = user.email
        token["first_name"] = user.full_name
        token["phone_number"] = user.phone_number
     
        return token

