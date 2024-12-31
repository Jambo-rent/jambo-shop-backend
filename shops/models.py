import uuid
from datetime import datetime, timezone

from django.contrib.gis.db import models
from django.conf import settings
from django.utils.html import format_html
from django.utils.translation import gettext as _
from django.urls import reverse
from django.core.validators import MaxLengthValidator,MinLengthValidator


from accounts.models import (User, Village)

# Create your models here.

class Stock(models.Model):
    SMALL = 'SMALL'
    MEDIUM = 'MEDIUM'
    LARGE = 'LARGE'
    STOCK_TYPE = (
        (SMALL, 'Signup'),
        (MEDIUM, 'Medium cap'),
        (LARGE, 'Large cap'),
    )

    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    stock_name=models.CharField(_("stock name"), max_length=100)
    owner = models.ForeignKey(
        User,related_name='shop_owner', on_delete=models.SET_NULL, blank=True, null=True)
    village=models.ForeignKey(Village,on_delete=models.SET_NULL,related_name='stock_village', blank=True, null=True)
    lng = models.FloatField()
    lat = models.FloatField()
    location = models.PointField(srid=4326, blank=True, null=True)
    is_close = models.BooleanField(_("close"), default=False)
    type = models.CharField(
        max_length=255, choices=STOCK_TYPE, default=MEDIUM)
    phone_number = models.CharField(
        _("phone number"), max_length=255,unique=True,validators=[
            MinLengthValidator(limit_value=13),
            MaxLengthValidator(limit_value=13)
        ]
    )
    created_on = models.DateTimeField(auto_now_add=True)
    
 
    
    class Meta:
        verbose_name = _("Stock")
        verbose_name_plural = _("Stockes")
        ordering = ('stock_name',)

    def __str__(self):
            return self.stock_name
    
    def get_absolute_url(self):
        return reverse("stock_detail", kwargs={"pk": self.pk})

class Product(models.Model):
    KG='KG'
    G='G'
    L='L'
    STOCK_TYPE = (
        (KG, 'Kilogram'),
        (G, 'Grams'),
        (L, 'Little'),
       
    )
    
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    name=models.CharField(max_length=100)
    quantity=models.IntegerField()
    stock=models.ForeignKey(Stock,on_delete=models.CASCADE,related_name='stock')
    is_available = models.BooleanField(default=True)
    price=models.FloatField()
    description=models.TextField()
    measure=models.CharField(
        max_length=10, choices=STOCK_TYPE, default=G)
    created_on = models.DateTimeField(auto_now_add=True)
    
    
    
    class Meta:
        verbose_name = _("Product")
        verbose_name_plural = _("Productes")
        ordering = ('name',)
    
    def __str__(self):
            return self.name
    
    def get_absolute_url(self):
        return reverse("product_detail", kwargs={"pk": self.pk})



class OrderItem(models.Model):
    KG='KG'
    G='G'
    L='L'
    TYPE = (
        (KG, 'Kilogram'),
        (G, 'Grams'),
        (L, 'Little'),
       
    )
    
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    quantity=models.IntegerField()
    product=models.ForeignKey(Product,on_delete=models.CASCADE,related_name='product')
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='user_ordered')
    measure=models.CharField(
        max_length=10, choices=TYPE, default=G)
    is_closed = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _("Order Item")
        verbose_name_plural = _("Order Items")
        ordering = ('created_on',)
    
    def __str__(self):
            return self.product.name
    
    def get_absolute_url(self):
        return reverse("orderitem_detail", kwargs={"pk": self.pk})
  

class Rating(models.Model):
    EXCELENT='EXCELENT'
    GOOD='GOOD'
    LOW='LOW'
    TYPE = (
        (EXCELENT, 15),
        (GOOD, 7.5),
        (LOW, 0),
       
    )
    
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    stock=models.ForeignKey(Stock,on_delete=models.CASCADE,related_name='stock_rate')
    order=models.ForeignKey(OrderItem,on_delete=models.CASCADE,related_name='order_rate')
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='user_rate')
    rate=models.FloatField(
        choices=TYPE, default=GOOD)
    is_valid = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    
    
    
    class Meta:
        verbose_name = _("rate")
        verbose_name_plural = _("rates")
        ordering = ('created_on',)
    
    def __str__(self):
            return self.stock.stock_name
    
    def get_absolute_url(self):
        return reverse("rate_detail", kwargs={"pk": self.pk})