from rest_framework import serializers
from .models import HandRaise

class HandRaiseSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    student_email = serializers.CharField(source='student.email', read_only=True)

    class Meta:
        model = HandRaise
        fields = ['id', 'student', 'student_name', 'student_email', 'classroom', 'raised_at', 'lowered_at']

    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}"
