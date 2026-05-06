import random
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Class, Announcement
from .serializers import ClassSerializer, AnnouncementSerializer
from students.models import Enrolment
from authentication.permissions import IsTeacher
from rest_framework.permissions import IsAuthenticated
from realtime.utils import broadcast_to_class

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def class_list_create(request):
    if request.method == 'GET':
        if getattr(request.user, 'role', '') == 'TEACHER':
            classes = Class.objects.filter(teacher=request.user)
        else:
            classes = Class.objects.filter(enrolments__student=request.user)
        serializer = ClassSerializer(classes, many=True)
        return Response(serializer.data)
        
    elif request.method == 'POST':
        if getattr(request.user, 'role', '') != 'TEACHER':
            return Response({'detail': 'Only teachers can create classes.'}, status=status.HTTP_403_FORBIDDEN)
            
        data = request.data.copy()
        data['teacher'] = request.user.id
        serializer = ClassSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def class_detail(request, class_id):
    classroom = get_object_or_404(Class, id=class_id)
    
    if request.method == 'GET':
        return Response(ClassSerializer(classroom).data)
        
    elif request.method == 'PATCH':
        if getattr(request.user, 'role', '') != 'TEACHER' or classroom.teacher != request.user:
            return Response({'detail': 'Only the assigned teacher can modify.'}, status=status.HTTP_403_FORBIDDEN)
            
        serializer = ClassSerializer(classroom, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    elif request.method == 'DELETE':
        if getattr(request.user, 'role', '') != 'TEACHER' or classroom.teacher != request.user:
            return Response({'detail': 'Only the assigned teacher can delete.'}, status=status.HTTP_403_FORBIDDEN)
            
        classroom.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
@api_view(['POST'])
@permission_classes([IsTeacher])
def random_groups(request):
    class_id = request.data.get('class_id')
    group_size = int(request.data.get('group_size', 2))
    classroom = get_object_or_404(Class, id=class_id, teacher=request.user)
    
    students = list(Enrolment.objects.filter(classroom=classroom).select_related('student'))
    random.shuffle(students)
    
    groups = []
    for i in range(0, len(students), group_size):
        group = students[i:i + group_size]
        groups.append([{'id': s.student.id, 'name': f"{s.student.first_name} {s.student.last_name}"} for s in group])
        
    return Response({'groups': groups})

@api_view(['POST'])
@permission_classes([IsTeacher])
def presentation_order(request):
    class_id = request.data.get('class_id')
    classroom = get_object_or_404(Class, id=class_id, teacher=request.user)
    
    students = list(Enrolment.objects.filter(classroom=classroom).select_related('student'))
    random.shuffle(students)
    
    order = [{'id': s.student.id, 'name': f"{s.student.first_name} {s.student.last_name}"} for s in students]
    return Response({'order': order})

@api_view(['POST'])
@permission_classes([IsTeacher])
def pick_student(request):
    class_id = request.data.get('class_id')
    classroom = get_object_or_404(Class, id=class_id, teacher=request.user)
    
    students = list(Enrolment.objects.filter(classroom=classroom).select_related('student'))
    if not students:
        return Response({'detail': 'No students enrolled.'}, status=400)
        
    picked = random.choice(students)
    return Response({
        'student': {'id': picked.student.id, 'name': f"{picked.student.first_name} {picked.student.last_name}"}
    })

@api_view(['GET', 'POST'])
def class_announcements(request, class_id):
    classroom = get_object_or_404(Class, id=class_id)
    
    if request.method == 'GET':
        announcements = Announcement.objects.filter(classroom=classroom).order_by('-sent_at')
        serializer = AnnouncementSerializer(announcements, many=True)
        return Response(serializer.data)
        
    elif request.method == 'POST':
        if getattr(request.user, 'role', '') != 'TEACHER' or classroom.teacher != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
            
        data = request.data.copy()
        data['classroom'] = classroom.id
        serializer = AnnouncementSerializer(data=data)
        if serializer.is_valid():
            announcement = serializer.save()
            broadcast_to_class(classroom.id, 'new_announcement', {'message': announcement.message})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
