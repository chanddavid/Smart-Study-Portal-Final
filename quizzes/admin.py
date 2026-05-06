from django.contrib import admin

# Register your models here.
from .models import Quiz, Question, QuizSubmission
admin.site.register(Quiz)
admin.site.register(Question)   
admin.site.register(QuizSubmission)

