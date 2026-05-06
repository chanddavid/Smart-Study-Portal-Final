from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'role', 'phone_number', 'address')


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'phone_number', 'address')
        extra_kwargs = {
            'first_name': {'required': False},  
            'last_name': {'required': False},
            'phone_number': {'required': False},
            'address': {'required': False},
        }
