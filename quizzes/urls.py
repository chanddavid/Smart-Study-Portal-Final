from django.urls import path
from .views import create_quiz, launch_quiz, submit_answer, submit_quiz, reveal_answer, quiz_results, me_grades

urlpatterns = [
    path('quizzes/', create_quiz, name='create_quiz'),
    path('quizzes/<int:id>/launch/', launch_quiz, name='launch_quiz'),
    path('quizzes/<int:id>/submit/', submit_quiz, name='submit_quiz'),
    path('quizzes/<int:id>/questions/<int:question_id>/submit/', submit_answer, name='submit_answer'),
    path('quizzes/<int:id>/reveal/', reveal_answer, name='reveal_answer'),
    path('quizzes/<int:id>/results/', quiz_results, name='quiz_results'),
    path('me/grades/', me_grades, name='me_grades'),
]
