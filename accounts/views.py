from django.shortcuts import render
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets, status
from rest_framework.exceptions import NotFound
from accounts.models import (User, VerificationCode)
from accounts.serializers import CustomTokenObtainPairSerializer
from accounts.permissions import BaseAuthPermission
from djoser.compat import get_user_email
from djoser import signals

from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from djoser.conf import settings as djoser_settings
from utils.generator_code import random_with_N_digits
from rest_framework.exceptions import NotFound, APIException



# Create your views here.

class LoginMixin(viewsets.ViewSet):
    '''
        User login with either Jwt token or Two Factor auth
    '''
    custom_serializer = CustomTokenObtainPairSerializer
    queryset = User.objects.all()
    permission_classes = ()
    authentication_classes = ()
    www_authenticate_realm = 'api'

    def get_authenticate_header(self, request):
        return '{0} realm="{1}"'.format(
            AUTH_HEADER_TYPES[0],
            self.www_authenticate_realm,
        )

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
            self.permission_classes = djoser_settings.PERMISSIONS.password_reset
        elif self.action == "validate_reset_password_otp":
            self.permission_classes = djoser_settings.PERMISSIONS.password_reset
        elif self.action == "reset_password_confirm":
            self.permission_classes = djoser_settings.PERMISSIONS.password_reset_confirm
        elif self.action == "set_password":
            self.permission_classes = djoser_settings.PERMISSIONS.set_password
        elif self.action == "set_username":
            self.permission_classes = djoser_settings.PERMISSIONS.set_username
        elif self.action == "reset_username":
            self.permission_classes = djoser_settings.PERMISSIONS.username_reset
        elif self.action == "reset_username_confirm":
            self.permission_classes = djoser_settings.PERMISSIONS.username_reset_confirm
        elif self.action == "edit_email_request":
            self.permission_classes = [BaseAuthPermission]
        elif self.action == "edit_email":
            self.permission_classes = [BaseAuthPermission]
        elif self.action == "destroy" or (
            self.action == "me" and self.request and self.request.method == "DELETE"
        ):
            self.permission_classes = djoser_settings.PERMISSIONS.user_delete
        elif self.action == "user_settings":
            self.permission_classes = [BaseAuthPermission]
        elif self.action == "send_otp_via_phone_number":
            self.permission_classes = [AllowAny]
        elif self.action == "resend_verification_code":
            self.permission_classes = [AllowAny]
        elif self.action == "validate_phone_otp":
            self.permission_classes = [AllowAny]
        elif self.action == "signing_up_code_cheking":
            self.permission_classes = [AllowAny]
        elif self.action == "user_account_activation":
            self.permission_classes = [AllowAny]
        elif self.action == "edit_user_profile":
            self.permission_classes = [BaseAuthPermission]
        elif self.action == "user_referree":
            self.permission_classes = [BaseAuthPermission]
        elif self.action == "two_factor_authentication_settings":
            self.permission_classes = [BaseAuthPermission]
        elif self.action == "profile_picture":
            self.permission_classes = [BaseAuthPermission]
        elif self.action == "deactivate_account":
            self.permission_classes = [BaseAuthPermission]
        elif self.action == "delete_account":
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
            return djoser_settings.SERIALIZERS.password_reset
        elif self.action == "reset_password":
            return djoser_settings.SERIALIZERS.password_reset
        elif self.action == "reset_password_confirm":
            if djoser_settings.PASSWORD_RESET_CONFIRM_RETYPE:
                return djoser_settings.SERIALIZERS.password_reset_confirm_retype
            return djoser_settings.SERIALIZERS.password_reset_confirm
        elif self.action == "set_password":
            if djoser_settings.SET_PASSWORD_RETYPE:
                return djoser_settings.SERIALIZERS.set_password_retype
            return djoser_settings.SERIALIZERS.set_password
        elif self.action == "set_username":
            if djoser_settings.SET_USERNAME_RETYPE:
                return djoser_settings.SERIALIZERS.set_username_retype
            return djoser_settings.SERIALIZERS.set_username
        elif self.action == "reset_username":
            return djoser_settings.SERIALIZERS.username_reset
        elif self.action == "reset_username_confirm":
            if djoser_settings.USERNAME_RESET_CONFIRM_RETYPE:
                return djoser_settings.SERIALIZERS.username_reset_confirm_retype
            return djoser_settings.SERIALIZERS.username_reset_confirm
        elif self.action == "me":
            return djoser_settings.SERIALIZERS.current_user
       

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
        user = serializer.user
        user.is_active = True
        user.save()
        
        # signals.user_activated.send(
        #     sender=self.__class__, user=user, request=self.request
        # )

        if djoser_settings.SEND_CONFIRMATION_EMAIL:
            context = {"user": user}
            to = [get_user_email(user)]
            djoser_settings.EMAIL.confirmation(self.request, context).send(to)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(["post"], detail=False)
    def resend_activation(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.get_user(is_active=False)

        if not djoser_settings.SEND_ACTIVATION_EMAIL or not user:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        context = {"user": user}
        to = [get_user_email(user)]
        djoser_settings.EMAIL.activation(self.request, context).send(to)

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

        # if djoser_settings.LOGOUT_ON_PASSWORD_CHANGE:
        #     utils.logout_user(self.request)
        # elif djoser_settings.CREATE_SESSION_ON_LOGIN:
        #     update_session_auth_hash(self.request, self.request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(["post"], detail=False, url_path='reset-password')
    def reset_password(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.get_user()
        if user:
            otp = random_with_N_digits(settings.VERIFICATION_CODE_LENGTH)
            verification_code = VerificationCode.objects.create(
                user=user, code=otp)
            # send_email.delay(user.full_name, verification_code.code, settings.ACCOUNT_CONSTANTS.messages.RESET_PASSWORD_VERIFICATION_EMAIL.format(
                # settings.VERIFICATION_CODE_LIFETIME.seconds//60), user.email)
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            raise NotFound(
                detail=settings.ACCOUNT_CONSTANTS.messages.EMAIL_NOT_FOUND)

    @action(["post"], detail=False, url_path='reset-password/(?P<otp>[^/.]+)')
    def validate_reset_password_otp(self, request, otp):
        OtpException = APIException
        OtpException.status_code = status.HTTP_403_FORBIDDEN
        try:
            instance = VerificationCode.objects.get(code=otp)
            if instance.valid:
                return Response(status=status.HTTP_202_ACCEPTED)
            else:
                raise OtpException(
                    settings.ACCOUNT_CONSTANTS.messages.OTP_NOT_VALID)
        except VerificationCode.DoesNotExist:
            raise OtpException(
                settings.ACCOUNT_CONSTANTS.messages.OTP_NOT_VALID)

    @action(["post"], detail=False, url_path='reset-password-confirm/(?P<otp>[^/.]+)')
    def reset_password_confirm(self, request, otp):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        OtpException = APIException
        OtpException.status_code = status.HTTP_403_FORBIDDEN
        try:
            v_instance = VerificationCode.objects.get(code=otp)
            if v_instance.valid:
                v_instance.user.set_password(
                    serializer.validated_data["new_password"])
                v_instance.user.save()
                v_instance.status = False
                v_instance.created_on = v_instance.created_on-settings.VERIFICATION_CODE_LIFETIME
                v_instance.save()
                if djoser_settings.PASSWORD_CHANGED_EMAIL_CONFIRMATION:
                    context = {"user": v_instance.user}
                    to = [get_user_email(v_instance.user)]
                    djoser_settings.EMAIL.password_changed_confirmation(
                        self.request, context).send(to)
                return Response(status=status.HTTP_204_NO_CONTENT)
            raise OtpException(
                settings.ACCOUNT_CONSTANTS.messages.OTP_NOT_VALID)
        except VerificationCode.DoesNotExist:
            raise OtpException(
                settings.ACCOUNT_CONSTANTS.messages.OTP_NOT_VALID)

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

    @action(["post"], detail=False, url_path="reset_{}".format(User.USERNAME_FIELD))
    def reset_username(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.get_user()

        if user:
            context = {"user": user}
            to = [get_user_email(user)]
            djoser_settings.EMAIL.username_reset(
                self.request, context).send(to)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(["post"], detail=False, url_path="reset_{}_confirm".format(User.USERNAME_FIELD))
    def reset_username_confirm(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_username = serializer.data["new_" + User.USERNAME_FIELD]

        # setattr(serializer.user, User.USERNAME_FIELD, new_username)
        # if hasattr(serializer.user, "last_login"):
        #     # serializer.user.last_login = now()
        # serializer.user.save()

        if djoser_settings.USERNAME_CHANGED_EMAIL_CONFIRMATION:
            context = {"user": serializer.user}
            to = [get_user_email(serializer.user)]
            djoser_settings.EMAIL.username_changed_confirmation(
                self.request, context).send(to)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(['post'], detail=False)
    def resend_verification_code(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        q = VerificationCode.objects.create(user=serializer.validated_data['email'], code=random_with_N_digits(
            settings.VERIFICATION_CODE_LENGTH), email=serializer.validated_data['email'].email, label=VerificationCode.SIGNUP)
        body = "Your Whatslike verification code is : "
        # send_email.delay(q.user.full_name, q.code, body,  q.user.email)
        return Response({"message": settings.ACCOUNT_CONSTANTS.messages.VERIFICATION_CODE_SENT}, status=status.HTTP_201_CREATED)

    @action(['post', 'patch'], detail=False)
    def edit_email(self, request, *args, **kwargs):
        if request.method == "POST":
            serializer = self.get_serializer(
                data=request.data, context={"user": request.user})
            serializer.is_valid(raise_exception=True)
            q = VerificationCode.objects.create(
                user=request.user, code=random_with_N_digits(settings.VERIFICATION_CODE_LENGTH))
            serializer.save()
            # verification_email_signal.send(
            #     sender=self.__class__, instance=serializer.data['id'], created=True, request=self.request
            # )
            return Response({"message": settings.ACCOUNT_CONSTANTS.messages.EMAIL_CHANGE_VERIFICATION_EMAIL}, status=status.HTTP_201_CREATED)

        elif request.method == "PATCH":
            serializer = self.get_serializer(
                data=request.data, context={"user": request.user})
            serializer.is_valid(raise_exception=True)
            instance = serializer.validated_data['code']
            instance = VerificationCode.objects.get(code=instance)
            user = instance.user
            user.email = instance.email
            user.save()
            instance.status = True
            instance.save()
            return Response({"message": settings.ACCOUNT_CONSTANTS.messages.EMAIL_CHANGE_COMFIRMED}, status=status.HTTP_200_OK)
    
    # @action(['get', 'post', 'patch'], detail=False)
    # def settings_2auth(self, request, *args, **kwargs):

    #     if request.method == "GET":
    #         user_settings, created = Settings.objects.get_or_create(
    #             user=request.user)
    #         serializer = self.get_serializer(user_settings)
    #         return Response(serializer.data, status=status.HTTP_200_OK)

    #     elif request.method == "POST":
    #         if request.GET.get('choice') == 'phone':
    #             if request.user.phone_number:
    #                 user_settings, created = Settings.objects.get_or_create(
    #                     user=request.user)
    #                 user_settings.is_phone_number = True
    #                 user_settings.is_email = False
    #                 user_settings.save()
    #                 return Response({}, status=status.HTTP_200_OK)
    #             else:
    #                 return Response({'message': settings.ACCOUNT_CONSTANTS.messages.PHONE_NUMBER_NOT_REGISTERED}, status=status.HTTP_404_NOT_FOUND)

    #         elif request.GET.get('choice') == 'email':
    #             user_settings, created = Settings.objects.get_or_create(
    #                 user=request.user)
    #             user_settings.is_email = True
    #             user_settings.is_phone_number = False
    #             user_settings.save()
    #             return Response({}, status=status.HTTP_200_OK)
    #         else:
    #             return Response({'message': settings.ACCOUNT_CONSTANTS.messages.PARAMS_REQUIRED}, status=status.HTTP_400_BAD_REQUEST)
        
        # elif request.method == "PATCH":
        #     user_settings, created = Settings.objects.get_or_create(
        #         user=request.user)
        #     user_settings.is_phone_number = False
        #     user_settings.is_email = False
        #     user_settings.save()
        #     return Response({}, status=status.HTTP_200_OK)

    @action(['post'], detail=False)
    def send_otp_via_phone_number(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if settings.DEBUG:
            key = '1234'
            VerificationCode.objects.create(
                label=VerificationCode.RESET_PASSWORD, code=key, user=serializer.validated_data['phone'])
        else:
            key = random_with_N_digits(settings.VERIFICATION_CODE_LENGTH)
            instance = VerificationCode.objects.create(
                code=key, label=VerificationCode.RESET_PASSWORD, user=serializer.validated_data['phone'])
            body = settings.ACCOUNT_CONSTANTS.messages.SEND_OTP.format(
                instance.user.full_name, key)
            # verification_sms_signal.send(
            #     sender=self.__class__, phone_number=instance.user.phone_number, body=body, request=self.request
            # )
        return Response({
            'message': settings.ACCOUNT_CONSTANTS.messages.VERIFICATION_CODE_SENT}, status=status.HTTP_201_CREATED)

    @action(['post', 'put'], detail=False)
    def validate_phone_otp(self, request, *args, **kwargs):

        if request.method == 'POST':
            try:
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                q = serializer.validated_data['otp']
                if q.valid:
                    return Response({
                        'message': settings.ACCOUNT_CONSTANTS.messages.CODE_VALIDATED}, status=status.HTTP_201_CREATED)
                q.delete()
                return Response({
                    'message': settings.ACCOUNT_CONSTANTS.messages.CODE_EXPIRED}, status=status.HTTP_406_NOT_ACCEPTABLE)
            except:
                return Response({
                    'message': settings.ACCOUNT_CONSTANTS.messages.CODE_NOT_EXIST},
                    status=status.HTTP_404_NOT_FOUND)

        if request.method == 'PUT':
            try:
                q = VerificationCode.objects.get(code=request.data.get('otp'))
                q.user.set_password(request.data['password'])
                q.user.save()
                q.delete()
                return Response({'message': settings.ACCOUNT_CONSTANTS.messages.PASSWORD_UPDATE}, status=status.HTTP_200_OK)
            except VerificationCode.DoesNotExist:
                return Response({
                    'message': settings.ACCOUNT_CONSTANTS.messages.ACCOUNT_NOT_EXIST},
                    status=status.HTTP_404_NOT_FOUND)

    @action(['post'], detail=False)
    def user_account_activation(self, request):
        try:
            activation_code = VerificationCode.objects.get(
                code=request.data.get("code"))
            if activation_code.valid:
                user = activation_code.user
                user.is_active = True
                user.save()
                activation_code.delete()
                # welcome_new_user_task.delay(user.id)
                token = CustomTokenObtainPairSerializer.get_token(user)
                user_token = {"refresh": str(
                    token), "access": str(token.access_token)}
                return Response(user_token, status=status.HTTP_200_OK)
            else:
                return Response({"message": settings.ACCOUNT_CONSTANTS.messages.VERIFICATION_CODE_EXPIRED}, status=status.HTTP_403_FORBIDDEN)
        except VerificationCode.DoesNotExist:
            return Response({"message": settings.ACCOUNT_CONSTANTS.messages.CODE_NOT_EXIST}, status=status.HTTP_403_FORBIDDEN)

    @action(['PATCH'], detail=False)
    def edit_user_profile(self, request):
        serializer = self.get_serializer(
            request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(["post"], detail=False,url_path='deactivate-account')
    def deactivate_account(self, request):
        user = request.user
        user.has_deactivated = True
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    
