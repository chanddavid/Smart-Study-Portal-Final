from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Quiz, Question, QuizSubmission
from classroom.models import Class
from .serializers import QuizSerializer, QuestionSerializer, StudentQuizSerializer
from authentication.permissions import IsTeacher, IsStudent
from realtime.utils import broadcast_to_class

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def create_quiz(request):
    if request.method == 'GET':
        class_id = request.query_params.get('class_id')
        if not class_id:
            return Response({'detail': 'class_id parameter required.'}, status=400)
        quizzes = Quiz.objects.filter(classroom_id=class_id)
        # Use StudentQuizSerializer for students (hides correct_index)
        if getattr(request.user, 'role', '') == 'STUDENT':
            return Response(StudentQuizSerializer(quizzes, many=True).data)
        return Response(QuizSerializer(quizzes, many=True).data)

    # POST — create quiz (teacher only)
    if getattr(request.user, 'role', '') != 'TEACHER':
        return Response({'detail': 'Only teachers can create quizzes.'}, status=status.HTTP_403_FORBIDDEN)

    class_id = request.data.get('class_id')
    classroom = get_object_or_404(Class, id=class_id, teacher=request.user)
    
    data = request.data.copy()
    data['classroom'] = classroom.id
    serializer = QuizSerializer(data=data)
    
    if serializer.is_valid():
        quiz = serializer.save()
        questions = request.data.get('questions', [])
        for q in questions:
            Question.objects.create(
                quiz=quiz,
                text=q.get('text', ''),
                options=q.get('options', []),
                correct_index=q.get('correct_index', 0)
            )
        return Response(QuizSerializer(quiz).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsTeacher])
def launch_quiz(request, id):
    quiz = get_object_or_404(Quiz, id=id, classroom__teacher=request.user)
    quiz.status = 'LIVE'
    quiz.save()
    broadcast_to_class(quiz.classroom.id, 'quiz_launched', {'quiz_id': quiz.id, 'title': quiz.title})
    return Response(QuizSerializer(quiz).data)

@api_view(['POST'])
@permission_classes([IsStudent])
def submit_answer(request, id, question_id):
    quiz = get_object_or_404(Quiz, id=id, status='LIVE')
    question = get_object_or_404(Question, id=question_id, quiz=quiz)
    selected_index = request.data.get('selected_index')
    
    is_correct = (selected_index == question.correct_index)
    
    submission, created = QuizSubmission.objects.update_or_create(
        student=request.user,
        question=question,
        defaults={'selected_index': selected_index, 'is_correct': is_correct}
    )
    return Response({'is_correct': is_correct})

@api_view(['POST'])
@permission_classes([IsTeacher])
def reveal_answer(request, id):
    quiz = get_object_or_404(Quiz, id=id, classroom__teacher=request.user)
    quiz.status = 'COMPLETED'
    quiz.save()
    broadcast_to_class(quiz.classroom.id, 'quiz_completed', {'quiz_id': quiz.id})
    return Response({'status': quiz.status, 'detail': 'Quiz completed and revealed.'})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def quiz_results(request, id):
    quiz = get_object_or_404(Quiz, id=id)
    
    if getattr(request.user, 'role', '') == 'TEACHER':
        if quiz.classroom.teacher != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        submissions = QuizSubmission.objects.filter(question__quiz=quiz).select_related('student', 'question')
        data = [{'student': s.student.email, 'question_id': s.question.id, 'is_correct': s.is_correct} for s in submissions]
        return Response(data)
    else:
        # Students can ONLY see their own submissions
        submissions = QuizSubmission.objects.filter(question__quiz=quiz, student=request.user).select_related('question')
        data = [{'question_id': s.question.id, 'is_correct': s.is_correct} for s in submissions]
        return Response(data)

@api_view(['GET'])
@permission_classes([IsStudent])
def me_grades(request):
    submissions = QuizSubmission.objects.filter(student=request.user)
    data = [{'quiz': s.question.quiz.title, 'question_id': s.question.id, 'is_correct': s.is_correct} for s in submissions]
    return Response(data)
