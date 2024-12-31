from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save, pre_delete

from shops.models import Stock
from utils.geo_location import point


@receiver(pre_save, sender=Stock)
def update_location(sender, instance, *args, **kwargs):
    instance.location =point(instance.lng, instance.lat)