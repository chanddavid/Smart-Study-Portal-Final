from django.urls import path
from .views import random_groups, presentation_order, pick_student, class_announcements, class_list_create, class_detail,class_groups

urlpatterns = [
      path('classes/', class_list_create, name='class_list_create'),
    path('classes/<int:class_id>/', class_detail, name='class_detail'),
    path('classes/<int:class_id>/announcements/', class_announcements, name='class_announcements'),
    path('classes/<int:class_id>/groups/', class_groups, name='class_groups'),
    path('random/groups/', random_groups, name='random_groups'),
    path('random/presentation-order/', presentation_order, name='presentation_order'),
    path('random/pick-student/', pick_student, name='pick_student'),
]
