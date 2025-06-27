from django.contrib import admin
from .models import Vendor, Environment, RoutingRule


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ("name", "code")
    search_fields = ("name", "code")


@admin.register(Environment)
class EnvironmentAdmin(admin.ModelAdmin):
    list_display = ("name", "vendor", "code", "target_url", "is_default")
    list_filter = ("vendor", "is_default")
    search_fields = ("name", "vendor__name", "code")


@admin.register(RoutingRule)
class RoutingRuleAdmin(admin.ModelAdmin):
    list_display = ("name", "wa_id", "environment")
    list_filter = ("environment__vendor", "environment")
    search_fields = ("name", "wa_id", "environment__name")
