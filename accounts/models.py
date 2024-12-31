from datetime import datetime, timezone
import uuid

from django.conf import settings
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin
from django.contrib.gis.db import models
from django.utils.translation import gettext as _
from django.core.validators import MaxLengthValidator,MinLengthValidator
from django.urls import reverse
from django.utils.html import format_html


class UserManager(BaseUserManager):
 
    def create_user(self, username, first_name,last_name, password=None, **extra_fields):
        """
        Creates and saves a User with the given email and password.
        """
    
        user = self.model(           
            username=username,
            first_name=first_name,
            last_name=last_name,
            **extra_fields,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(
        self, email, username, first_name,last_name, password=None, **extra_fields
    ):
        """
        Creates and saves a admin with the given email and password.
        """
        user = self.create_user(
            email=email,
            username=username,
            first_name=first_name,
            last_name=last_name,
            user_type=User.ADMIN,
            password=password,
            **extra_fields,
        )
        
        user.is_active = True
        user.is_staff = True
        user.admin = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):

    ADMIN="ADMIN"
    SHOPER="SHOPER"
    USER="USER"
    STAFF="STAFF"
  


    USER_TYPE_CHOICE = (
        (ADMIN,"Super User"),
        (STAFF,"STAFF User"),
        (SHOPER,"Shoper User"),
        (USER,"User"),
       
       
    )
    
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    username = models.CharField(_("username"), max_length=100, unique=True)
    first_name=models.CharField(_("first name"), max_length=100)
    last_name=models.CharField(_("last name"), max_length=100)
    email = models.EmailField(_("email address"), max_length=255, unique=True,blank=True,null=True)
    phone_number = models.CharField(
        _("phone number"), max_length=255,unique=True,validators=[
            MinLengthValidator(limit_value=13),
            MaxLengthValidator(limit_value=13)
        ]
    )
    profile_image = models.ImageField(
        upload_to="cooperative_logo",default="default_image/default.png")
    date_of_birth = models.DateField(blank=True, null=True)
    user_type = models.CharField(
        _("user type"), choices=USER_TYPE_CHOICE, max_length=50, default=USER
    )
    is_active = models.BooleanField(_("is active"), default=False)
    # admin user; non super-user
    is_staff = models.BooleanField(_("staff"), default=False)
    last_login = models.DateTimeField(_("last login on"), auto_now_add=False,null=True,blank=True)
    is_phone_visible = models.BooleanField(_("visible"), default=False)
    
    admin = models.BooleanField(_("admin"), default=False)  # a admin
    created_on = models.DateTimeField(_("created on"), auto_now_add=True)
    objects = UserManager()
    USERNAME_FIELD = _("username")
    REQUIRED_FIELDS = ["phone_number",]
    
    def get_full_name(self):
        # The user is identified by their address
        return self.first_name+' '+self.last_name


    def __str__(self):  # __unicode__ on Python 2O
        return self.last_name

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True


class JWTTokenBlacklist(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    token = models.CharField(max_length=500, unique=True)
    user = models.ForeignKey(
        User, related_name="black_listed_token", on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)
    refresh_tokens = models.CharField(max_length=500, unique=True)
    
    class Meta:
        verbose_name = _("JwtTokenBlacklist")
        verbose_name_plural = _("JwtTokenBlacklists")
    
    def __str__(self):
        return str(self.created_on)
    
    def get_absolute_url(self):
        return reverse("JwtTokenBlacklist_detail", kwargs={"pk": self.pk})



class Province(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    name=models.CharField(max_length=50)


    class Meta:
        verbose_name = _("Province")
        verbose_name_plural = _("Provinces")
        ordering = ('name',)

    def __str__(self):
            return self.name

    def get_absolute_url(self):
        return reverse("province_detail", kwargs={"pk": self.pk})


class District(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    name=models.CharField(max_length=50)
    province=models.ForeignKey(Province,on_delete=models.CASCADE,related_name='province')

    
    class Meta:
        verbose_name = _("District")
        verbose_name_plural = _("Districts")
        ordering = ('name',)

    def __str__(self):
            return self.name
    
    def get_absolute_url(self):
        return reverse("district_detail", kwargs={"pk": self.pk})



class Sector(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    name=models.CharField(max_length=50)
    district=models.ForeignKey(District,on_delete=models.CASCADE,related_name='district')


    class Meta:
        verbose_name = _("Sector")
        verbose_name_plural = _("Sectors")
        ordering = ('name',)

    def __str__(self):
            return self.name

    def get_absolute_url(self):
        return reverse("sector_detail", kwargs={"pk": self.pk})


class Village(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    name=models.CharField(max_length=50)
    sector=models.ForeignKey(Sector,on_delete=models.CASCADE,related_name='sector')


    class Meta:
        verbose_name = _("Village")
        verbose_name_plural = _("Villages")
        ordering = ('name',)

    def __str__(self):
            return self.name

    def get_absolute_url(self):
        return reverse("village_detail", kwargs={"pk": self.pk})



class UserAddress(models.Model):
    user=models.OneToOneField(User,related_name='user_location',on_delete=models.CASCADE)
    village=models.ForeignKey(Village,on_delete=models.SET_NULL,related_name='user_village', blank=True, null=True)
    lng = models.FloatField(blank=True, null=True)
    lat = models.FloatField(blank=True, null=True)
    location = models.PointField(srid=4326, blank=True, null=True)
    
    class Meta:
        verbose_name = _("User Address")
        verbose_name_plural = _("User addresses")
        ordering = ('user',)


    def get_absolute_url(self):
        return reverse("user_address_detail", kwargs={"pk": self.pk})




class VerificationCode(models.Model):
    SIGNUP = 'SIGNUP'
    RESET_PASSWORD = 'RESET_PASSWORD'
    CHANGE_EMAIL = 'CHANGE_EMAIL'
    VERIFICATION_CODE_CHOICES = (
        (SIGNUP, 'Signup'),
        (RESET_PASSWORD, 'Reset password'),
        (CHANGE_EMAIL, 'Change email'),
    )
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True, null=True)
    code = models.CharField(
        max_length=6, blank=True, null=True)
    status = models.BooleanField(default=False)
    label = models.CharField(
        max_length=255, choices=VERIFICATION_CODE_CHOICES, default=CHANGE_EMAIL)
    email = models.EmailField(max_length=255, blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('code', 'user')
    
    
    @property
    def valid(self):
        future_time = self.created_on + settings.VERIFICATION_CODE_LIFETIME
        return datetime.now(timezone.utc) < future_time
    
    def get_absolute_url(self):
        return reverse("favorite_detail", kwargs={"pk": self.pk})
