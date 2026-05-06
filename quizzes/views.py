from django.db import IntegrityError, transaction
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Quiz, Question, QuizAttempt, QuizSubmission
from classroom.models import Class
from .serializers import QuizSerializer, StudentQuizSerializer
from authentication.permissions import IsTeacher, IsStudent
from realtime.utils import broadcast_to_class
from students.models import Enrolment

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def create_quiz(request):
    if request.method == 'GET':
        class_id = request.query_params.get('class_id')
        if not class_id:
            return Response({'detail': 'class_id parameter required.'}, status=400)
        classroom = get_object_or_404(Class, id=class_id)
        role = getattr(request.user, 'role', '')
        if role == 'TEACHER' and classroom.teacher != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        if role == 'STUDENT' and not Enrolment.objects.filter(classroom=classroom, student=request.user).exists():
            return Response(status=status.HTTP_403_FORBIDDEN)

        quizzes = Quiz.objects.filter(classroom=classroom).prefetch_related('questions')
        # Use StudentQuizSerializer for students (hides correct_index)
        if role == 'STUDENT':
            return Response(StudentQuizSerializer(quizzes, many=True, context={'request': request}).data)
        return Response(QuizSerializer(quizzes, many=True).data)

    # POST — create quiz (teacher only)
    if getattr(request.user, 'role', '') != 'TEACHER':
        return Response({'detail': 'Only teachers can create quizzes.'}, status=status.HTTP_403_FORBIDDEN)

    class_id = request.data.get('class_id')
    classroom = get_object_or_404(Class, id=class_id, teacher=request.user)
    
    data = request.data.copy()
    data['classroom'] = classroom.id
    serializer = QuizSerializer(data=data)
    questions = request.data.get('questions', [])
    if not isinstance(questions, list) or not questions:
        return Response({'detail': 'At least one question is required.'}, status=status.HTTP_400_BAD_REQUEST)

    validated_questions = []
    for q in questions:
        options = q.get('options', [])
        if not isinstance(options, list) or len(options) < 2:
            return Response({'detail': 'Each question needs at least two options.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            correct_index = int(q.get('correct_index', 0))
        except (TypeError, ValueError):
            return Response({'detail': 'Correct index must be a number.'}, status=status.HTTP_400_BAD_REQUEST)
        if correct_index < 0 or correct_index >= len(options):
            return Response({'detail': 'Correct index must match one of the options.'}, status=status.HTTP_400_BAD_REQUEST)
        validated_questions.append({
            'text': q.get('text', ''),
            'options': options,
            'correct_index': correct_index,
        })
    
    if serializer.is_valid():
        quiz = serializer.save()
        for q in validated_questions:
            Question.objects.create(
                quiz=quiz,
                text=q['text'],
                options=q['options'],
                correct_index=q['correct_index']
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
    return Response(
        {'detail': 'Submit the full quiz once using /quizzes/<id>/submit/.'},
        status=status.HTTP_405_METHOD_NOT_ALLOWED,
    )

@api_view(['POST'])
@permission_classes([IsStudent])
def submit_quiz(request, id):
    quiz = get_object_or_404(Quiz.objects.prefetch_related('questions'), id=id, status='LIVE')
    if not Enrolment.objects.filter(classroom=quiz.classroom, student=request.user).exists():
        return Response(status=status.HTTP_403_FORBIDDEN)

    if QuizAttempt.objects.filter(quiz=quiz, student=request.user).exists():
        return Response({'detail': 'Quiz already submitted.'}, status=status.HTTP_400_BAD_REQUEST)
    if QuizSubmission.objects.filter(question__quiz=quiz, student=request.user).exists():
        return Response({'detail': 'Quiz already submitted.'}, status=status.HTTP_400_BAD_REQUEST)

    answers = request.data.get('answers', [])
    if not isinstance(answers, list):
        return Response({'detail': 'Answers must be a list.'}, status=status.HTTP_400_BAD_REQUEST)

    questions = list(quiz.questions.all())
    questions_by_id = {question.id: question for question in questions}
    if len(answers) != len(questions_by_id):
        return Response({'detail': 'Answer every question before submitting.'}, status=status.HTTP_400_BAD_REQUEST)

    clean_answers = []
    seen_questions = set()
    for answer in answers:
        try:
            question_id = int(answer.get('question_id'))
            selected_index = int(answer.get('selected_index'))
        except (TypeError, ValueError, AttributeError):
            return Response({'detail': 'Each answer requires question_id and selected_index.'}, status=status.HTTP_400_BAD_REQUEST)

        question = questions_by_id.get(question_id)
        if not question:
            return Response({'detail': 'Answer contains a question outside this quiz.'}, status=status.HTTP_400_BAD_REQUEST)
        if question_id in seen_questions:
            return Response({'detail': 'Each question can be answered only once.'}, status=status.HTTP_400_BAD_REQUEST)
        if selected_index < 0 or selected_index >= len(question.options):
            return Response({'detail': 'Selected option is invalid.'}, status=status.HTTP_400_BAD_REQUEST)

        seen_questions.add(question_id)
        clean_answers.append((question, selected_index))

    score = sum(1 for question, selected_index in clean_answers if selected_index == question.correct_index)

    try:
        with transaction.atomic():
            attempt = QuizAttempt.objects.create(
                quiz=quiz,
                student=request.user,
                score=score,
                total_questions=len(questions),
            )
            QuizSubmission.objects.bulk_create([
                QuizSubmission(
                    attempt=attempt,
                    student=request.user,
                    question=question,
                    selected_index=selected_index,
                    is_correct=(selected_index == question.correct_index),
                )
                for question, selected_index in clean_answers
            ])
    except IntegrityError:
        return Response({'detail': 'Quiz already submitted.'}, status=status.HTTP_400_BAD_REQUEST)

    return Response({'submitted': True, 'detail': 'Quiz submitted.'})

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
        if quiz.status != 'COMPLETED':
            return Response({'detail': 'Results are available after the quiz ends.'}, status=status.HTTP_403_FORBIDDEN)
        submissions = QuizSubmission.objects.filter(question__quiz=quiz, student=request.user).select_related('question')
        data = [{'question_id': s.question.id, 'is_correct': s.is_correct} for s in submissions]
        return Response(data)

@api_view(['GET'])
@permission_classes([IsStudent])
def me_grades(request):
    submissions = QuizSubmission.objects.filter(student=request.user, question__quiz__status='COMPLETED')
    data = [{'quiz': s.question.quiz.title, 'question_id': s.question.id, 'is_correct': s.is_correct} for s in submissions]
    return Response(data)
