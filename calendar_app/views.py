from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import CalendarEvent
from classroom.models import Class
from .serializers import CalendarEventSerializer
from authentication.permissions import IsTeacher

@api_view(['GET', 'POST'])
def class_calendar(request, class_id):
    classroom = get_object_or_404(Class, id=class_id)
    
    if request.method == 'GET':
        events = CalendarEvent.objects.filter(classroom=classroom).order_by('event_date')
        return Response(CalendarEventSerializer(events, many=True).data)
        
    elif request.method == 'POST':
        if getattr(request.user, 'role', '') != 'TEACHER':
            return Response(status=status.HTTP_403_FORBIDDEN)
            
        data = request.data.copy()
        data['classroom'] = classroom.id
        serializer = CalendarEventSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PATCH', 'DELETE'])
@permission_classes([IsTeacher])
def manage_calendar_event(request, event_id):
    event = get_object_or_404(CalendarEvent, id=event_id, classroom__teacher=request.user)
    
    if request.method == 'DELETE':
        event.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
        
    elif request.method == 'PATCH':
        serializer = CalendarEventSerializer(event, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
