from django.db import models
from classroom.models import Class

class CalendarEvent(models.Model):
    classroom = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='calendar_events')
    title = models.CharField(max_length=255)
    event_date = models.DateTimeField()
    

    def __str__(self):
        return f"{self.title} on {self.event_date}"

