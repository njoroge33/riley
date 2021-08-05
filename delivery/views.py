import datetime
from django.core import serializers
from django.shortcuts import render
from .serializers import RiderSerializer, RequestSerializer, BranchSerializer
from .models import Rider, Otp, Request, BlackList, RiderLocation, Client, Branch, RequestLocation
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.decorators import api_view
from django.http import HttpResponse, JsonResponse
from .otp import generate_random_otp, get_otp_phone_number, is_otp_expired
from .code_location import code_location, get_distance, get_duration, get_client_ip
import requests as req
import jwt
from geopy.geocoders import Nominatim
import json
import logging

logger = logging.getLogger('django')


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
        ip = get_client_ip(request)

        try:
            rider = Rider.objects.get(phone_number=phone)
        except Exception as e:

            response_object = {'status':False, 'message':'Invalid phone number'}
            logger.critical(f'[{ip}] - Invalid phone number - Payload: {data} -Response: {response_object}')
            return JsonResponse(response_object)
            # if the rider exists generate and send the otp
        if rider and imei:
            if not rider.active:
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

                response_object = {'status':False, 'message':'some error occurred.Please try again'}
                logger.critical(f'[{ip}] - Udefined error - Payload: {data} -Response: {response_object}')
                return JsonResponse(response_object)

            return JsonResponse({'status':True, 'message':'Verified'})
        
        response_object = {'status':False, 'message':'No imei'}
        logger.critical(f'[{ip}] - Imei not provided - Payload: {data} -Response: {response_object}')
        return JsonResponse(response_object)
    return Response('bad request', status=status.HTTP_400_BAD_REQUEST)

# this recieves phone no., otp_token and otp
@api_view(['POST'])
def verify_otp(request):
    if request.method == "POST":
        data = request.data
        phone = data.get('phone')
        otp_number = data.get('otp')
        token = request.headers.get('Authorization')
        ip = get_client_ip(request)

        if token:
            otp_token = token.split(" ")[1]
        else:
            otp_token = ' '
        if otp_token:
            resp = Rider.decode_auth_token(otp_token, request)

            if isinstance(resp, int):
                try:
                    otp = Otp.objects.get(phone_number=phone, otp=otp_number)
                    rider = Rider.objects.get(phone_number=phone)
                except Exception as e:
                    
                    response_object = {'status':False, 'message':'Wrong phone number or wrong otp was provided'}
                    logger.critical(f'[{ip}] - Wrong phone number or otp - Payload: {data} -Response: {response_object}')
                    return JsonResponse(response_object)
                    # rider_id = resp
                if resp == rider.id:
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

                    response_object = {'status':False, 'message':'The otp has expired'}
                    logger.critical(f'[{ip}] - Expired otp - Payload: {data} -Response: {response_object}')
                    return JsonResponse(response_object)

                response_object = {'status':False, 'message':'Wrong token was provided'}
                logger.critical(f'[{ip}] - Wrong token - Payload: {data} -Response: {response_object}')
                return JsonResponse(response_object) 

            response_object = {'status':False, 'message': resp.split('.')[0]}
            logger.critical(f'[{ip}] - Invalid otp token - Payload: {data} - Token: {otp_token} - Response: {response_object}')
            return JsonResponse(response_object)

        response_object = {'status':False, 'message':'Provide a valid otp token.'}
        logger.critical(f'[{ip}] - Wrong token - Payload: {data} - Token: {otp_token} - Response: {response_object}')
        return JsonResponse(response_object) 

    
# this recieves phone no.& pin 
@api_view(['POST'])
def login(request):
    if request.method == "POST":
        data = request.data
        phone = data.get('phone')
        pin = data.get('pin')
        ip = get_client_ip(request)
        try:
            rider = Rider.objects.get(phone_number=phone)
        except Exception as e:
            
            response_object = {'status':False, 'message':'Wrong phone number was provided'}
            logger.critical(f'[{ip}] -Login authentication failure - Payload: {data} -Response: {response_object}')
            return JsonResponse(response_object)
        if rider.pin == int(pin):
            if rider.active:
                # riders=Rider(phone_number=phone, id=rider.id)
                token = rider.encode_auth_token(rider.id, request)
                return JsonResponse({'status':True, 'message':'logged in sucessfully', 'session_token': token.decode()})

            response_object = {'status':False, 'message':'Sorry, Your account is deactivated.Please, contact the support team'}
            logger.critical(f'[{ip}] - Account deactivated - Payload: {data} -Response: {response_object}')
            return JsonResponse(response_object)

        response_object ={'status':False, 'message':'Wrong pin was provided'}
        logger.critical(f'[{ip}] - Login authentication failure - Payload: {data} -Response: {response_object}')

        return JsonResponse(response_object)
        
    return Response('bad request', status=status.HTTP_400_BAD_REQUEST)

# this recieves old_pin, new_pin & session_token
@api_view(['POST'])
def change_pin(request):
    data = request.data
    # token = data.get('session_token')
    old_pin = data.get('old_pin')
    new_pin = data.get('new_pin')
    token = request.headers.get('Authorization')
    ip = get_client_ip(request)

    if token:
        session_token = token.split(" ")[1]
    else:
        session_token = ''
    
    if len(str(new_pin))== 4:
        defaults={"pin":int(new_pin)}
    else:
        return JsonResponse({'status':False, 'message':'your pin must be 4 digits in length'})

    if session_token:
        resp = Rider.decode_auth_token(session_token, request)

        if isinstance(resp, int):
            rider_id = resp
            try:
                obj = Rider.objects.get(id=rider_id)
                # print(type(obj.pin))
                if obj.pin == int(old_pin):
                    for key, value in defaults.items():
                        setattr(obj, key, value)
                    obj.save()
                    return JsonResponse({'status':True, 'message':'pin sucessfully changed'})

                response_object = {'status':False, 'message':'please, input the correct current pin'}
                logger.critical(f'[{ip}] - Invalid pin - Payload: {data} -Response: {response_object}')
                return JsonResponse(response_object)
                
            except Exception as e:
                
                response_object = {'status':False, 'message':'No rider found'}
                logger.critical(f'[{ip}] - No rider found - Payload: {data} -Response: {response_object}')
                return JsonResponse(response_object) 
                
        response_object = {'status':False, 'message':resp}
        logger.critical(f'[{ip}] - {resp} - Payload: {data} - Token: {session_token} - Response: {response_object}')
        return JsonResponse(response_object)

    response_object = {'status':False, 'message':'Provide a valid session token.'}
    logger.critical(f'[{ip}] - Wrong token - Payload: {data} -Token: {session_token} -Response: {response_object}')
    return JsonResponse(response_object) 

# receives the session_token
@api_view(['POST'])
def logout(request):
    # session_token = request.headers.get('Authorization')
    token = request.headers.get('Authorization')
    ip = get_client_ip(request)

    if token:
        session_token = token.split(" ")[1]
    else:
        session_token = ''
    # blacklist the token to log out the user
    if session_token:
        resp = Rider.decode_auth_token(session_token, request)

        if isinstance(resp, int):
            # rider_id = resp
            blacklist = BlackList(token=session_token)
            blacklist.save()
            return JsonResponse({'status':True, 'message':"Logged out sucessfully"})

        response_object = {'status':False, 'message':resp}
        logger.critical(f'[{ip}] - {resp} - Payload-token: {session_token} -Response: {response_object}')
        return JsonResponse(response_object)

    response_object = {'status':False, 'message':'Provide a valid session token.'}
    logger.critical(f'[{ip}] - Wrong token - Payload-token: {session_token} -Response: {response_object}')
    return JsonResponse(response_object) 


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
    ip = get_client_ip(request)

    if token:
        session_token = token.split(" ")[1]
    else:
        session_token = ''
    if session_token:
        resp = Rider.decode_auth_token(session_token, request)

        if isinstance(resp, int):
            rider_id = resp
            result = Request.objects.filter(rider=rider_id).exclude(status='Completed')
            serializer = RequestSerializer(result, many=True)
            data = serializer.data
            return JsonResponse({'status':True, 'message':'OK', 'requests': data})

        response_object = {'status':False, 'message':resp}
        logger.critical(f'[{ip}] - {resp} - Payload-token: {session_token} -Response: {response_object}')
        return JsonResponse(response_object)

    response_object = {'status':False, 'message':'Provide a valid session token.'}
    logger.critical(f'[{ip}] - Wrong token - Payload-token: {session_token} -Response: {response_object}')
    return JsonResponse(response_object) 

# receives a session_token & request_id & status(accept, picked-up, complete, cancel)
@api_view(['POST'])
def update_status(request):
    data = request.data
    # token = request.headers.get('Authorization')
    request_id = data.get('id')
    status = data.get('status')
    ip = get_client_ip(request)
    token = request.headers.get('Authorization')

    if token:
        session_token = token.split(" ")[1]
    else:
        session_token = ''
    if session_token:
        resp = Rider.decode_auth_token(session_token, request)

        if isinstance(resp, int):
            # rider_id = resp
            try:
                request = Request.objects.get(id=request_id)
            except Exception as e:
                return JsonResponse({'status':False, 'message':'No request by this id'})
        # return JsonResponse({'status':False, 'message': resp})

            if status != 'accept' or status != 'complete' or status != 'picked' or status != 'picked':
                if status == 'accept' and request.status == 'Assigned':
                    serializer = RequestSerializer(request, data={'status': 'Accepted'}, partial=True)
                    if serializer.is_valid():
                        serializer.save()
                elif status == 'picked' and request.status == 'Accepted':
                    # create the initial instance location of the rider at the pickup point to beinging tracking
                    # keys = ['lat', 'long']
                    # loc = str({x:request.pickup_location[x] for x in keys}).replace(',', '>')
                    # # print(loc)
                    try:
                        RequestLocation.objects.get(request=request, rider=request.rider)
                    except Exception as e:
                        new_location_instance = RequestLocation(request=request, rider=request.rider, current_location=[])
                        new_location_instance.save()
                    serializer = RequestSerializer(request, data={'status': 'Enroute'}, partial=True)
                    if serializer.is_valid():
                        serializer.save()
                elif status == 'complete' and request.status == 'Enroute':
                    serializer = RequestSerializer(request, data={'status': 'Completed'}, partial=True)
                    if serializer.is_valid():
                        serializer.save()
                elif status == 'cancel':
                    serializer = RequestSerializer(request, data={'status': 'Cancelled'}, partial=True)
                    if serializer.is_valid():
                        serializer.save()

                return JsonResponse({'status':True, 'message':'OK'})
                
            response_object = {'status':False, 'message':'Please, select a valid status and try again'}
            logger.critical(f'[{ip}] - No rider found - Payload: {data} -Response: {response_object}')
            return JsonResponse(response_object)

        response_object = {'status':False, 'message':resp}
        logger.critical(f'[{ip}] - {resp} - Payload: {data} - Token: {session_token} -Response: {response_object}')
        return JsonResponse(response_object)

    response_object = {'status':False, 'message':'Provide a valid session token.'}
    logger.critical(f'[{ip}] - Wrong token - Payload: {data} - Token: {session_token} -Response: {response_object}')
    return JsonResponse(response_object) 

# receives a session_token, request_id, long & lat
@api_view(['POST'])
def update_rider_location(request):
    data = request.data
    # token = request.headers.get('Authorization')
    request_id = data.get('id')
    long = data.get('long')
    lat = data.get('lat')
    token = request.headers.get('Authorization')
    ip = get_client_ip(request)
    
    if token:
        session_token = token.split(" ")[1]
    else:
        session_token = ''

    location = {"long":long, "lat": lat}

    # if 'long' in location and 'lat' in location:
    #     current_location=str(location).replace(',', '>')
    # else:
    #     return JsonResponse({'status':False, 'message':'Invalid location object.Location must contain "long" and "lat"'})
   
    if session_token:
        resp = Rider.decode_auth_token(session_token, request)

        if isinstance(resp, int):
            rider_id = resp
            if request_id:
                current_location=str(location).replace(',', '>')
                try:
                    obj = RequestLocation.objects.get(request=request_id, rider=rider_id)
                    # for key, value in defaults.items():
                    #     setattr(obj, key, value)  
                    obj.current_location.append(current_location)
                    obj.save()
                    return JsonResponse({'status':True, 'message':'OK'})
                except Exception as e:

                    response_object = {'status':False, 'message':'This request is not enroute yet'}
                    logger.critical(f'[{ip}] - Not enroute yet - Payload: {data} -Response: {response_object}')
                    return JsonResponse(response_object)

            else:
                try:
                    obj = RiderLocation.objects.get(rider=rider_id)
                    obj.current_location = location
                    obj.save()
                    return JsonResponse({'status':True, 'message':'OK'})
                except Exception:
                    rider = Rider.objects.get(id=rider_id)
                    new_location_instance = RiderLocation(rider=rider, current_location=location)
                    new_location_instance.save()
                    return JsonResponse({'status':True, 'message':'OK'})

        response_object = {'status':False, 'message':resp}
        logger.critical(f'[{ip}] - No rider found - Payload: {data}- Token: {session_token} -Response: {response_object}')
        return JsonResponse(response_object)

    response_object = {'status':False, 'message':'Provide a valid session token.'}
    logger.critical(f'[{ip}] - Wrong token - Payload: {data} - TOken: {session_token} - Response: {response_object}')
    return JsonResponse(response_object) 

# receives a session_token
@api_view(['POST'])
def get_current_location(request):
    # data = request.data
    # token = request.headers.get('Authorization')
    # request_id = data.get('id')

    token = request.headers.get('Authorization')
    ip = get_client_ip(request)

    if token:
        session_token = token.split(" ")[1]
    else:
        session_token = ''

    # blacklisted = BlackList.objects.filter(token=session_token)

    if session_token:
        resp = Rider.decode_auth_token(session_token, request)

        if isinstance(resp, int):
            rider_id = resp
            try:
                rider_location = RiderLocation.objects.get(rider=rider_id)
                # for key, value in defaults.items():
                #     setattr(obj, key, value)
                # print(rider)
                # obj.save()
                return JsonResponse({'status':True, 'message':'OK', 'rider_location':rider_location.current_location})
            except Exception as e:
                response_object = {'status':False, 'message':'The request doesn"t exists'}
                logger.critical(f'[{ip}] - request not found - Payload-token: {session_token} -Response: {response_object}')
                return JsonResponse(response_object)

        response_object = {'status':False, 'message':resp}
        logger.critical(f'[{ip}] - {resp} - Payload-token: {session_token} -Response: {response_object}')
        return JsonResponse(response_object)

    response_object = {'status':False, 'message':'Provide a valid session token.'}
    logger.critical(f'[{ip}] - Wrong token - Payload-token: {session_token} -Response: {response_object}')
    return JsonResponse(response_object) 
# receives a session_token
@api_view(['POST'])
def get_rides(request):
    # token = request.headers.get('Authorization')
    token = request.headers.get('Authorization')
    ip = get_client_ip(request)

    if token:
        session_token = token.split(" ")[1]
    else:
        session_token = ''
    # blacklisted = BlackList.objects.filter(token=session_token)
    
    if session_token:
        resp = Rider.decode_auth_token(session_token, request)

        if isinstance(resp, int):
            rider_id = resp

            results = Request.objects.filter(rider=rider_id, status="Completed")
            
            rides = []

            for result in results:

                request_location = RequestLocation.objects.get(request=result.id)
            
                duration = get_duration(request_location.date_created, request_location.date_modified)

                ride = { 'ride_id': result.id, 'destination': result.delivery_location,'pickup' :result.pickup_location,
                'distance' : str(get_distance(result.pickup_location, result.delivery_location)) + "kms", 'date': result.date_modified.strftime("%d %B, %Y"), "duration": duration}

                rides.append(ride)

            return JsonResponse({'status':True, 'message':'OK', 'rides': rides})

        response_object = {'status':False, 'message':resp}
        logger.critical(f'[{ip}] - {resp} - Payload-token: {session_token} -Response: {response_object}')
        return JsonResponse(response_object)

    response_object = {'status':False, 'message':'Provide a valid session token.'}
    logger.critical(f'[{ip}] - Wrong token - Payload-token: {session_token} -Response: {response_object}')
    return JsonResponse(response_object) 

# receives a session_token
@api_view(['POST'])
def get_rider_info(request):
    # token = request.headers.get('Authorization')
    token = request.headers.get('Authorization')
    ip = get_client_ip(request)

    if token:
        session_token = token.split(" ")[1]
    else:
        session_token = ''
    # blacklisted = BlackList.objects.filter(token=session_token)
    
    if session_token:
        resp = Rider.decode_auth_token(session_token, request)

        if isinstance(resp, int):
            rider_id = resp
            
            try:
                rider = Rider.objects.get(id=rider_id)
            except Exception as e:
                    response_object = {'status':False, 'message':'Rider doesn"t exist'}
                    logger.critical(f'[{ip}] - Rider not found - Payload-token: {session_token} -Response: {response_object}')
                    return JsonResponse(response_object)

            rides = Request.objects.filter(rider=rider_id, status="Completed")
            distances = []
            for result in rides:
                dis = get_distance(result.pickup_location, result.delivery_location)

                distances.append(dis)
            
            info = {"name": rider.name, "phone": rider.phone_number, "total_rides": len(rides), "total_distance": str(sum(distances)) + "kms"}
    
            return JsonResponse({'status':True, 'message':'OK', 'info': info})

        response_object = {'status':False, 'message':resp}
        logger.critical(f'[{ip}] - {resp} - Payload-token: {session_token} -Response: {response_object}')
        return JsonResponse(response_object)

    response_object = {'status':False, 'message':'Provide a valid session token.'}
    logger.critical(f'[{ip}] - Wrong token - Payload-token: {session_token} -Response: {response_object}')
    return JsonResponse(response_object) 

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
