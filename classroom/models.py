from django.db import models
from django.conf import settings

class Class(models.Model):
    name = models.CharField(max_length=255)
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='classes')

    def __str__(self):
        return self.name

class Announcement(models.Model):
    classroom = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='announcements')
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Announcement for {self.classroom.name} at {self.sent_at}"
