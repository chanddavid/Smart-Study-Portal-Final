from rest_framework import serializers
from .models import Class, Announcement,StudentGroup, StudentGroupMember

class ClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = Class
        fields = '__all__'

class AnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Announcement
        fields = '__all__'

class StudentGroupMemberSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='student.id', read_only=True)
    name = serializers.SerializerMethodField()
    email = serializers.EmailField(source='student.email', read_only=True)

    class Meta:
        model = StudentGroupMember
        fields = ['id', 'name', 'email']

    def get_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}".strip() or obj.student.email
    

class StudentGroupSerializer(serializers.ModelSerializer):
    members = StudentGroupMemberSerializer(many=True, read_only=True)
    status = serializers.SerializerMethodField()
    group_set_id = serializers.IntegerField(source='group_set.id', read_only=True)
    created_at = serializers.DateTimeField(source='group_set.created_at', read_only=True)

    class Meta:
        model = StudentGroup
        fields = ['id', 'group_set_id', 'name', 'members', 'status', 'created_at']

    def get_status(self, obj):
        return 'Active' if obj.group_set.is_active else 'Past'
