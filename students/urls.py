from django.urls import path
from .views import class_students, manage_student

urlpatterns = [
    path('classes/<int:class_id>/students/', class_students, name='class_students'),
    path('classes/<int:class_id>/students/<int:student_id>/', manage_student, name='manage_student'),
]
