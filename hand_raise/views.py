from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import HandRaise
from classroom.models import Class
from .serializers import HandRaiseSerializer
from authentication.permissions import IsTeacher, IsStudent
from realtime.utils import broadcast_to_class

@api_view(['GET', 'DELETE'])
@permission_classes([IsTeacher])
def class_hand_raises(request, class_id):
    classroom = get_object_or_404(Class, id=class_id, teacher=request.user)
    
    if request.method == 'GET':
        hand_raises = HandRaise.objects.filter(classroom=classroom, lowered_at__isnull=True).order_by('raised_at')
        return Response(HandRaiseSerializer(hand_raises, many=True).data)
        
    elif request.method == 'DELETE':
        from django.utils import timezone
        HandRaise.objects.filter(classroom=classroom, lowered_at__isnull=True).update(lowered_at=timezone.now())
        broadcast_to_class(class_id, 'queue_cleared', {})
        return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['POST'])
@permission_classes([IsStudent])
def raise_hand(request):
    class_id = request.data.get('class_id')
    classroom = get_object_or_404(Class, id=class_id)
    
    hand_raise, created = HandRaise.objects.get_or_create(
        student=request.user, 
        classroom=classroom, 
        lowered_at__isnull=True
    )
    if created:
        broadcast_to_class(class_id, 'hand_raised', {'student_email': request.user.email})
    return Response(HandRaiseSerializer(hand_raise).data, status=status.HTTP_201_CREATED)

@api_view(['DELETE'])
def lower_hand(request, id):
    from django.utils import timezone
    hand_raise = get_object_or_404(HandRaise, id=id)
    
    if getattr(request.user, 'role', '') == 'TEACHER':
        if hand_raise.classroom.teacher != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
    else:
        if hand_raise.student != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
            
    hand_raise.lowered_at = timezone.now()
    hand_raise.save()
    broadcast_to_class(hand_raise.classroom.id, 'hand_lowered', {'student_email': hand_raise.student.email})
    return Response(status=status.HTTP_204_NO_CONTENT)
