from django.urls import path
from .views import class_hand_raises, raise_hand, lower_hand

urlpatterns = [
    path('classes/<int:class_id>/hand-raises/', class_hand_raises, name='class_hand_raises'),
    path('hand-raises/', raise_hand, name='raise_hand'),
    path('hand-raises/<int:id>/', lower_hand, name='lower_hand'),
]
