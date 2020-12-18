from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Rider

class RiderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rider
        fields = '__all__'
        
        