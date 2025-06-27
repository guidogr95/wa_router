from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('router.urls')),
    path('health/', lambda request: HttpResponse("Health check OK"), name='health_check'),
]