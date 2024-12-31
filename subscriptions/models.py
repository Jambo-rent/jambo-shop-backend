import uuid
from datetime import datetime,timedelta,timezone
from django.contrib.gis.db import models
from django.utils.translation import gettext as _
from django.conf import settings
from django.urls import reverse

from accounts.models import (User)



class MonthlySub(models.Model):
    P='PREMIUM'
    B='BASIC'
    F='FREE'
    TYPE = (
        (P, 2000.0),
        (B, 1000.0),
        (F, 0.0),
       
    )
    
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='user_sub')
    type_sub=models.FloatField(
       choices=TYPE, default=F)
    is_expired = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    
    
    @property
    def is_valid(self):
        # Calculate expiry date
        expiry_date = self.created_on + timedelta(days=settings.MONTHLY_DAY)
        # Check if subscription is active
        if datetime.now(timezone.utc) > expiry_date:
            return False
        else:
            return False

    class Meta:
        verbose_name = _("Order Item")
        verbose_name_plural = _("Order Items")
        ordering = ('created_on',)
    
    def __str__(self):
            return self.user.first_name
    
    def get_absolute_url(self):
        return reverse("monthly_sub_detail", kwargs={"pk": self.pk})