from django.shortcuts import render
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets, status
from rest_framework.exceptions import NotFound
from accounts.models import (User, VerificationCode)
from accounts.serializers import CustomTokenObtainPairSerializer, GetUserLocationSerializer
from accounts.permissions import BaseAuthPermission
from djoser.compat import get_user_email
from djoser import signals

from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from djoser.conf import settings as djoser_settings
from utils.generator_code import random_with_N_digits
from rest_framework.exceptions import NotFound, APIException
from accounts.signals import verification_email_signal


# Create your views here.



class LoginMixin(viewsets.ViewSet):
    '''
        User login with either Jwt token or Two Factor auth
    '''
    custom_serializer = CustomTokenObtainPairSerializer
    queryset = User.objects.all()
    permission_classes = ()
 

    def create(self, request, *args, **kwargs):
        '''
        User login with Jwt token
        params : username , password
        return : Jwt token
        '''
        serializer = self.custom_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        return Response(serializer.validated_data, status=status.HTTP_200_OK)

   
class UserViewSet(viewsets.ModelViewSet):
    serializer_class = djoser_settings.SERIALIZERS.user
    queryset = User.objects.all()
    permission_classes = djoser_settings.PERMISSIONS.user
    token_generator = default_token_generator
    lookup_field = djoser_settings.USER_ID_FIELD

    def permission_denied(self, request, **kwargs):
        if (
            djoser_settings.HIDE_USERS
            and request.user.is_authenticated
            and self.action in ["update", "partial_update", "list", "retrieve"]
        ):
            raise NotFound()
        super().permission_denied(request, **kwargs)

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset() 
        if djoser_settings.HIDE_USERS and self.action == "list" and not user.is_staff:
            queryset = queryset.filter(pk=user.pk)
        return queryset

    def get_permissions(self):
        if self.action == "create":
            self.permission_classes = djoser_settings.PERMISSIONS.user_create
        elif self.action == "activation":
            self.permission_classes = djoser_settings.PERMISSIONS.activation
        elif self.action == "resend_activation":
            self.permission_classes = djoser_settings.PERMISSIONS.password_reset
        elif self.action == "list":
            self.permission_classes = djoser_settings.PERMISSIONS.user_list
        elif self.action == "reset_password":
            self.permission_classes =[AllowAny]
      
       
        elif self.action == "set_password":
            self.permission_classes = djoser_settings.PERMISSIONS.set_password
        elif self.action == "set_username":
            self.permission_classes = djoser_settings.PERMISSIONS.set_username
      
 
        elif self.action == "destroy" or (
            self.action == "me" and self.request and self.request.method == "DELETE"
        ):
            self.permission_classes = djoser_settings.PERMISSIONS.user_delete
        elif self.action == "validate_phone_otp":
            self.permission_classes = [AllowAny]
        elif self.action == "signing_up_code_cheking":
            self.permission_classes = [AllowAny]
        elif self.action == "user_account_activation":
            self.permission_classes = [AllowAny]
        elif self.action == "edit_user_profile":
            self.permission_classes = [BaseAuthPermission]
        elif self.action == "set_email":
            self.permission_classes = [BaseAuthPermission]
        elif self.action == "deactivate_account":
            self.permission_classes = [BaseAuthPermission]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == "create":
            if djoser_settings.USER_CREATE_PASSWORD_RETYPE:
                return djoser_settings.SERIALIZERS.user_create_password_retype
            return djoser_settings.SERIALIZERS.user_create
        elif self.action == "destroy" or (
            self.action == "me" and self.request and self.request.method == "DELETE"
        ):
            return djoser_settings.SERIALIZERS.user_delete
        elif self.action == "activation":
            return djoser_settings.SERIALIZERS.activation
        elif self.action == "resend_activation":
            return djoser_settings.SERIALIZERS.resend_activation
        elif self.action == "reset_password":
            return djoser_settings.SERIALIZERS.password_reset
       
        elif self.action == "set_password":
            if djoser_settings.SET_PASSWORD_RETYPE:
                return djoser_settings.SERIALIZERS.set_password_retype
            return djoser_settings.SERIALIZERS.set_password
        elif self.action == "set_username":
            if djoser_settings.SET_USERNAME_RETYPE:
                return djoser_settings.SERIALIZERS.set_username_retype
            return djoser_settings.SERIALIZERS.set_username
        elif self.action == "set_email":
            return djoser_settings.SERIALIZERS.set_email
    
        elif self.action == "reset_username_confirm":
            if djoser_settings.USERNAME_RESET_CONFIRM_RETYPE:
                return djoser_settings.SERIALIZERS.username_reset_confirm_retype
            return djoser_settings.SERIALIZERS.username_reset_confirm
        elif self.action == "me":
            return djoser_settings.SERIALIZERS.current_user
        elif self.action == "set_user_location":
            return GetUserLocationSerializer
     
    
    def get_instance(self):
        return self.request.user

    def perform_create(self, serializer):
        user = serializer.save()
        signals.user_registered.send(
            sender=self.__class__, user=user, request=self.request
        )
        context = {"user": user}
        to = [get_user_email(user)]
        if djoser_settings.SEND_ACTIVATION_EMAIL:
            djoser_settings.EMAIL.activation(self.request, context).send(to)
        elif djoser_settings.SEND_CONFIRMATION_EMAIL:
            djoser_settings.EMAIL.confirmation(self.request, context).send(to)
    
    def perform_update(self, serializer):

        super().perform_update(serializer)
        user = serializer.instance
        # should we send activation email after update?
        if djoser_settings.SEND_ACTIVATION_EMAIL:
            context = {"user": user}
            to = [get_user_email(user)]
            djoser_settings.EMAIL.activation(self.request, context).send(to)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(["get", "put", "patch", "delete"], detail=False)
    def me(self, request, *args, **kwargs):
        self.get_object = self.get_instance
        if request.method == "GET":
            return self.retrieve(request, *args, **kwargs)
        elif request.method == "PUT":
            return self.update(request, *args, **kwargs)
        elif request.method == "PATCH":
            return self.partial_update(request, *args, **kwargs)
        elif request.method == "DELETE":
            return self.destroy(request, *args, **kwargs)

    @action(["post"], detail=False)
    def activation(self, request, *args, **kwargs):
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.validated_data
        user = instance.user
        user.is_active = True
        user.save()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(["post"], detail=False)
    def resend_activation(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        inst=VerificationCode.objects.create(user=data.get('user'),label=data.get('label'),email=data.get('email'))
        verification_email_signal.send(
            sender=self.__class__, instance=inst.id, created=True, request=self.request)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(["post"], detail=False)
    def set_password(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        self.request.user.set_password(serializer.data["new_password"])
        self.request.user.save()

        if djoser_settings.PASSWORD_CHANGED_EMAIL_CONFIRMATION:
            context = {"user": self.request.user}
            to = [get_user_email(self.request.user)]
            djoser_settings.EMAIL.password_changed_confirmation(
                self.request, context).send(to)

        return Response(status=status.HTTP_204_NO_CONTENT)
    
    
    @action(["post"], detail=False)
    def reset_password(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user=serializer.validated_data.get('instance').user
        user.set_password(serializer.validated_data.get("password"))
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
           
    @action(["post"], detail=False, url_path="set_{}".format(User.USERNAME_FIELD))
    def set_username(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self.request.user
        new_username = serializer.data["new_" + User.USERNAME_FIELD]

        setattr(user, User.USERNAME_FIELD, new_username)
        user.save()
        if djoser_settings.USERNAME_CHANGED_EMAIL_CONFIRMATION:
            context = {"user": user}
            to = [get_user_email(user)]
            djoser_settings.EMAIL.username_changed_confirmation(
                self.request, context).send(to)
        return Response(status=status.HTTP_204_NO_CONTENT)
    

    @action(['post'], detail=False)
    def set_email(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        instance = serializer.validated_data['instance']
        request.user.email = instance.email
        request.user.save()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(['post'], detail=False)
    def set_user_location(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(data=serializer.data,status=status.HTTP_200_OK)
    
    @action(["post"], detail=False,url_path='deactivate-account')
    def deactivate_account(self, request):
        user = request.user
        user.has_deactivated = True
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    
