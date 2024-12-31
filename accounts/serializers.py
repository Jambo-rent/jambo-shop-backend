import datetime
from accounts.models import UserAddress, VerificationCode
from djoser.serializers import UserCreateSerializer, UserSerializer,SetUsernameSerializer

from django.core import exceptions as django_exceptions
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.conf import settings
from django.contrib.auth.password_validation import validate_password

from utils.geo_location import point


User = get_user_model()


class UserCreationSerializer(UserCreateSerializer):
    # email=serializers.EmailField(required=True)
    class Meta(UserCreateSerializer.Meta):
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "user_type",
            "phone_number",
            "password",
            "is_staff",
            "is_active",
            "date_of_birth",
            "is_phone_visible",
            "profile_image"
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
    def create(self, validated_data):
        return super().create(validated_data)

class GetUserLocationSerializer(serializers.ModelSerializer):
    """
    This serializer represents User location 
    """
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    lng= serializers.DecimalField(max_digits=22, decimal_places=16)
    lat= serializers.DecimalField(max_digits=22, decimal_places=16)
    class Meta:
        model = UserAddress
        fields = [
            "id",
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

    user_location = GetUserLocationSerializer(
        source="user_address", read_only=True)
   
    
    class Meta(UserSerializer.Meta):
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "date_of_birth",
            "user_type",
            "phone_number",
            "profile_image",
            "user_location",
            "last_login",
            "created_on"
        )



class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    
    @classmethod
    def get_token(cls, user):
        User.objects.filter(id=user.id).update(
            last_login=datetime.datetime.now())
        user.save()
        token = super().get_token(user)
        # Add custom claims
        token["username"] = user.username
        token["email"] = user.email
        token["first_name"] = user.first_name
        token["phone_number"] = user.phone_number
     
        return token
    
class ActivationSerializer(serializers.Serializer):
    email=serializers.EmailField(required=True)
    token = serializers.CharField(
        required=True, max_length=settings.VERIFICATION_CODE_LENGTH)
    
    def validate(self, value):
        try:
            instance = VerificationCode.objects.get(user__email=value.get("email"),code=value.get("token"), status=False)
            if instance.valid:
                return instance
            else:
                raise serializers.ValidationError(
                    settings.ACCOUNT_CONSTANTS.messages.CODE_NOT_VALID)
        except VerificationCode.DoesNotExist:
            raise serializers.ValidationError(
                settings.ACCOUNT_CONSTANTS.messages.CODE_NOT_VALID)

class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    label=serializers.ChoiceField(choices=VerificationCode.VERIFICATION_CODE_CHOICES)
    
    def validate(self, value):
        lower_email = value.get("email").lower()
        try:
            user = User.objects.get(email=lower_email)
            return {"user":user,"email":lower_email,"label":value.get("label")}
        except User.DoesNotExist:
            return {"user":None,"email":lower_email,"label":value.get("label")}
            
class SetNewPasswordSerializer(serializers.Serializer):
    token = serializers.CharField(
        required=True, max_length=settings.VERIFICATION_CODE_LENGTH)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        min_length=8, write_only=True, required=True)
    
    def validate(self, value):
        password = value.get("password")
        lower_email = value.get("email").lower()
        if validate_password(password) is None:
            try:
                instance = VerificationCode.objects.get(user__email=lower_email,code=value.get("token"), status=False)
                if instance.valid:
                    # Check the password
                    if not instance.user.check_password(password):
                        return {"instance":instance,"password":password}
                    else:
                        raise serializers.ValidationError(
                            settings.ACCOUNT_CONSTANTS.messages.INVALID_PASSWORD
                        )
                else:
                    raise serializers.ValidationError(
                        settings.ACCOUNT_CONSTANTS.messages.CODE_NOT_VALID)
            except VerificationCode.DoesNotExist:
                raise serializers.ValidationError(
                        settings.ACCOUNT_CONSTANTS.messages.CODE_NOT_VALID)
            
    class Meta:
        field = ["password"]
    

class SetNewEmailSerializer(serializers.Serializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    token = serializers.CharField(
        required=True, max_length=settings.VERIFICATION_CODE_LENGTH)
    email = serializers.EmailField(required=True)
   
    def validate(self, value):
        lower_email = value.get("email").lower()
      
        
        try:
            instance = VerificationCode.objects.get(email=lower_email,code=value.get("token"), status=False)
            if instance.valid:
                return {"instance":instance,"email":lower_email}
            else:
                raise serializers.ValidationError(
                    settings.ACCOUNT_CONSTANTS.messages.CODE_NOT_VALID
                )
             
        except VerificationCode.DoesNotExist:
            raise serializers.ValidationError(
                    settings.ACCOUNT_CONSTANTS.messages.CODE_NOT_VALID)

class UserInfoSerializer(serializers.ModelSerializer):
 
    """
    This serializer is intended to provide minimal information
    to the user
    """
    class Meta:
        model = User
        fields = ['id',
                  'first_name',
                  'last_name',
                  'username',
                  'profile_image',
                  'date_of_birth',
                  'email',
                  'user_type',
                  'phone_number',
                  'is_active'
                  ]

  