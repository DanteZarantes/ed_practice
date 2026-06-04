from django.contrib import admin
from .models import Task, Profile


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'priority', 'status', 'category', 'due_date', 'completed', 'created_at']
    list_filter = ['priority', 'status', 'category', 'completed']
    search_fields = ['title', 'description']
    list_editable = ['priority', 'status', 'completed']


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'location', 'created_at']
    search_fields = ['user__username', 'user__email']
