from django.db import models
from django.conf import settings
from classroom.models import Class

class HandRaise(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='hand_raises')
    classroom = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='hand_raises')
    raised_at = models.DateTimeField(auto_now_add=True)
    lowered_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.student.email} in {self.classroom.name} at {self.raised_at}"
