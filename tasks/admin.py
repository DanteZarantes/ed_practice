from django.contrib import admin
from .models import Task, Profile, SubTask, Activity, TaskAttachment


class SubTaskInline(admin.TabularInline):
    model = SubTask
    extra = 1


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'priority', 'status', 'category', 'due_date', 'completed', 'created_at']
    list_filter = ['priority', 'status', 'category', 'completed']
    search_fields = ['title', 'description']
    list_editable = ['priority', 'status', 'completed']
    inlines = [SubTaskInline]


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'location', 'theme', 'created_at']
    search_fields = ['user__username', 'user__email']


@admin.register(SubTask)
class SubTaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'task', 'is_completed', 'position']
    list_filter = ['is_completed']
    search_fields = ['title']


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'task_title', 'timestamp']
    list_filter = ['action']
    search_fields = ['task_title', 'user__username']
    readonly_fields = ['timestamp']


@admin.register(TaskAttachment)
class TaskAttachmentAdmin(admin.ModelAdmin):
    list_display = ['filename', 'task', 'uploaded_at']
    readonly_fields = ['uploaded_at']
