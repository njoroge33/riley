from django.db import models

# import datetime
# from phonenumber_field.modelfields import PhoneNumberField
class Client(models.Model):
    name = models.CharField(max_length=255)
    status = models.BooleanField(null=False, default=True)

class Branch(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    status = models.BooleanField(null=False, default=True)
    location = models.JSONField(default=dict)


class Rider(models.Model):
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, unique=True)
    active = models.BooleanField(null=False, default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    pin = models.IntegerField(unique=True, null=False)

class Otp(models.Model):
    phone_number = models.CharField(max_length=20)
    otp = models.CharField(max_length =6, unique=True)
    imei = models.CharField(max_length=20)
    date_created = models.DateTimeField(auto_now_add=True)
    
class RiderLocation(models.Model):
    rider = models.ForeignKey(Rider, on_delete=models.CASCADE)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    status = status = models.BooleanField(null=False, default=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

class Request(models.Model):
    STATUSES_CHOICES = (
        ('Pending asignment', 'Pending assignment'),
        ('Assigned', 'Assigned'),
        ('Enroute', 'Enroute'),
        ('Cancelled', 'Cancelled'),
    )
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    rider = models.ForeignKey(Rider, on_delete=models.CASCADE)
    status = models.CharField(max_length=25, choices=STATUSES_CHOICES)
    pickup_location = models.JSONField(default=dict)
    delivery_location = models.JSONField(default=dict)
    notes = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

# class BlackList(models.Model):
#     token = models.CharField(max_length=500, unique=True)
#     date_added = models.DateTimeField(auto_now_add=True)
    


  