from rest_framework import serializers
from .models import Quiz, Question, QuizAttempt, QuizSubmission

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
    attempted = serializers.SerializerMethodField()
    submitted_at = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = ['id', 'classroom', 'title', 'status', 'questions', 'attempted', 'submitted_at']

    def get_attempted(self, obj):
        user = self.context.get('request').user if self.context.get('request') else None
        if not user or not user.is_authenticated:
            return False
        return (
            QuizAttempt.objects.filter(quiz=obj, student=user).exists() or
            QuizSubmission.objects.filter(question__quiz=obj, student=user).exists()
        )

    def get_submitted_at(self, obj):
        user = self.context.get('request').user if self.context.get('request') else None
        if not user or not user.is_authenticated:
            return None
        attempt = QuizAttempt.objects.filter(quiz=obj, student=user).first()
        return attempt.submitted_at if attempt else None

class QuizSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizSubmission
        fields = '__all__'
