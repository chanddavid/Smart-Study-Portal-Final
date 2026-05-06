from django.urls import path
from .views import class_calendar, manage_calendar_event

urlpatterns = [
    path('classes/<int:class_id>/calendar/', class_calendar, name='class_calendar'),
    path('calendar/<int:event_id>/', manage_calendar_event, name='manage_calendar_event'),
]
