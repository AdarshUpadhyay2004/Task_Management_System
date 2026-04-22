# Task Management System

A Django-based Task Management System with authentication, task assignment, time tracking, analytics, chatbot support, gamification, personal notes, smart notifications, KPI reporting, real-time team presence, and Role-Based Access Control (RBAC).

## Main Highlights
- Custom user model with role support
- RBAC for `Manager`, `Team Lead`, and `Employee`
- Task creation, assignment, tracking, and completion
- Work session timer with start and stop flow
- Role-based dashboards and filtered task views
- Reports, analytics, heatmaps, and risk tracking
- KPI dashboard with charts and filters
- Personal notes for each logged-in user
- Smart notifications with in-app, email, and WebSocket delivery
- Chatbot, rewards, badges, and live team presence

## Role-Based Access Control (RBAC)

### Roles
- `Manager`
- `Team Lead`
- `Employee`

### User Model
The custom user model includes:
- `role`
- `department`
- `email`
- profile media fields such as `avatar` and `banner`

### Role Permissions

#### Manager
- Can view all tasks
- Can view analytics and reports
- Can view activity logs
- Can manage users and assign roles from admin/app screens
- Cannot create or assign tasks directly through the Team Lead task flow

#### Team Lead
- Can create tasks
- Can update tasks
- Can assign tasks to employees
- Can view team tasks
- Can access the Team Lead dashboard

#### Employee
- Can view only assigned tasks
- Can start task timer
- Can stop task timer
- Can mark task as completed
- Can access their personal task view

### RBAC Utilities
The project includes reusable RBAC helpers:
- `get_user_role(user)`
- `has_permission(user, action)`
- role decorators for Manager, Team Lead, and Employee access
- middleware that injects the current role into `request.current_role`

## Core Features

### Authentication and User Management
- Login using the custom Django user model
- Manager-controlled user creation and password reset
- Role and department assignment from forms and Django admin
- Profile settings for avatar and banner uploads
- Employee impersonation for Manager users

### Task Management
- Create, edit, assign, and delete tasks
- Task statuses:
  `NEW`, `IN_PROGRESS`, `DONE`
- Task priorities:
  `HIGH`, `MEDIUM`, `LOW`
- Due date and estimated hours support
- Automatic priority suggestion
- Activity logging for task-related changes

### Work Session Tracking
- Start a task timer
- Stop a running task timer
- Prevent multiple active timers for the same employee
- Track `started_at`, `ended_at`, and `duration_seconds`
- Mark tasks complete after stopping active work

### Role-Based Dashboards
- Manager dashboard with task summary charts and analytics
- Team Lead dashboard with team task counts and department team members
- Employee task dashboard for assigned work
- Role-based home redirect after login

### Personal Notes
- Each user can create, edit, delete, and view only their own notes
- Notes are sorted by latest updates, with pinned notes shown first
- Search notes by title or content
- Expand note cards to view full content
- Pin and unpin notes for quick access

### Smart Notifications
- Notification model with unread/read state and timestamps
- In-app notification bell with unread badge
- Real-time WebSocket notifications using Django Channels
- Email notifications for task assignment and overdue tasks
- Notifications for:
  task assignment, deadline approaching, and task overdue
- Mark one or all notifications as read
- Toast popups and sound alerts for new notifications

### KPI Dashboard
- Task Completion Rate calculation
- Delay Rate calculation
- Productivity Score based on completion, on-time delivery, and tracked hours
- Filter KPI metrics by:
  selected user and last `7` or `30` days
- Visual charts using Chart.js:
  pie chart, bar chart, doughnut progress, and trend chart
- Leaderboard view for users with reporting access
- Delay alert when delay rate is above `30%`

## Analytics and Reports
- Completed tasks report
- Productivity heatmap for the last 90 days
- Task risk dashboard
- Activity log timeline
- Reports API for Manager users only
- KPI API and KPI dashboard for performance metrics

## Smart Productivity Features
- Smart deadline prediction
- Risk levels:
  `On Track`
  `At Risk`
  `High Risk`
  `Delayed`
- Automatic risk recalculation
- Progress percentage calculation using tracked work time
- Warning messages for risky tasks

## Chatbot Features
- Text-based assistant for task and work-hour queries
- Voice chatbot support in the browser
- Speech-to-text input
- Optional text-to-speech output
- Multi-language support for English, Hindi, and basic Hinglish

## Gamification Features
- Points for completed tasks
- Automatic level progression
- Badge system
- Rewards dashboard
- Leaderboard and streak-based engagement

## Real-Time Team Presence
- Live team presence page
- Online, idle, and offline states
- Django Channels and Daphne integration
- Live presence updates
- Last-seen tracking
- Typing indicator support

## Notification and Real-Time UX
- Notification dropdown in the shared layout
- WebSocket updates on `/ws/notifications/`
- Presence updates on `/ws/presence/`
- Optional Redis channel layer support through `REDIS_URL`

## Frontend Behavior by Role

### Manager UI
- Sees Manager dashboard
- Sees analytics and reports links
- Sees KPI dashboard
- Sees all tasks
- Sees user management screens
- Does not get Team Lead assignment buttons in normal flow

### Team Lead UI
- Sees Team Lead dashboard
- Sees team tasks
- Sees `Assign Task` button
- Sees KPI dashboard
- Can access task create and edit screens

### Employee UI
- Sees assigned tasks only
- Does not see task assignment controls
- Can start, stop, and complete assigned tasks
- Can access KPI dashboard, notes, and notifications

## API Endpoints

### Task APIs
- `GET /api/tasks/`
  Returns tasks filtered by role
  - Manager: all tasks
  - Team Lead: team-visible tasks
  - Employee: assigned tasks only

- `POST /api/tasks/create/`
  Team Lead only

### Report APIs
- `GET /api/reports/`
  Manager only

### Other APIs
- `GET /api/kpi/`
- `GET /notifications/`
- `POST /notifications/read/`
- `POST /notifications/read-all/`
- `GET /tasks/risk/`
- `GET /api/logs/`
- `GET /api/heatmap/`
- `GET /users/status/`

## Main Web URLs
- `/`
  Role-based home redirect

- `/dashboard/`
  Manager dashboard

- `/dashboard/team-lead/`
  Team Lead dashboard

- `/dashboard/report/`
  Completed tasks report

- `/dashboard/heatmap/`
  Productivity heatmap for Manager

- `/dashboard/kpi/`
  KPI dashboard with filters and charts

- `/tasks/`
  Main role-aware task list

- `/tasks/create/`
  Task create page for Team Lead

- `/tasks/risk-dashboard/`
  Task risk dashboard

- `/notes/`
  Personal notes page

- `/notifications/`
  Notification list endpoint

- `/notifications/read/`
  Mark notification(s) as read

- `/notifications/read-all/`
  Mark all notifications as read

- `/chat/`
  Chatbot page

- `/rewards/`
  Gamification dashboard

- `/team/presence/`
  Team presence page

## WebSocket URLs
- `/ws/presence/`
  Team presence updates

- `/ws/notifications/`
  Real-time notification updates

## Django Admin Support
- Admin can assign roles to users
- Admin can assign departments to users
- Role and department are visible in user list filters
- Admin can review notifications and notes

## Project Structure
- `accounts/`
  Custom user model, RBAC helpers, decorators, forms, and user views
- `tasks/`
  Task model, work sessions, task views, APIs, and risk logic
- `dashboard/`
  Role-based dashboards, reports, analytics, heatmap, and KPI logic
- `notes/`
  Personal notes model, forms, views, and templates
- `notifications/`
  Notifications model, signals, email helpers, WebSocket consumer, APIs, and management command
- `gamification/`
  Points, levels, badges, and rewards
- `presence/`
  Live team presence and WebSocket updates
- `chatbot/`
  Chatbot views and assistant logic

## Setup (Windows / PowerShell)
```powershell
cd C:\Working\python_project
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python manage.py migrate
.\.venv\Scripts\python manage.py createsuperuser
.\.venv\Scripts\python manage.py runserver
```

Open `http://127.0.0.1:8000/`.

## Important Migration Note
This project now uses RBAC roles:
- `MANAGER`
- `TEAM_LEAD`
- `EMPLOYEE`

If you are upgrading from the older version:
- old `ADMIN` users are migrated to `MANAGER`
- a new `department` field is added to the user model

Run:

```powershell
.\.venv\Scripts\python manage.py migrate
```

## Real-Time Presence Notes
- Real-time presence uses Django Channels and Daphne
- Install all dependencies from `requirements.txt`
- Start the app with:

```powershell
.\.venv\Scripts\python manage.py runserver
```

## Notification Scheduler
Deadline-near and overdue notifications can also be generated by a scheduled command:

```powershell
.\.venv\Scripts\python manage.py send_deadline_notifications
```

You can run this daily using Task Scheduler, cron, or Celery Beat.

## Redis Channel Layer (Optional)
For multi-user production real-time updates, configure Redis:

```powershell
$env:REDIS_URL="redis://127.0.0.1:6379/1"
.\.venv\Scripts\python manage.py runserver
```

## MySQL Config (Optional)
By default the project uses SQLite. To use MySQL, set environment variables before running migrations:

```powershell
$env:DB_ENGINE="mysql"
$env:DB_NAME="task_db"
$env:DB_USER="root"
$env:DB_PASSWORD="your_password"
$env:DB_HOST="127.0.0.1"
$env:DB_PORT="3306"
.\.venv\Scripts\python manage.py migrate
```

## Email Configuration
Default email backend is console output during development. To use SMTP:

```powershell
$env:EMAIL_HOST="smtp.example.com"
$env:EMAIL_PORT="587"
$env:EMAIL_HOST_USER="user@example.com"
$env:EMAIL_HOST_PASSWORD="app_password"
$env:EMAIL_USE_TLS="1"
```

## Recommended Test Commands
```powershell
.\.venv\Scripts\python manage.py check
.\.venv\Scripts\python manage.py test
```
