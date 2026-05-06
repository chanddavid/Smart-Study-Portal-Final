from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Enrolment
from classroom.models import Class
from authentication.models import User
from .serializers import EnrolmentSerializer
from authentication.permissions import IsTeacher

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def class_students(request, class_id):
    classroom = get_object_or_404(Class, id=class_id)
    
    if request.method == 'GET':
        enrolments = Enrolment.objects.filter(classroom=classroom).select_related('student')
        return Response(EnrolmentSerializer(enrolments, many=True).data)
        
    elif request.method == 'POST':
        # Only teachers who own this class can enrol students
        if getattr(request.user, 'role', '') != 'TEACHER' or classroom.teacher != request.user:
            return Response({'detail': 'Only the class teacher can enrol students.'}, status=status.HTTP_403_FORBIDDEN)
        email = request.data.get('email')
        if not email:
            return Response({'detail': 'Requires email'}, status=400)
            
        student = get_object_or_404(User, email=email, role='STUDENT')
        enrolment, created = Enrolment.objects.get_or_create(student=student, classroom=classroom)
        if created:
            return Response(EnrolmentSerializer(enrolment).data, status=status.HTTP_201_CREATED)
        return Response({'detail': 'Student already enrolled'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsTeacher])
def manage_student(request, class_id, student_id):
    classroom = get_object_or_404(Class, id=class_id, teacher=request.user)
    enrolment = get_object_or_404(Enrolment, classroom=classroom, student_id=student_id)
    
    if request.method == 'DELETE':
        enrolment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
