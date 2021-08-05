from django.urls import path, re_path, include
from .views import RiderList, RequestList, BranchList
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r'api/riders', RiderList)
router.register(r'api/requests', RequestList)
router.register(r'api/branches', BranchList)

urlpatterns = [
    re_path(r'^', include(router.urls)),
    path('api/auth/otp/get', views.get_otp, name='otp'),
    path('api/auth/otp/verify', views.verify_otp, name='verify'),
    path('api/auth/pin/update', views.change_pin, name='change_pin'),
    path('api/auth/login', views.login, name='login'),
    path('api/auth/logout', views.logout, name='logout'),
    path('api/requests/get', views.get_requests, name='requests'),
    path('api/requests/status', views.update_status, name='status'),
    path('api/location/update', views.update_rider_location, name='location_update'),
    path('api/location/get', views.get_current_location, name='current_location'),
    path('api/rides/get', views.get_rides, name='rides'),
    path('api/rider/info', views.get_rider_info, name='info'),
    path('api/newclient', views.create_client, name='client')
]
