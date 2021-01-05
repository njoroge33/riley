from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Rider, Request, Branch

class RiderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rider
        exclude = ('pin', )
        
class RequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Request
        fields = '__all__'

class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = '__all__'
