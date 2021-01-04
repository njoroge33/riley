import datetime
from django.core import serializers
from django.shortcuts import render
from .serializers import RiderSerializer, RequestSerializer
from .models import Rider, Otp, Request, BlackList, RiderLocation
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.decorators import api_view
from django.http import HttpResponse, JsonResponse
from rest_framework_simplejwt.tokens import RefreshToken
from .otp import generate_random_otp, get_otp_phone_number, is_otp_expired
from .code_location import code_location
import requests as req
import jwt
from geopy.geocoders import Nominatim

OTP_URL = 'https://pyris.socialcom.co.ke/api/PushSMS.php?'
OTP_USERNAME = 'sub_api_user'
OTP_PASSWORD = '73wjzRNPAzgT8EZ1JQv8hpD2BsQ9'
OTP_SHORTCODE = 'SOCIALCOM'

class RiderList(viewsets.ModelViewSet):
    queryset = Rider.objects.all()
    serializer_class = RiderSerializer

    def perform_create(self, serializer):
        serializer.save(pin=generate_random_otp(4))

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
            # if the rider exists generate and send the otp
        if rider:
            otp_number = generate_random_otp(6)
            message = f'<#> Riley: Your verification code is {otp_number}'

            # send request to send otp via sms
            payload = {'username': OTP_USERNAME, 'password': OTP_PASSWORD, 'shortcode': OTP_SHORTCODE, \
                    'mobile': get_otp_phone_number(phone), 'message': message}
            response = req.get(OTP_URL, params=payload, verify=False)

            if response.status_code == 200:
                new_otp = Otp(phone_number=phone, otp=otp_number, imei=imei)
                new_otp.save()
                return JsonResponse({'status':True, 'message':'otp sucessfully created'})
            return JsonResponse({'status':False, 'message':'some error occurred.Please try again'})
    return Response('bad request', status=status.HTTP_400_BAD_REQUEST)

# this recieves phone no., token and otp
@api_view(['POST'])
def verify_otp(request):
    if request.method == "POST":
        data = request.data
        phone = data.get('phone')
        otp_number = data.get('otp')
    
        try:
            otp = Otp.objects.get(phone_number=phone, otp=otp_number)
            rider = Rider.objects.get(phone_number=phone)
        except Exception as e:
            return JsonResponse({'status':False, 'message':'No otp for the number or wrong otp'})

        if otp and rider and not is_otp_expired(otp):
                # After verifying the otp send the pin to the ider to enable them to login
                pin = rider.pin
                message = f'<#> Riley: Your pin is {pin}'

                # send request to send pin via sms
                payload = {'username': OTP_USERNAME, 'password': OTP_PASSWORD, 'shortcode': OTP_SHORTCODE, \
                    'mobile': get_otp_phone_number(phone), 'message': message}
                response = req.get(OTP_URL, params=payload, verify=False)

                if response.status_code == 200:
                    rider.active = 'True'
                    rider.save()
                    return JsonResponse({'status':True, 'message':'OK'})
                return JsonResponse({'status':False, 'message':'The otp has expired'})       
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
        if rider.pin == int(pin):
            riders=Rider(phone_number=phone, id=rider.id)
            token = RefreshToken.for_user(riders)
            return JsonResponse({'status':True, 'message':'logged in sucessfully', 'token': str(token)})
        return JsonResponse({'status':False, 'message':'Wrong pin was provided'})
    return Response('bad request', status=status.HTTP_400_BAD_REQUEST)

# this recieves old_pin, new_pin & token
@api_view(['POST'])
def change_pin(request):
    data = request.data
    token = data.get('token')
    old_pin = data.get('old_pin')
    new_pin = data.get('new_pin')

    if len(str(new_pin))== 4:
        defaults={"pin":int(new_pin)}
    else:
        return JsonResponse({'status':False, 'message':'your pin must be 4 digits in length'})

    blacklisted = BlackList.objects.filter(token=token)

    if token and not blacklisted:
        decoded_token = jwt.decode(token, None, None)
        rider_id = decoded_token['user_id']
        print(rider_id)
        try:
            obj = Rider.objects.get(id=rider_id)
            print(type(obj.pin))
            if obj.pin == int(old_pin):
                for key, value in defaults.items():
                    setattr(obj, key, value)
                obj.save()
                return JsonResponse({'status':True, 'message':'pin sucessfully changed'})
            return JsonResponse({'status':False, 'message':'please, input the correct current pin'})
        except Exception as e:
            return JsonResponse({'status':False, 'message':'Invalid token was provided'})
    return JsonResponse({'status':False, 'message':"Unsucessful, No token was provided or token is blaklisted"})

# receives the token
@api_view(['POST'])
def logout(request):
    token = request.data.get('token')

    # blacklist the token to log out the user
    if token:
        blacklist = BlackList(token=token)
        blacklist.save()
        return JsonResponse({'status':True, 'message':"Logged out sucessfully"})
    return JsonResponse({'status':False, 'message':"Command unsucessful, Wrong token was provided"})


class RequestList(viewsets.ModelViewSet):
    queryset = Request.objects.all()
    serializer_class = RequestSerializer

    def perform_create(self, serializer):
        pick = code_location(self.request.data.get('pickup_location'))
        deliver = code_location(self.request.data.get('delivery_location'))

        if self.request.data.get('rider') == '':
            serializer.save(status='Pending assignment', pickup_location=pick, delivery_location=deliver)         
        else:
            serializer.save(status='Assigned', pickup_location=pick, delivery_location=deliver)

# receives a token
@api_view(['POST'])
def get_requests(request):
    token = request.data.get('token')
    blacklisted = BlackList.objects.filter(token=token)
    
    if token and not blacklisted:
        decoded_token = jwt.decode(token, None, None)
        rider_id = decoded_token['user_id']

        result = Request.objects.filter(rider=rider_id)
        serializer = RequestSerializer(result, many=True)
        data = serializer.data
        return JsonResponse({'status':True, 'message':'OK', 'requests': data})
    return JsonResponse({'status':False, 'message':"No token was provided or token is blaklisted"})

# receives a token & request_id & status(accept, picked-up, complete, cancel)
@api_view(['POST'])
def update_status(request):
    data = request.data
    token = data.get('token')
    request_id = data.get('id')
    status = data.get('status')
    blacklisted = BlackList.objects.filter(token=token)

    if token and not blacklisted:
        try:
            request = Request.objects.get(id=request_id)
        except Exception as e:
            return JsonResponse({'status':False, 'message':'No request by this id'})
        if status == 'accept':
            serializer = RequestSerializer(request, data={'status': 'Accepted'}, partial=True)
            if serializer.is_valid():
                serializer.save()
        elif status == 'picked_up':
            # create the initial instance location of the rider at the pickup point to beinging tracking
            new_location_instance = RiderLocation(request=request, rider=request.rider, current_location=request.pickup_location)
            new_location_instance.save()
            serializer = RequestSerializer(request, data={'status': 'Enroute'}, partial=True)
            if serializer.is_valid():
                serializer.save()
        elif status == 'complete':
            serializer = RequestSerializer(request, data={'status': 'Completed'}, partial=True)
            if serializer.is_valid():
                serializer.save()
        elif status == 'cancel':
            serializer = RequestSerializer(request, data={'status': 'Cancelled'}, partial=True)
            if serializer.is_valid():
                serializer.save()
        else:
            return JsonResponse({'status':False, 'message':'Please, select a valid status and try again'})
        return JsonResponse({'status':True, 'message':'OK'})
    return JsonResponse({'status':False, 'message':"No token was provided or token is blaklisted"})

# receives a token, request_id & location(json)
@api_view(['POST'])
def update_rider_location(request):
    data = request.data
    token = data.get('token')
    request_id = data.get('id')
    location = data.get('location')

    defaults={"current_location":location}
    blacklisted = BlackList.objects.filter(token=token)

    if token and not blacklisted:
        decoded_token = jwt.decode(token, None, None)
        rider_id = decoded_token['user_id']

        try:
            obj = RiderLocation.objects.get(request=request_id, rider=rider_id)
            for key, value in defaults.items():
                setattr(obj, key, value)
            obj.save()
            return JsonResponse({'status':True, 'message':'OK'})
        except Exception as e:
            return JsonResponse({'status':False, 'message':"The request doesn't exists"})
    return JsonResponse({'status':False, 'message':"No token was provided or token is blaklisted"})

