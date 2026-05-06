from django.contrib import admin

# Register your models here.
from .models import Class, Announcement
admin.site.register(Class)
admin.site.register(Announcement)
