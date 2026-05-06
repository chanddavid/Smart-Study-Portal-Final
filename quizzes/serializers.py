from rest_framework import serializers
from .models import Quiz, Question, QuizSubmission

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'text', 'options', 'correct_index']

# Hides correct_index from students so they can't cheat
class StudentQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'text', 'options']

class QuizSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    class Meta:
        model = Quiz
        fields = ['id', 'classroom', 'title', 'status', 'questions']

class StudentQuizSerializer(serializers.ModelSerializer):
    questions = StudentQuestionSerializer(many=True, read_only=True)
    class Meta:
        model = Quiz
        fields = ['id', 'classroom', 'title', 'status', 'questions']

class QuizSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizSubmission
        fields = '__all__'
