# wa_router/router/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path(
        "webhook/meta/<slug:vendor_code>/",
        views.meta_webhook_receiver,
        name="meta_webhook",
    ),
]
