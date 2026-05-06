# Smart Study Portal — Backend API

A role-based classroom management backend built with Django, Django REST Framework, and Django Channels. Features JWT authentication, live quizzes, student enrolment, hand-raise queues, announcements, calendar scheduling, and real-time WebSocket broadcasts.


## Tech Stack
- **Python 3.10+** / **Django 6.x**
- **Django REST Framework** (SimpleJWT for auth)
- **Django Channels** + Daphne (WebSockets)
- **PostgreSQL** (via Supabase)
- **bcrypt** password hashing


## Installation & Setup

1. **Create and activate a Virtual Environment** (PowerShell / Windows)
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate
   ```
   ```for mac/linux
   python -m venv venv
   source/bin/activate
   ```

2. **Install dependencies**
   ```powershell
   .\venv\Scripts\pip install -r requirements.txt
   ```
   ```for mac/linux
   pip install -r requirements.txt
   ```

3. **Environment Variables**
   Create a `.env` in the root folder:
   ```env
   DEBUG=True
   DATABASE_URL=postgresql://postgres.xxx:YOURPASSWORD@aws-xxx.pooler.supabase.com:5432/postgres
   SECRET_KEY=your-secret-key-here
   ALLOWED_HOSTS=127.0.0.1,localhost
   ```

4. **Migrations**
   ```powershell
   .\venv\Scripts\python manage.py makemigrations
   .\venv\Scripts\python manage.py migrate
   ```

5. **Create Initial Teacher (Admin)**
   ```powershell
   .\venv\Scripts\python manage.py createsuperuser
   ```
   Follow the prompts (email, first name, last name, password). Superusers are automatically assigned the `TEACHER` role.

6. **Run Development Server**
   ```powershell
   .\venv\Scripts\python manage.py runserver
   ```

> **Note:** The root `http://127.0.0.1:8000/` returns 404 — this is expected. Use the specific API endpoints documented below.

---

## Authentication

All protected endpoints require a **Bearer token** in the `Authorization` header:
```
Authorization: Bearer <access_token>
```

Access tokens expire in **15 minutes**. Use the refresh endpoint to get a new one.

### Roles
| Role       | Description                                      |
|------------|--------------------------------------------------|
| `TEACHER`  | Can create classes, quizzes, manage students      |
| `STUDENT`  | Can join classes, submit quiz answers, raise hand  |

---

## API Endpoints Reference

**Base URL:** `http://127.0.0.1:8000`

### 1. Authentication

| Method | Endpoint                          | Auth     | Description                      |
|--------|-----------------------------------|----------|----------------------------------|
| POST   | `/auth/login/`                    | ❌ None  | Login and get access token       |
| POST   | `/auth/refresh/`                  | 🍪 Cookie | Refresh access token             |
| POST   | `/auth/logout/`                   | ✅ Bearer | Logout and clear refresh cookie  |
| GET    | `/me/`                            | ✅ Bearer | Get current user profile         |
| POST   | `/auth/password-reset/request/`   | ❌ None  | Request password reset           |
| POST   | `/auth/password-reset/confirm/`   | ❌ None  | Confirm password reset           |

#### `POST /auth/login/`
**Request:**
```json
{
  "email": "teacher@example.com",
  "password": "your-password"
}
```
**Response `200`:**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": 1,
    "email": "teacher@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "TEACHER"
  }
}
```
> Also sets an `httponly` cookie named `refresh_token` for silent refresh.

**Response `401`:** `{"detail": "Invalid credentials"}`

---

#### `POST /auth/refresh/`
Reads the `refresh_token` from cookies (no body needed).

**Response `200`:**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIs..."
}
```

---

#### `POST /auth/logout/`
Clears the refresh token cookie.

**Response `200`:** `{"detail": "Logged out successfully."}`

---

#### `GET /me/`
**Response `200`:**
```json
{
  "id": 1,
  "email": "teacher@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "role": "TEACHER"
}
```

---

#### `POST /auth/password-reset/request/`
**Request:**
```json
{
  "email": "teacher@example.com"
}
```
**Response `200`:** `{"detail": "Password reset link sent (check console)."}`

> In development, the UID and token are printed to the server console.

---

#### `POST /auth/password-reset/confirm/`
**Request:**
```json
{
  "uid": "MQ",
  "token": "d7j86l-eb1ea4196a695d689990...",
  "new_password": "NewSecurePass123!"
}
```
**Response `200`:** `{"detail": "Password reset successful."}`
**Response `400`:** `{"detail": "Invalid token."}`

---

### 2. Classrooms

| Method | Endpoint                                | Auth     | Role      | Description            |
|--------|-----------------------------------------|----------|-----------|------------------------|
| GET    | `/classes/`                             | ✅ Bearer | Any       | List user's classes    |
| POST   | `/classes/`                             | ✅ Bearer | Teacher   | Create a new class     |
| GET    | `/classes/<class_id>/`                  | ✅ Bearer | Any       | Get class detail       |
| PATCH  | `/classes/<class_id>/`                  | ✅ Bearer | Teacher*  | Update class           |
| DELETE | `/classes/<class_id>/`                  | ✅ Bearer | Teacher*  | Delete class           |

> *Only the assigned teacher can modify/delete their own class.

#### `POST /classes/`
**Request:**
```json
{
  "name": "Mathematics 101"
}
```
**Response `201`:**
```json
{
  "id": 1,
  "name": "Mathematics 101",
  "teacher": 1
}
```

#### `PATCH /classes/<class_id>/`
**Request:**
```json
{
  "name": "Advanced Mathematics"
}
```
**Response `200`:** Returns the updated class object.

#### `GET /classes/`
- **Teachers** → returns classes they created
- **Students** → returns classes they are enrolled in

---

### 3. Students (Enrolment)

| Method | Endpoint                                             | Auth     | Role    | Description              |
|--------|------------------------------------------------------|----------|---------|--------------------------|
| GET    | `/classes/<class_id>/students/`                      | ✅ Bearer | Teacher | List enrolled students   |
| POST   | `/classes/<class_id>/students/`                      | ✅ Bearer | Teacher | Enroll a student         |
| DELETE | `/classes/<class_id>/students/<student_id>/`         | ✅ Bearer | Teacher | Remove a student         |

#### `POST /classes/<class_id>/students/`
**Request:**
```json
{
  "email": "student@example.com"
}
```
> The student must already exist in the system with `role: STUDENT`.

**Response `201`:**
```json
{
  "id": 1,
  "student": {
    "id": 3,
    "email": "student@example.com",
    "first_name": "Jane",
    "last_name": "Smith",
    "role": "STUDENT"
  },
  "classroom": {
    "id": 1,
    "name": "Mathematics 101",
    "teacher": 1
  }
}
```
**Response `400`:** `{"detail": "Student already enrolled"}`

---

### 4. Announcements

| Method | Endpoint                                          | Auth     | Role     | Description             |
|--------|---------------------------------------------------|----------|----------|-------------------------|
| GET    | `/classes/<class_id>/announcements/`              | ✅ Bearer | Any      | List announcements      |
| POST   | `/classes/<class_id>/announcements/`              | ✅ Bearer | Teacher* | Create announcement     |

> *Only the assigned teacher of the class.

#### `POST /classes/<class_id>/announcements/`
**Request:**
```json
{
  "message": "Homework due tomorrow!"
}
```
**Response `201`:**
```json
{
  "id": 1,
  "classroom": 1,
  "message": "Homework due tomorrow!",
  "sent_at": "2026-04-24T09:00:00Z"
}
```
> Also broadcasts a `new_announcement` event via WebSocket.

---

### 5. Quizzes

| Method | Endpoint                                                       | Auth     | Role    | Description                |
|--------|----------------------------------------------------------------|----------|---------|----------------------------|
| GET    | `/quizzes/?class_id=<class_id>`                                | ✅ Bearer | Teacher | List quizzes for a class   |
| POST   | `/quizzes/`                                                    | ✅ Bearer | Teacher | Create a quiz              |
| POST   | `/quizzes/<quiz_id>/launch/`                                   | ✅ Bearer | Teacher | Launch quiz (set LIVE)     |
| POST   | `/quizzes/<quiz_id>/questions/<question_id>/submit/`           | ✅ Bearer | Student | Submit an answer           |
| POST   | `/quizzes/<quiz_id>/reveal/`                                   | ✅ Bearer | Teacher | Complete quiz & reveal     |
| GET    | `/quizzes/<quiz_id>/results/`                                  | ✅ Bearer | Any     | Get quiz results           |
| GET    | `/me/grades/`                                                  | ✅ Bearer | Student | Get student's grades       |

#### `POST /quizzes/`
**Request:**
```json
{
  "class_id": 1,
  "title": "Chapter 1 Quiz",
  "questions": [
    {
      "text": "What is 2 + 2?",
      "options": ["3", "4", "5"],
      "correct_index": 1
    },
    {
      "text": "Capital of France?",
      "options": ["London", "Berlin", "Paris"],
      "correct_index": 2
    }
  ]
}
```
**Response `201`:**
```json
{
  "id": 1,
  "classroom": 1,
  "title": "Chapter 1 Quiz",
  "status": "DRAFT",
  "questions": [
    {
      "id": 1,
      "text": "What is 2 + 2?",
      "options": ["3", "4", "5"],
      "correct_index": 1
    }
  ]
}
```

#### Quiz Lifecycle
```
DRAFT → LIVE (launch) → COMPLETED (reveal)
```
- `POST /quizzes/<id>/launch/` → sets status to `LIVE`, broadcasts `quiz_launched` event
- `POST /quizzes/<id>/reveal/` → sets status to `COMPLETED`, broadcasts `quiz_completed` event

#### `POST /quizzes/<quiz_id>/questions/<question_id>/submit/`
**Request:**
```json
{
  "selected_index": 1
}
```
**Response `200`:**
```json
{
  "is_correct": true
}
```

#### `GET /quizzes/<quiz_id>/results/`
**Teacher response:**
```json
[
  { "student": "student@example.com", "question_id": 1, "is_correct": true },
  { "student": "student@example.com", "question_id": 2, "is_correct": false }
]
```
**Student response:**
```json
[
  { "question_id": 1, "is_correct": true },
  { "question_id": 2, "is_correct": false }
]
```

#### `GET /me/grades/`
**Response `200`:**
```json
[
  { "quiz": "Chapter 1 Quiz", "question_id": 1, "is_correct": true }
]
```

---

### 6. Hand Raise

| Method | Endpoint                                   | Auth     | Role     | Description              |
|--------|--------------------------------------------|----------|----------|--------------------------|
| POST   | `/hand-raises/`                            | ✅ Bearer | Student  | Raise hand               |
| GET    | `/classes/<class_id>/hand-raises/`         | ✅ Bearer | Teacher  | List active hand raises  |
| DELETE | `/hand-raises/<id>/`                       | ✅ Bearer | Any*     | Lower a hand             |
| DELETE | `/classes/<class_id>/hand-raises/`         | ✅ Bearer | Teacher  | Clear entire queue       |

> *Students can lower their own hand; Teachers can lower any hand in their class.

#### `POST /hand-raises/`
**Request:**
```json
{
  "class_id": 1
}
```
**Response `201`:**
```json
{
  "id": 1,
  "student": 3,
  "classroom": 1,
  "raised_at": "2026-04-24T09:05:00Z",
  "lowered_at": null
}
```
> Broadcasts `hand_raised` event via WebSocket.
> Lowering broadcasts `hand_lowered`. Clearing broadcasts `queue_cleared`.

---

### 7. Calendar

| Method | Endpoint                                   | Auth     | Role     | Description             |
|--------|--------------------------------------------|----------|----------|-------------------------|
| GET    | `/classes/<class_id>/calendar/`            | ✅ Bearer | Any      | List calendar events    |
| POST   | `/classes/<class_id>/calendar/`            | ✅ Bearer | Teacher  | Create calendar event   |
| PATCH  | `/calendar/<event_id>/`                    | ✅ Bearer | Teacher  | Update calendar event   |
| DELETE | `/calendar/<event_id>/`                    | ✅ Bearer | Teacher  | Delete calendar event   |

#### `POST /classes/<class_id>/calendar/`
**Request:**
```json
{
  "title": "Mid-term Exam",
  "event_date": "2026-05-15T10:00:00Z"
}
```
**Response `201`:**
```json
{
  "id": 1,
  "classroom": 1,
  "title": "Mid-term Exam",
  "event_date": "2026-05-15T10:00:00Z"
}
```

---

### 8. Randomizer Tools

| Method | Endpoint                       | Auth     | Role    | Description                    |
|--------|--------------------------------|----------|---------|--------------------------------|
| POST   | `/random/groups/`              | ✅ Bearer | Teacher | Random student groups          |
| POST   | `/random/presentation-order/`  | ✅ Bearer | Teacher | Random presentation order      |
| POST   | `/random/pick-student/`        | ✅ Bearer | Teacher | Pick one random student        |

#### `POST /random/groups/`
**Request:**
```json
{
  "class_id": 1,
  "group_size": 3
}
```
**Response `200`:**
```json
{
  "groups": [
    [
      { "id": 3, "name": "Jane Smith" },
      { "id": 4, "name": "Bob Lee" },
      { "id": 5, "name": "Alice Chen" }
    ],
    [
      { "id": 6, "name": "Tom Brown" }
    ]
  ]
}
```

#### `POST /random/presentation-order/`
**Request:**
```json
{
  "class_id": 1
}
```
**Response `200`:**
```json
{
  "order": [
    { "id": 4, "name": "Bob Lee" },
    { "id": 3, "name": "Jane Smith" }
  ]
}
```

#### `POST /random/pick-student/`
**Request:**
```json
{
  "class_id": 1
}
```
**Response `200`:**
```json
{
  "student": { "id": 3, "name": "Jane Smith" }
}
```

---

## WebSocket (Real-time Events)

Connect to a classroom's real-time channel:
```
ws://127.0.0.1:8000/ws/classroom/<class_id>/
```

### Events Received

| Event              | Trigger                        | Data                                     |
|--------------------|--------------------------------|------------------------------------------|
| `new_announcement` | Teacher posts announcement     | `{"message": "..."}`                    |
| `quiz_launched`    | Teacher launches quiz          | `{"quiz_id": 1, "title": "..."}`        |
| `quiz_completed`   | Teacher reveals quiz answers   | `{"quiz_id": 1}`                        |
| `hand_raised`      | Student raises hand            | `{"student_email": "..."}`              |
| `hand_lowered`     | Hand is lowered                | `{"student_email": "..."}`              |
| `queue_cleared`    | Teacher clears hand raise queue| `{}`                                    |

**Message format:**
```json
{
  "event": "quiz_launched",
  "data": {
    "quiz_id": 1,
    "title": "Chapter 1 Quiz"
  }
}
```

---

## Error Responses

All error responses follow a consistent format:

| Status | Meaning                  | Example                                    |
|--------|--------------------------|--------------------------------------------|
| `400`  | Bad Request              | `{"detail": "Student already enrolled"}`   |
| `401`  | Unauthorized             | `{"detail": "Invalid credentials"}`        |
| `403`  | Forbidden                | `{"detail": "Only teachers can create..."}`|
| `404`  | Not Found                | `{"detail": "Not found."}`                 |

---

## Postman Collection

A ready-to-use Postman Collection is included:
```
Smart_Study_Portal_Postman_Collection.json
```
Import directly into Postman. Default host: `http://127.0.0.1:8000`

---

## Useful Commands

| Command | Purpose |
|---------|---------|
| `.\venv\Scripts\python manage.py check` | Scan for syntax/import errors |
| `.\venv\Scripts\python manage.py runserver` | Start dev server (HTTP + WebSocket) |
| `.\venv\Scripts\python manage.py createsuperuser` | Create a teacher account |
| `.\venv\Scripts\python manage.py makemigrations` | Generate new migrations |
| `.\venv\Scripts\python manage.py migrate` | Apply migrations |
| `.\venv\Scripts\python manage.py test` | Run test suite |
