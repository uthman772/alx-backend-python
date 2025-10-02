# Django Messaging App

A Django REST Framework based messaging application.

## Setup

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
4. Install dependencies: `pip install -r requirements.txt`
5. Run migrations: `python manage.py migrate`
6. Create superuser: `python manage.py createsuperuser`
7. Run the server: `python manage.py runserver`

## API Endpoints

- `GET /api/messages/` - List all messages
- `POST /api/messages/` - Create a new message
- `GET /api/messages/{id}/` - Retrieve a specific message
- `PUT /api/messages/{id}/` - Update a message
- `DELETE /api/messages/{id}/` - Delete a message
- `GET /api/messages/unread/` - List unread messages
- `POST /api/messages/{id}/mark_read/` - Mark a message as read