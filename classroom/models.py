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
    

class GroupSet(models.Model):
    classroom = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='group_sets')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_group_sets')
    group_size = models.PositiveIntegerField(default=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['classroom'],
                condition=models.Q(is_active=True),
                name='unique_active_group_set_per_class',
            )
        ]

    def __str__(self):
        status = 'Active' if self.is_active else 'Past'
        return f"{self.classroom.name} groups ({status})"

class StudentGroup(models.Model):
    group_set = models.ForeignKey(GroupSet, on_delete=models.CASCADE, related_name='groups')
    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']
        unique_together = ('group_set', 'name')

    def __str__(self):
        return self.name

class StudentGroupMember(models.Model):
    group = models.ForeignKey(StudentGroup, on_delete=models.CASCADE, related_name='members')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='group_memberships')

    class Meta:
        unique_together = ('group', 'student')

    def __str__(self):
        return f"{self.student.email} in {self.group.name}"
