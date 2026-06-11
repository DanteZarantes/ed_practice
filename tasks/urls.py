from django.urls import path
from . import views

urlpatterns = [
    # Tasks
    path('', views.task_list, name='task_list'),
    path('task/<int:pk>/', views.task_detail, name='task_detail'),
    path('task/create/', views.task_create, name='task_create'),
    path('task/<int:pk>/edit/', views.task_edit, name='task_edit'),
    path('task/<int:pk>/delete/', views.task_delete, name='task_delete'),
    path('task/<int:pk>/toggle/', views.task_toggle, name='task_toggle'),

    # Kanban
    path('kanban/', views.kanban_view, name='kanban'),

    # Trash
    path('trash/', views.trash_view, name='trash'),
    path('api/task/<int:pk>/restore/', views.task_restore, name='task_restore'),
    path('api/task/<int:pk>/permanent-delete/', views.task_permanent_delete, name='task_permanent_delete'),
    path('api/trash/empty/', views.trash_empty, name='trash_empty'),

    # AJAX endpoints
    path('api/task/<int:pk>/toggle/', views.task_toggle_ajax, name='task_toggle_ajax'),
    path('api/task/<int:pk>/delete/', views.task_delete_ajax, name='task_delete_ajax'),
    path('api/task/<int:pk>/status/', views.task_update_status, name='task_update_status'),
    path('api/tasks/reorder/', views.task_reorder, name='task_reorder'),
    path('api/subtask/<int:pk>/toggle/', views.subtask_toggle, name='subtask_toggle'),
    path('api/subtask/<int:pk>/delete/', views.subtask_delete, name='subtask_delete'),
    path('api/attachment/<int:pk>/delete/', views.attachment_delete, name='attachment_delete'),
    path('api/tasks/bulk/', views.bulk_action, name='bulk_action'),

    # Dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('api/dashboard-data/', views.dashboard_data, name='dashboard_data'),

    # Auth
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Profile
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
]
