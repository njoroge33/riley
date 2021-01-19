import datetime
from django.core import serializers
from django.shortcuts import render
from .serializers import RiderSerializer, RequestSerializer, BranchSerializer
from .models import Rider, Otp, Request, BlackList, RiderLocation, Client, Branch
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.decorators import api_view
from django.http import HttpResponse, JsonResponse
# from rest_framework_simplejwt.tokens import RefreshToken
from .otp import generate_random_otp, get_otp_phone_number, is_otp_expired
from .code_location import code_location, get_distance
import requests as req
import jwt
from geopy.geocoders import Nominatim
import json
# from deliver.settings import SECRET_KEY

# key = SECRET_KEY


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
        # print(request.headers)
        data = request.data
        phone = data.get('phone')
        imei = data.get('imei')

        try:
            rider = Rider.objects.get(phone_number=phone)
        except Exception as e:
            return JsonResponse({'status':False, 'message':'Invalid phone number'})
            # if the rider exists generate and send the otp
        if rider and imei:
            otp_number = generate_random_otp(6)
            message = f'<#> Riley: Your verification code is {otp_number}'

            # send request to send otp via sms
            payload = {'username': OTP_USERNAME, 'password': OTP_PASSWORD, 'shortcode': OTP_SHORTCODE, \
                    'mobile': get_otp_phone_number(phone), 'message': message}
            response = req.get(OTP_URL, params=payload, verify=False)

            if response.status_code == 200:
                # riders=Rider(phone_number=phone, id=rider.id)
                token = rider.encode_auth_token(rider.id, request)
                new_otp = Otp(phone_number=phone, otp=otp_number, imei=imei)
                new_otp.save()
                return JsonResponse({'status':True, 'message':'otp sucessfully created', 'otp_token': token.decode()})
            return JsonResponse({'status':False, 'message':'some error occurred.Please try again'})
        return JsonResponse({'status':False, 'message':'No imei'})
    return Response('bad request', status=status.HTTP_400_BAD_REQUEST)

# this recieves phone no., otp_token and otp
@api_view(['POST'])
def verify_otp(request):
    if request.method == "POST":
        data = request.data
        phone = data.get('phone')
        otp_number = data.get('otp')
        otp_token = request.headers.get('Authorization')
    
        try:
            otp = Otp.objects.get(phone_number=phone, otp=otp_number)
            rider = Rider.objects.get(phone_number=phone)
        except Exception as e:
            return JsonResponse({'status':False, 'message':'Wrong phone number or wrong otp was provided'})

        if otp and rider:
            token = jwt.decode(otp_token, None, None)
            # print(token['sub'])
            if token['sub'] == rider.id:
                if not is_otp_expired(otp):
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
            return JsonResponse({'status':False, 'message':'Wrong token was provided'})
        # return JsonResponse({'status':False, 'message':'No otp or wrong phone number was provided'})     
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
            if rider.active:
                # riders=Rider(phone_number=phone, id=rider.id)
                token = rider.encode_auth_token(rider.id, request)
                return JsonResponse({'status':True, 'message':'logged in sucessfully', 'session_token': token.decode()})
            return JsonResponse({'status':False, 'message':'Sorry, Your account is deactivated.Please, contact the support team'})
        return JsonResponse({'status':False, 'message':'Wrong pin was provided'})
    return Response('bad request', status=status.HTTP_400_BAD_REQUEST)

# this recieves old_pin, new_pin & session_token
@api_view(['POST'])
def change_pin(request):
    data = request.data
    # token = data.get('session_token')
    old_pin = data.get('old_pin')
    new_pin = data.get('new_pin')
    session_token = request.headers.get('Authorization')

    if len(str(new_pin))== 4:
        defaults={"pin":int(new_pin)}
    else:
        return JsonResponse({'status':False, 'message':'your pin must be 4 digits in length'})

    blacklisted = BlackList.objects.filter(token=session_token)

    if session_token and not blacklisted:
        decoded_token = jwt.decode(session_token, None, None)
        rider_id = decoded_token['sub']
        # print(rider_id)
        try:
            obj = Rider.objects.get(id=rider_id)
            # print(type(obj.pin))
            if obj.pin == int(old_pin):
                for key, value in defaults.items():
                    setattr(obj, key, value)
                obj.save()
                return JsonResponse({'status':True, 'message':'pin sucessfully changed'})
            return JsonResponse({'status':False, 'message':'please, input the correct current pin'})
        except Exception as e:
            return JsonResponse({'status':False, 'message':'Invalid token was provided'})
    return JsonResponse({'status':False, 'message':"Unsucessful, No token was provided or token is blaklisted"})

# receives the session_token
@api_view(['POST'])
def logout(request):
    session_token = request.headers.get('Authorization')
    # blacklist the token to log out the user
    if session_token:
        blacklist = BlackList(token=session_token)
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

# receives a session_token
@api_view(['POST'])
def get_requests(request):
    token = request.headers.get('Authorization')
    blacklisted = BlackList.objects.filter(token=token)
    
    if token and not blacklisted:
        decoded_token = jwt.decode(token, None, None)
        rider_id = decoded_token['user_id']

        result = Request.objects.filter(rider=rider_id)
        serializer = RequestSerializer(result, many=True)
        data = serializer.data
        return JsonResponse({'status':True, 'message':'OK', 'requests': data})
    return JsonResponse({'status':False, 'message':"No token was provided or token is blaklisted"})

# receives a session_token & request_id & status(accept, picked-up, complete, cancel)
@api_view(['POST'])
def update_status(request):
    data = request.data
    token = request.headers.get('Authorization')
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
        elif status == 'picked':
            # create the initial instance location of the rider at the pickup point to beinging tracking
            keys = ['lat', 'long']
            loc = str({x:request.pickup_location[x] for x in keys}).replace(',', '>')
            print(loc)
            new_location_instance = RiderLocation(request=request, rider=request.rider, current_location=[loc])
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

# receives a session_token, request_id & location(json)
@api_view(['POST'])
def update_rider_location(request):
    data = request.data
    token = request.headers.get('Authorization')
    request_id = data.get('id')
    location = data.get('location')

    current_location=str(location).replace(',', '>')
    blacklisted = BlackList.objects.filter(token=token)

    if token and not blacklisted:
        decoded_token = jwt.decode(token, None, None)
        rider_id = decoded_token['user_id']

        try:
            obj = RiderLocation.objects.get(request=request_id, rider=rider_id)
            # for key, value in defaults.items():
            #     setattr(obj, key, value)
            obj.current_location.append(current_location)
            obj.save()
            return JsonResponse({'status':True, 'message':'OK'})
        except Exception as e:
            return JsonResponse({'status':False, 'message':"The request doesn't exists"})
    return JsonResponse({'status':False, 'message':"No token was provided or token is blaklisted"})

# receives a session_token & request_id
@api_view(['POST'])
def get_current_location(request):
    data = request.data
    token = request.headers.get('Authorization')
    request_id = data.get('id')

    blacklisted = BlackList.objects.filter(token=token)

    if token and not blacklisted:
        decoded_token = jwt.decode(token, None, None)
        rider_id = decoded_token['user_id']

        try:
            rider_location = RiderLocation.objects.get(request=request_id, rider=rider_id)
            # for key, value in defaults.items():
            #     setattr(obj, key, value)
            rider=rider_location.current_location[-1].replace('>', ',')
            print(rider)
            # obj.save()
            return JsonResponse({'status':True, 'message':'OK', 'rider':rider})
        except Exception as e:
            return JsonResponse({'status':False, 'message':"The request doesn't exists"})
    return JsonResponse({'status':False, 'message':"No token was provided or token is blaklisted"})

# receives a session_token
@api_view(['POST'])
def get_rides(request):
    token = request.headers.get('Authorization')
    blacklisted = BlackList.objects.filter(token=token)
    
    if token and not blacklisted:
        decoded_token = jwt.decode(token, None, None)
        rider_id = decoded_token['user_id']

        results = Request.objects.filter(rider=rider_id, status="Completed")
        rides = []

        for result in results:
            ride = { 'destination': result.delivery_location,'pickup' :result.pickup_location,
            'distance' : get_distance(result.pickup_location, result.delivery_location)}

            rides.append(ride)

        return JsonResponse({'status':True, 'message':'OK', 'rides': rides})
    return JsonResponse({'status':False, 'message':"No token was provided or token is blaklisted"})

@api_view(['POST'])
def create_client(request):
    data = request.data
    name = data.get('name')
    new_client = Client(name=name)
    new_client.save()
    return JsonResponse({'status':True, 'message':'OK'})

class BranchList(viewsets.ModelViewSet):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer

    def perform_create(self, serializer):
        loc = code_location(self.request.data.get('location'))
        serializer.save(location=loc)
