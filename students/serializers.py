from rest_framework import serializers
from .models import Enrolment

class EnrolmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrolment
        fields = ['id', 'student', 'classroom']
        depth = 1
