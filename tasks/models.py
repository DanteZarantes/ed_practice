from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar_color = models.CharField(max_length=7, default='#10b981')
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=100, blank=True)
    theme = models.CharField(max_length=10, choices=[('dark', 'Dark'), ('light', 'Light')], default='dark')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s profile"

    @property
    def initials(self):
        if self.user.first_name and self.user.last_name:
            return f"{self.user.first_name[0]}{self.user.last_name[0]}".upper()
        return self.user.username[:2].upper()


class Task(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    STATUS_CHOICES = [
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
    ]

    CATEGORY_CHOICES = [
        ('work', 'Work'),
        ('personal', 'Personal'),
        ('study', 'Study'),
        ('health', 'Health'),
        ('finance', 'Finance'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='todo')
    category = models.CharField(max_length=15, choices=CATEGORY_CHOICES, default='other')
    due_date = models.DateField(null=True, blank=True)
    position = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed = models.BooleanField(default=False)

    class Meta:
        ordering = ['position', '-created_at']

    def __str__(self):
        return self.title

    @property
    def is_overdue(self):
        if self.due_date and not self.completed:
            return self.due_date < timezone.now().date()
        return False

    @property
    def is_due_soon(self):
        """Returns True if task is due within the next 2 days."""
        if self.due_date and not self.completed:
            delta = self.due_date - timezone.now().date()
            return 0 <= delta.days <= 2
        return False

    @property
    def time_remaining(self):
        if not self.due_date or self.completed:
            return None
        days = (self.due_date - timezone.now().date()).days
        if days < 0:
            return f"Overdue by {-days} day{'s' if -days != 1 else ''}"
        if days == 0:
            return "Due today"
        if days == 1:
            return "Due tomorrow"
        if days < 7:
            return f"{days} days left"
        weeks = days // 7
        return f"{weeks} week{'s' if weeks != 1 else ''} left"

    @property
    def subtask_progress(self):
        """Returns (completed_count, total_count) for subtasks."""
        total = self.subtasks.count()
        if total == 0:
            return (0, 0)
        done = self.subtasks.filter(is_completed=True).count()
        return (done, total)

    @property
    def subtask_percentage(self):
        done, total = self.subtask_progress
        if total == 0:
            return 0
        return int((done / total) * 100)


class TaskAttachment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='attachments/%Y/%m/')
    filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.filename

    @property
    def file_exists(self):
        try:
            return self.file and self.file.storage.exists(self.file.name)
        except Exception:
            return False


class SubTask(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='subtasks')
    title = models.CharField(max_length=200)
    is_completed = models.BooleanField(default=False)
    position = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['position', 'created_at']

    def __str__(self):
        return self.title


class Activity(models.Model):
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('completed', 'Completed'),
        ('reopened', 'Reopened'),
        ('deleted', 'Deleted'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    task_title = models.CharField(max_length=200)
    action = models.CharField(max_length=15, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = 'Activities'

    def __str__(self):
        return f"{self.user.username} {self.action} '{self.task_title}'"

    @property
    def icon(self):
        icons = {
            'created': 'bi-plus-circle',
            'updated': 'bi-pencil',
            'completed': 'bi-check-circle',
            'reopened': 'bi-arrow-counterclockwise',
            'deleted': 'bi-trash3',
        }
        return icons.get(self.action, 'bi-circle')

    @property
    def color(self):
        colors = {
            'created': '#10b981',
            'updated': '#3b82f6',
            'completed': '#34d399',
            'reopened': '#f59e0b',
            'deleted': '#ef4444',
        }
        return colors.get(self.action, '#94a3b8')
