from django.db import models
from django.core.exceptions import ValidationError
from encrypted_model_fields.fields import EncryptedTextField


class Vendor(models.Model):
    name = models.CharField(max_length=100)
    code = models.SlugField(
        max_length=50,
        unique=True,
        help_text="A unique, URL-safe identifier for the vendor.",
    )
    secure_variables = EncryptedTextField(
        blank=True,
        null=True,
        help_text="Encrypted JSON object of secure variables (e.g., API keys).",
    )

    def __str__(self):
        return self.name


class Environment(models.Model):
    vendor = models.ForeignKey(
        Vendor, on_delete=models.CASCADE, related_name="environments"
    )
    name = models.CharField(max_length=100)
    code = models.SlugField(
        max_length=50,
        help_text="A unique code for the environment within this vendor (e.g., 'prod', 'dev').",
    )
    target_url = models.URLField(
        max_length=512, help_text="The full URL to forward requests to."
    )
    is_default = models.BooleanField(
        default=False,
        help_text="Is this the default environment for the vendor? Only one can be default.",
    )

    class Meta:
        unique_together = ("vendor", "code")

    def __str__(self):
        return f"{self.vendor.name} - {self.name}"

    def clean(self):
        if self.is_default:
            existing_defaults = Environment.objects.filter(
                vendor=self.vendor, is_default=True
            ).exclude(pk=self.pk)
            if existing_defaults.exists():
                raise ValidationError(
                    f"Vendor '{self.vendor.name}' already has a default environment."
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class RoutingRule(models.Model):
    environment = models.ForeignKey(
        Environment, on_delete=models.CASCADE, related_name="rules"
    )
    wa_id = models.CharField(
        max_length=20, help_text="The sender's WhatsApp ID (phone number)."
    )
    name = models.CharField(
        max_length=100, help_text="A descriptive name for this rule."
    )

    def __str__(self):
        return f"Rule for {self.wa_id} -> {self.environment}"

    def clean(self):
        vendor = self.environment.vendor
        vendor_environments = Environment.objects.filter(vendor=vendor)
        conflicting_rules = RoutingRule.objects.filter(
            environment__in=vendor_environments, wa_id=self.wa_id
        ).exclude(pk=self.pk)

        if conflicting_rules.exists():
            raise ValidationError(
                f"The WhatsApp ID '{self.wa_id}' is already assigned to an environment for vendor '{vendor.name}'."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
