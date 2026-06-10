import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core.paginator import Paginator
from django.db.models import Q, Count, F
from django.db.models.functions import TruncDate
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from .models import Task, Profile, SubTask, Activity, TaskAttachment
from .forms import TaskForm, SignUpForm, ProfileForm, SubTaskForm, AttachmentForm


# ─── Helper ──────────────────────────────────────────────────────────────────

def log_activity(user, task_title, action):
    """Log a user activity."""
    Activity.objects.create(user=user, task_title=task_title, action=action)


# ─── Authentication Views ─────────────────────────────────────────────────────

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('task_list')
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.get_or_create(user=user)
            login(request, user)
            messages.success(request, f'Welcome to TaskFlow, {user.first_name}!')
            return redirect('task_list')
    else:
        form = SignUpForm()
    return render(request, 'accounts/signup.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('task_list')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            return redirect('task_list')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})


@require_http_methods(["GET", "POST"])
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('login')


# ─── Profile Views ────────────────────────────────────────────────────────────

@login_required
def profile_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    user_tasks = Task.objects.filter(user=request.user)

    stats = {
        'total': user_tasks.count(),
        'completed': user_tasks.filter(status='done').count(),
        'in_progress': user_tasks.filter(status='in_progress').count(),
        'pending': user_tasks.filter(status='todo').count(),
    }

    # Recent activity
    recent_activity = Activity.objects.filter(user=request.user)[:10]

    context = {
        'profile': profile,
        'stats': stats,
        'recent_activity': recent_activity,
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def profile_edit(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile, user=request.user)
    return render(request, 'accounts/profile_edit.html', {'form': form})


# ─── Task Views ───────────────────────────────────────────────────────────────

@login_required
def task_list(request):
    tasks = Task.objects.filter(user=request.user)

    # Search
    query = request.GET.get('q', '')
    if query:
        tasks = tasks.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )

    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        tasks = tasks.filter(status=status_filter)

    # Filter by priority
    priority_filter = request.GET.get('priority', '')
    if priority_filter:
        tasks = tasks.filter(priority=priority_filter)

    # Filter by category
    category_filter = request.GET.get('category', '')
    if category_filter:
        tasks = tasks.filter(category=category_filter)

    # Sorting
    sort_by = request.GET.get('sort', '')
    if sort_by == 'due_date':
        # Put tasks with no due date at the end
        tasks = tasks.order_by(F('due_date').asc(nulls_last=True))
    elif sort_by == 'priority':
        from django.db.models import Case, When, Value, IntegerField
        tasks = tasks.annotate(
            priority_order=Case(
                When(priority='high', then=Value(1)),
                When(priority='medium', then=Value(2)),
                When(priority='low', then=Value(3)),
                output_field=IntegerField(),
            )
        ).order_by('priority_order')
    elif sort_by == 'title':
        tasks = tasks.order_by('title')
    elif sort_by == 'created':
        tasks = tasks.order_by('-created_at')

    # Pagination
    paginator = Paginator(tasks, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Statistics for current user (use aggregation, not Python loop)
    user_tasks = Task.objects.filter(user=request.user)
    total_tasks = user_tasks.count()
    completed_tasks = user_tasks.filter(status='done').count()
    pending_tasks = user_tasks.filter(status='todo').count()
    in_progress_tasks = user_tasks.filter(status='in_progress').count()

    from django.utils import timezone
    today = timezone.now().date()
    overdue_tasks = user_tasks.filter(
        due_date__lt=today, completed=False
    ).count()

    # Weekly progress: tasks completed this week
    from datetime import timedelta
    week_ago = timezone.now() - timedelta(days=7)
    completed_this_week = user_tasks.filter(
        status='done', updated_at__gte=week_ago
    ).count()
    created_this_week = user_tasks.filter(
        created_at__gte=week_ago
    ).count()

    context = {
        'tasks': page_obj,
        'page_obj': page_obj,
        'query': query,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'category_filter': category_filter,
        'sort_by': sort_by,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'in_progress_tasks': in_progress_tasks,
        'overdue_tasks': overdue_tasks,
        'completed_this_week': completed_this_week,
        'created_this_week': created_this_week,
    }
    return render(request, 'tasks/task_list.html', context)


@login_required
def task_detail(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    subtasks = task.subtasks.all()
    subtask_form = SubTaskForm()
    attachment_form = AttachmentForm()

    if request.method == 'POST':
        if 'subtask_submit' in request.POST:
            subtask_form = SubTaskForm(request.POST)
            if subtask_form.is_valid():
                subtask = subtask_form.save(commit=False)
                subtask.task = task
                subtask.position = task.subtasks.count()
                subtask.save()
                messages.success(request, 'Subtask added!')
                return redirect('task_detail', pk=task.pk)
        elif 'attachment_submit' in request.POST:
            attachment_form = AttachmentForm(request.POST, request.FILES)
            if attachment_form.is_valid():
                attachment = attachment_form.save(commit=False)
                attachment.task = task
                attachment.filename = attachment_form.cleaned_data['file'].name
                attachment.save()
                messages.success(request, 'Attachment uploaded!')
                return redirect('task_detail', pk=task.pk)

    context = {
        'task': task,
        'subtasks': subtasks,
        'subtask_form': subtask_form,
        'attachment_form': attachment_form,
        'attachments': task.attachments.all(),
    }
    return render(request, 'tasks/task_detail.html', context)


@login_required
def task_create(request):
    if request.method == 'POST':
        form = TaskForm(request.POST, request.FILES)

        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.position = Task.objects.filter(user=request.user).count()
            task.save()

            if form.cleaned_data.get('attachment'):
                TaskAttachment.objects.create(
                    task=task,
                    file=form.cleaned_data['attachment'],
                    filename=form.cleaned_data['attachment'].name
                )

            log_activity(request.user, task.title, 'created')
            messages.success(request, f'Task "{task.title}" created successfully!')
            return redirect('task_list')
    else:
        form = TaskForm()

    return render(request, 'tasks/task_form.html', {'form': form, 'title': 'Create Task'})
@login_required
def task_edit(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            log_activity(request.user, task.title, 'updated')
            messages.success(request, f'Task "{task.title}" updated successfully!')
            return redirect('task_list')
    else:
        form = TaskForm(instance=task)
    return render(request, 'tasks/task_form.html', {'form': form, 'title': 'Edit Task', 'task': task})


@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    if request.method == 'POST':
        title = task.title
        task.delete()
        log_activity(request.user, title, 'deleted')
        messages.success(request, f'Task "{title}" deleted successfully!')
        return redirect('task_list')
    return render(request, 'tasks/task_confirm_delete.html', {'task': task})


@login_required
@require_POST
def task_toggle(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    if task.status == 'done':
        task.status = 'todo'
        task.completed = False
        log_activity(request.user, task.title, 'reopened')
    else:
        task.status = 'done'
        task.completed = True
        log_activity(request.user, task.title, 'completed')
    task.save()

    # For AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': task.status,
            'completed': task.completed,
        })
    return redirect('task_list')


@login_required
@require_POST
def attachment_delete(request, pk):
    attachment = get_object_or_404(TaskAttachment, pk=pk, task__user=request.user)
    attachment.delete()
    return JsonResponse({'success': True})


# ─── AJAX / API Views ─────────────────────────────────────────────────────────

@login_required
@require_POST
def task_toggle_ajax(request, pk):
    """AJAX endpoint to toggle task completion without page reload."""
    task = get_object_or_404(Task, pk=pk, user=request.user)
    if task.status == 'done':
        task.status = 'todo'
        task.completed = False
        log_activity(request.user, task.title, 'reopened')
    else:
        task.status = 'done'
        task.completed = True
        log_activity(request.user, task.title, 'completed')
    task.save()
    return JsonResponse({
        'success': True,
        'status': task.status,
        'completed': task.completed,
        'status_display': task.get_status_display(),
    })


@login_required
@require_POST
def task_delete_ajax(request, pk):
    """AJAX endpoint to delete a task without page reload."""
    task = get_object_or_404(Task, pk=pk, user=request.user)
    title = task.title
    task.delete()
    log_activity(request.user, title, 'deleted')
    return JsonResponse({'success': True, 'message': f'Task "{title}" deleted.'})


@login_required
@require_POST
def task_reorder(request):
    """AJAX endpoint to reorder tasks (for drag-and-drop)."""
    try:
        data = json.loads(request.body)
        task_ids = data.get('task_ids', [])
        for index, task_id in enumerate(task_ids):
            Task.objects.filter(pk=task_id, user=request.user).update(position=index)
        return JsonResponse({'success': True})
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({'success': False, 'error': 'Invalid data'}, status=400)


@login_required
@require_POST
def task_update_status(request, pk):
    """AJAX endpoint to update task status (for Kanban drag-and-drop)."""
    task = get_object_or_404(Task, pk=pk, user=request.user)
    try:
        data = json.loads(request.body)
        new_status = data.get('status', '')
        if new_status in dict(Task.STATUS_CHOICES):
            task.status = new_status
            task.completed = (new_status == 'done')
            task.save()
            if new_status == 'done':
                log_activity(request.user, task.title, 'completed')
            return JsonResponse({'success': True, 'status': task.status})
        return JsonResponse({'success': False, 'error': 'Invalid status'}, status=400)
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({'success': False, 'error': 'Invalid data'}, status=400)


@login_required
@require_POST
def subtask_toggle(request, pk):
    """AJAX endpoint to toggle subtask completion."""
    subtask = get_object_or_404(SubTask, pk=pk, task__user=request.user)
    subtask.is_completed = not subtask.is_completed
    subtask.save()
    task = subtask.task
    done, total = task.subtask_progress
    return JsonResponse({
        'success': True,
        'is_completed': subtask.is_completed,
        'progress': task.subtask_percentage,
        'done': done,
        'total': total,
    })


@login_required
@require_POST
def subtask_delete(request, pk):
    """AJAX endpoint to delete a subtask."""
    subtask = get_object_or_404(SubTask, pk=pk, task__user=request.user)
    task = subtask.task
    subtask.delete()
    done, total = task.subtask_progress
    return JsonResponse({
        'success': True,
        'progress': task.subtask_percentage,
        'done': done,
        'total': total,
    })


@login_required
@require_POST
def bulk_action(request):
    """Handle bulk actions on multiple tasks."""
    try:
        data = json.loads(request.body)
        action = data.get('action', '')
        task_ids = data.get('task_ids', [])

        tasks = Task.objects.filter(pk__in=task_ids, user=request.user)

        if action == 'complete':
            count = 0
            for task in tasks:
                task.status = 'done'
                task.completed = True
                task.save()
                log_activity(request.user, task.title, 'completed')
                count += 1
            return JsonResponse({'success': True, 'message': f'{count} task{"s" if count != 1 else ""} completed.'})
        elif action == 'delete':
            count = 0
            for task in tasks:
                log_activity(request.user, task.title, 'deleted')
                count += 1
            tasks.delete()
            return JsonResponse({'success': True, 'message': f'{count} task{"s" if count != 1 else ""} deleted.'})
        elif action in dict(Task.STATUS_CHOICES):
            count = tasks.count()
            tasks.update(status=action, completed=(action == 'done'))
            return JsonResponse({'success': True, 'message': f'{count} task{"s" if count != 1 else ""} updated.'})
        else:
            return JsonResponse({'success': False, 'error': 'Invalid action'}, status=400)
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({'success': False, 'error': 'Invalid data'}, status=400)


# ─── Kanban View ──────────────────────────────────────────────────────────────

@login_required
def kanban_view(request):
    """Kanban board view with drag-and-drop columns."""
    tasks = Task.objects.filter(user=request.user)
    todo_tasks = tasks.filter(status='todo')
    in_progress_tasks = tasks.filter(status='in_progress')
    done_tasks = tasks.filter(status='done')

    context = {
        'todo_tasks': todo_tasks,
        'in_progress_tasks': in_progress_tasks,
        'done_tasks': done_tasks,
    }
    return render(request, 'tasks/kanban.html', context)


# ─── Dashboard / Visualization Views ─────────────────────────────────────────

@login_required
def dashboard_view(request):
    # Recent activity for the dashboard
    recent_activity = Activity.objects.filter(user=request.user)[:15]
    from django.utils import timezone
    from datetime import timedelta
    user_tasks = Task.objects.filter(user=request.user)
    today = timezone.now().date()
    overdue_tasks = user_tasks.filter(due_date__lt=today, completed=False)
    due_soon_tasks = user_tasks.filter(due_date__gte=today, due_date__lte=today + timedelta(days=2), completed=False)

    context = {
        'recent_activity': recent_activity,
        'overdue_tasks': overdue_tasks,
        'due_soon_tasks': due_soon_tasks,
    }
    return render(request, 'tasks/dashboard.html', context)


@login_required
def dashboard_data(request):
    """API endpoint returning chart data for D3.js visualizations."""
    user_tasks = Task.objects.filter(user=request.user)

    # Status distribution
    status_data = list(
        user_tasks.values('status').annotate(count=Count('id'))
    )

    # Priority distribution
    priority_data = list(
        user_tasks.values('priority').annotate(count=Count('id'))
    )

    # Category distribution
    category_data = list(
        user_tasks.values('category').annotate(count=Count('id'))
    )

    # Tasks created over time (last 30 days)
    timeline_data = list(
        user_tasks.annotate(date=TruncDate('created_at'))
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')
    )

    # Completion rate
    total = user_tasks.count()
    completed = user_tasks.filter(status='done').count()

    data = {
        'status': status_data,
        'priority': priority_data,
        'category': category_data,
        'timeline': [{'date': item['date'].isoformat(), 'count': item['count']} for item in timeline_data],
        'completion': {
            'total': total,
            'completed': completed,
            'rate': round((completed / total * 100) if total > 0 else 0, 1),
        }
    }
    return JsonResponse(data)
