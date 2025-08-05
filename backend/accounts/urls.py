from django.urls import path
from .views import RegisterAPIView,CustomTokenObtainPairView,LogoutAPIView
from rest_framework_simplejwt.views import (
    
    TokenRefreshView,
)

 

urlpatterns = [
    path('api/register/', RegisterAPIView.as_view()),
    path('api/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/logout/', LogoutAPIView.as_view(), name='logout'),
]
