import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Q, Count
from django.db.models.functions import TruncDate
from django.http import JsonResponse
from .models import Task, Profile
from .forms import TaskForm, SignUpForm, ProfileForm


# ─── Authentication Views ─────────────────────────────────────────────────────

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('task_list')
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create profile if signal didn't fire
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

    context = {
        'profile': profile,
        'stats': stats,
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

    # Statistics for current user
    user_tasks = Task.objects.filter(user=request.user)
    total_tasks = user_tasks.count()
    completed_tasks = user_tasks.filter(status='done').count()
    pending_tasks = user_tasks.filter(status='todo').count()
    in_progress_tasks = user_tasks.filter(status='in_progress').count()

    context = {
        'tasks': tasks,
        'query': query,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'category_filter': category_filter,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'in_progress_tasks': in_progress_tasks,
    }
    return render(request, 'tasks/task_list.html', context)


@login_required
def task_detail(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    return render(request, 'tasks/task_detail.html', {'task': task})


@login_required
def task_create(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()
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
        messages.success(request, f'Task "{title}" deleted successfully!')
        return redirect('task_list')
    return render(request, 'tasks/task_confirm_delete.html', {'task': task})


@login_required
def task_toggle(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    if task.status == 'done':
        task.status = 'todo'
        task.completed = False
    else:
        task.status = 'done'
        task.completed = True
    task.save()
    return redirect('task_list')


# ─── Dashboard / Visualization Views ─────────────────────────────────────────

@login_required
def dashboard_view(request):
    return render(request, 'tasks/dashboard.html')


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
