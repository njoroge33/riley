  
import datetime
from django.core import serializers
from django.shortcuts import render
from .serializers import RiderSerializer
from .models import Rider, Otp
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.decorators import api_view
from django.http import HttpResponse, JsonResponse
from rest_framework_simplejwt.tokens import RefreshToken
from .otp import generate_random_otp, get_otp_phone_number, is_otp_expired
import requests as req
import jwt

OTP_URL = 'https://pyris.socialcom.co.ke/api/PushSMS.php?'
OTP_USERNAME = 'sub_api_user'
OTP_PASSWORD = '73wjzRNPAzgT8EZ1JQv8hpD2BsQ9'
OTP_SHORTCODE = 'SOCIALCOM'

class RiderList(viewsets.ModelViewSet):
    queryset = Rider.objects.all()
    serializer_class = RiderSerializer
    
    def post(self,request):
        serializer = RiderSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

# this recieves phone no. and imei
@api_view(['POST'])
def get_otp(request):
    if request.method == "POST":
        data = request.data
        phone = data.get('phone')
        imei = data.get('imei')

        try:
            rider = Rider.objects.get(phone_number=phone)
        except Exception as e:
            return JsonResponse({'status':False, 'message':'Invalid phone number'})
        if rider:
            otp_number = generate_random_otp(6)
            message = f'<#> Riley: Your verification code is {otp_number}'

            # send request to send otp via sms
            payload = {'username': OTP_USERNAME, 'password': OTP_PASSWORD, 'shortcode': OTP_SHORTCODE, \
                    'mobile': get_otp_phone_number(phone), 'message': message}
            response = req.get(OTP_URL, params=payload, verify=False)

            if response.status_code == 200:
                riders=Rider(phone_number=phone, id=rider.id)
                token = RefreshToken.for_user(riders)
                new_otp = Otp(phone_number=phone, otp=otp_number, imei=imei)
                new_otp.save()
                return JsonResponse({'status':True, 'message':'otp sucessfully created', 'token': str(token)})
            return JsonResponse({'status':False, 'message':'some error occurred.Please try again'})
    return Response('bad request', status=status.HTTP_400_BAD_REQUEST)

# this recieves phone no., token and otp
@api_view(['POST'])
def verify_otp(request):
    if request.method == "POST":
        data = request.data
        phone = data.get('phone')
        otp_number = data.get('otp')
        token = data.get('token')
    
        try:
            otp = Otp.objects.get(phone_number=phone, otp=otp_number)
            rider = Rider.objects.get(phone_number=phone)
        except Exception as e:
            return JsonResponse({'status':False, 'message':'No otp for the number or wrong otp'})
        if otp and rider:
            token = jwt.decode(token, None, None)
            if token['user_id'] == rider.id:
                if not is_otp_expired(otp):
                    rider.active = True
                    rider.save()
                    return JsonResponse({'status':True, 'message':'OK'})
                return JsonResponse({'status':False, 'message':'The otp has expired'})
            return JsonResponse({'status':False, 'message':'Wrong token was provided'})
    return Response('bad request', status=status.HTTP_400_BAD_REQUEST)
    
# this recieves phone no.& pin 
@api_view(['POST'])
def login(request):
    if request.method == "POST":
        data = request.data
        phone = data.get('phone')
        pin = data.get('pin')
        try:
            rider = Rider.objects.get(phone_number=phone)
        except Exception as e:
            return JsonResponse({'status':False, 'message':'Wrong phone number was provided'})
        if rider.pin == pin:
            return JsonResponse({'status':True, 'message':'logged in  sucessfully'})
        return JsonResponse({'status':False, 'message':'Wrong phone number was provided'})
    return Response('bad request', status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def logout(request):
    return JsonResponse({'status':True, 'message':"Logged out sucessfully"})
