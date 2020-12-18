from django.urls import path, re_path, include
from .views import RiderList
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r'api/riders', RiderList)

urlpatterns = [
    re_path(r'^', include(router.urls)),
    path('api/auth/otp/request', views.get_otp, name='otp'),
    path('api/auth/otp/verify', views.verify_otp, name='verify'),
    path('api/auth/login', views.login, name='login'),
    path('api/auth/logout', views.logout, name='logout')
]
