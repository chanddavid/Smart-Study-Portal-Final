from django.db import models
from django.conf import settings
from classroom.models import Class

class Quiz(models.Model):
    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('LIVE', 'Live'),
        ('COMPLETED', 'Completed'),
    )
    classroom = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='quizzes')
    title = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')

    def __str__(self):
        return f"{self.title} ({self.status})"

class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    options = models.JSONField(default=list) # e.g. ["Option A", "Option B"]
    correct_index = models.IntegerField()

    def __str__(self):
        return self.text

class QuizSubmission(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='quiz_submissions')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='submissions')
    selected_index = models.IntegerField()
    is_correct = models.BooleanField()

    def __str__(self):
        return f"{self.student.email} - {self.question.id} ({self.is_correct})"
