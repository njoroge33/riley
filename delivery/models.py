from django.db import models
from django.db.models import CharField
from django_mysql.models import JSONField, ListTextField
import datetime
import jwt
# from .otp import generate_random_otp
from deliver.settings import SECRET_KEY
# from base import *

key = SECRET_KEY

# import datetime
# from phonenumber_field.modelfields import PhoneNumberField
class Client(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
       return f'{self.name}'

class Branch(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    location = JSONField()

    def __str__(self):
        loc=self.location['address']
        return f'{self.client.name, loc}'

class Rider(models.Model):
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, unique=True)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    active = models.BooleanField(null=False, default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    pin = models.IntegerField(unique=True, null=False)

    def __str__(self):
       return f'{self.name}'

    def encode_auth_token(self, user_id, request=None):
        """
        Generates the Auth Token
        :return: string
        """
        payload = {
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1, seconds=5),
                'iat': datetime.datetime.utcnow(),
                'sub': user_id,
                "token_type":"access",
            }
        return jwt.encode(
                payload,
                key,
                algorithm='HS256'
            )
    
    @staticmethod  
    def decode_auth_token(session_token, request=None):
        """
        Decodes the auth token
        :param auth_token:
        :return: string
        """
        try:
            payload = jwt.decode(session_token, key)
            is_blacklisted_token = BlackList.objects.filter(token=session_token)
            if is_blacklisted_token:
                response = 'Token blacklisted. Please log in again.'

                #  log blacklisted token
                # critical_logger.critical(f'[{request.remote_addr}] - {__name__}.decode_auth_token() - Decode blacklisted token failure - Payload token: {auth_token} - Response: {response}')

                return response
            else:
                # if payload['token_type'] and payload['unique'] and not payload['jti']:
                #     response = 'Invalid token. Please log in again.'
                #     return response
                return payload['sub']
        except jwt.ExpiredSignatureError:
            response = 'Signature expired. Please log in again.'

            #  log expired token
            # critical_logger.critical(f'[{request.remote_addr}] - {__name__}.decode_auth_token() - Decode expired token failure - Payload token: {auth_token} - Response: {response}')

            return response
        except jwt.InvalidTokenError:
            response = 'Invalid token. Please log in again.'

            #  log invalid token
            # critical_logger.critical(f'[{request.remote_addr}] - {__name__}.decode_auth_token() - Decode invalid token failure - Payload token: {auth_token} - Response: {response}')
            
            return response

    

class Otp(models.Model):
    phone_number = models.CharField(max_length=20)
    otp = models.CharField(max_length =6, unique=True)
    imei = models.CharField(max_length=20)
    date_created = models.DateTimeField(auto_now_add=True)

class Request(models.Model):
    STATUSES_CHOICES = (
        ('Pending asignment', 'Pending assignment'),
        ('Assigned', 'Assigned'),
        ('Enroute', 'Enroute'),
        ('Accepted', 'Accepted'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    )
    # client = models.ForeignKey(Client, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    rider = models.ForeignKey(Rider, null=True, on_delete=models.CASCADE)
    status = models.CharField(max_length=25, choices=STATUSES_CHOICES)
    pickup_location = JSONField()
    delivery_location = JSONField()
    notes = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

class BlackList(models.Model):
    token = models.CharField(max_length=255, unique=True)
    date_added = models.DateTimeField(auto_now_add=True)

class RiderLocation(models.Model):
    # rider = models.ForeignKey(Rider, on_delete=models.CASCADE)
    # client = models.ForeignKey(Client, on_delete=models.CASCADE)
    # branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    # status = status = models.BooleanField(null=False, default=True)
    # request = models.OneToOneField(Request, on_delete=models.CASCADE, primary_key=True)
    rider = models.ForeignKey(Rider, on_delete=models.CASCADE)
    current_location = JSONField()
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    
    
class RequestLocation(models.Model):
    # rider = models.ForeignKey(Rider, on_delete=models.CASCADE)
    # client = models.ForeignKey(Client, on_delete=models.CASCADE)
    # branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    # status = status = models.BooleanField(null=False, default=True)
    request = models.OneToOneField(Request, on_delete=models.CASCADE, primary_key=True)
    rider = models.ForeignKey(Rider, on_delete=models.CASCADE)
    current_location = ListTextField(base_field=CharField(max_length=60))
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

  