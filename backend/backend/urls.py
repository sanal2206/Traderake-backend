from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),             # Admin panel
    path('accounts/', include('accounts.urls')), # URLs from accounts app
    path('core/', include('core.urls')),         # URLs from core app
]

