# TaskFlow - Task Manager

A dynamic task management web application built with Django. Features a dark/light theme, Kanban board, subtasks, activity tracking, D3.js dashboard visualizations, and keyboard shortcuts.

## Project Structure

```
Programming/
├── manage.py                  # Django management script
├── requirements.txt           # Python dependencies
├── db.sqlite3                 # SQLite database (auto-generated)
├── static/                    # Static files (CSS, JS, images)
│   └── .gitkeep
├── taskmanager/               # Django project settings
│   ├── __init__.py
│   ├── settings.py            # Project configuration
│   ├── urls.py                # Root URL routing
│   ├── wsgi.py                # WSGI entry point
│   └── asgi.py                # ASGI entry point
├── media/                     # Uploaded files (auto-generated)
│   └── attachments/           # Task attachments (organized by YYYY/MM/)
├── tasks/                     # Main application
│   ├── __init__.py
│   ├── admin.py               # Admin panel registration
│   ├── apps.py                # App configuration
│   ├── forms.py               # Task, Profile, SignUp, Attachment forms
│   ├── models.py              # Task, SubTask, Profile, Activity, TaskAttachment models
│   ├── signals.py             # Auto-create profile; delete attachment files on removal
│   ├── urls.py                # App URL patterns
│   ├── views.py               # Views and API endpoints
│   ├── tests.py               # Tests
│   └── migrations/            # Database migrations
└── templates/                 # HTML templates
    ├── base.html              # Base layout (navbar, theme, shortcuts)
    ├── accounts/
    │   ├── login.html         # Login page
    │   ├── signup.html        # Registration page
    │   ├── profile.html       # User profile view
    │   └── profile_edit.html  # Edit profile form
    └── tasks/
        ├── task_list.html     # Task list with filters and bulk actions
        ├── task_detail.html   # Single task view with subtasks and attachments
        ├── task_form.html     # Create/Edit task form
        ├── task_confirm_delete.html  # Delete confirmation
        ├── kanban.html        # Kanban board (drag-and-drop)
        └── dashboard.html     # Analytics dashboard with D3.js charts
```

## Features

- **Task Management** - Create, edit, delete, and toggle task completion
- **Subtasks** - Break tasks into smaller steps with progress tracking
- **Kanban Board** - Drag-and-drop tasks between To Do, In Progress, and Done columns
- **Dashboard** - D3.js visualizations (completion ring, status/priority/category charts, activity timeline)
- **Activity Feed** - Tracks all task actions with timestamps
- **Search & Filters** - Filter by status, priority, category; sort by date, priority, or title
- **Bulk Actions** - Select multiple tasks to complete or delete at once
- **Drag-and-Drop Reorder** - Reorder tasks in list view
- **Dark/Light Theme** - Toggle with button or keyboard shortcut, persisted in localStorage
- **Keyboard Shortcuts** - `N` (new task), `/` (search), `T` (theme), `?` (show all shortcuts)
- **Due Date Alerts** - Visual indicators for overdue and upcoming tasks
- **Time Remaining** - Calculated countdown shown on task detail (e.g. "3 days left", "Due today", "Overdue by 2 days")
- **Task Attachments** - Upload and manage files on any task (images, PDF, Word, Excel, ZIP, TXT — max 100MB per file)
- **User Profiles** - Custom avatar color, bio, location

## Prerequisites

- Python 3.10 or higher

## Getting Started

### 1. Clone the repository

```bash
git clone <repository-url>
cd Programming
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it:

- **Windows:**
  ```bash
  venv\Scripts\activate
  ```
- **macOS / Linux:**
  ```bash
  source venv/bin/activate
  ```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Apply database migrations

```bash
python manage.py migrate
```

### 5. Create a superuser (optional, for admin panel)

```bash
python manage.py createsuperuser
```

### 6. Run the development server

```bash
python manage.py runserver
```

Open your browser and go to: **http://127.0.0.1:8000**

## Usage

1. **Register** a new account at `/signup/`
2. **Create tasks** with title, description, priority, status, category, and due date
3. **Manage tasks** from the list view or the Kanban board at `/kanban/`
4. **Add subtasks** from the task detail page
5. **View analytics** on the dashboard at `/dashboard/`
6. **Use keyboard shortcuts** - press `?` to see all available shortcuts
7. **Access the admin panel** at `/admin/` (requires superuser)

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `N` | Create new task |
| `/` | Focus search input |
| `T` | Toggle dark/light theme |
| `?` | Show shortcuts modal |
| `G` then `L` | Go to task list |
| `G` then `K` | Go to Kanban board |
| `G` then `D` | Go to dashboard |
| `Ctrl+A` | Select all tasks |
| `Esc` | Deselect all |

## Tech Stack

- **Backend:** Django 5.1
- **Database:** SQLite (default)
- **Frontend:** Bootstrap 5, Bootstrap Icons, D3.js, SortableJS
- **Fonts:** Inter (Google Fonts)
