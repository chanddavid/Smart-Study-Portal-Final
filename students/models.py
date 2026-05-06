from django.db import models
from django.conf import settings
from classroom.models import Class

class Enrolment(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='enrolments')
    classroom = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='enrolments')

    class Meta:
        unique_together = ('student', 'classroom')
        
    def __str__(self):
        return f"{self.student.email} in {self.classroom.name}"
