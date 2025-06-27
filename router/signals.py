from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import RoutingRule

@receiver(pre_delete, sender=RoutingRule)
def invalidate_rule_cache(sender, instance, **kwargs):
    vendor_code = instance.environment.vendor.code
    wa_id = instance.wa_id
    cache_key = f"rule:{vendor_code}:{wa_id}"
    cache.delete(cache_key)