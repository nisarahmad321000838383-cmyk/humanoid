# Humanoid Backend

Django REST Framework backend for the Humanoid AI chatbot application.

## Features

- RESTful API with Django REST Framework
- JWT authentication
- MySQL database integration
- Hugging Face API integration for AI responses
- User management and settings
- Chat history persistence

## Setup

### 1. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your configuration:
- Database credentials
- Secret key
- Hugging Face API key

### 4. Set Up Database

Create MySQL database:
```bash
mysql -u root -p
CREATE DATABASE humanoid_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 5. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

### 7. Run Development Server

```bash
python manage.py runserver
```

Server will be available at `http://localhost:8000`

## API Documentation

### Authentication Endpoints

#### Register
```
POST /api/auth/register/
Content-Type: application/json

{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "securepassword",
  "password2": "securepassword",
  "first_name": "John",
  "last_name": "Doe"
}
```

#### Login
```
POST /api/auth/login/
Content-Type: application/json

{
  "username": "johndoe",
  "password": "securepassword"
}
```

#### Get Current User
```
GET /api/auth/user/
Authorization: Bearer <access_token>
```

### Chat Endpoints

#### List Chats
```
GET /api/chats/
Authorization: Bearer <access_token>
```

#### Create Chat
```
POST /api/chats/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "title": "My Chat"
}
```

#### Get Chat Details
```
GET /api/chats/{id}/
Authorization: Bearer <access_token>
```

#### Send Message
```
POST /api/chats/{id}/send_message/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "message": "Hello, how are you?"
}
```

#### Get Chat History
```
GET /api/chats/history/
Authorization: Bearer <access_token>
```

### Settings Endpoints

#### Get User Settings
```
GET /api/settings/
Authorization: Bearer <access_token>
```

#### Update User Settings
```
PUT /api/settings/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "theme": "dark"
}
```

## Models

### Chat
- `user`: ForeignKey to User
- `title`: CharField
- `created_at`: DateTimeField
- `updated_at`: DateTimeField

### Message
- `chat`: ForeignKey to Chat
- `role`: CharField (user/assistant)
- `content`: TextField
- `created_at`: DateTimeField

### UserSettings
- `user`: OneToOneField to User
- `theme`: CharField (light/dark)
- `created_at`: DateTimeField
- `updated_at`: DateTimeField

## Hugging Face Integration

The backend uses Hugging Face's Inference API to generate AI responses using the Qwen1.5-110B-Chat model.

### Configuration
Set your Hugging Face API key in `.env`:
```
HUGGINGFACE_API_KEY=your_api_key_here
```

### Model
- Model: `Qwen/Qwen1.5-110B-Chat`
- Parameters: Configurable in `api/huggingface_service.py`

## Admin Panel

Access the admin panel at `http://localhost:8000/admin` with your superuser credentials.

### Available Models
- Users
- Chats
- Messages
- User Settings

## Testing

Run tests:
```bash
python manage.py test
```

## Common Commands

```bash
# Make migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver

# Open Django shell
python manage.py shell

# Collect static files
python manage.py collectstatic
```

## Troubleshooting

### Database Connection Error
- Check MySQL is running: `sudo service mysql status`
- Verify credentials in `.env`
- Ensure database exists

### Migration Errors
```bash
# Reset migrations (development only)
python manage.py migrate --fake api zero
python manage.py migrate api
```

### Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

## Production Deployment

1. Set `DEBUG=False`
2. Use strong `SECRET_KEY`
3. Configure `ALLOWED_HOSTS`
4. Set up Gunicorn
5. Configure Nginx as reverse proxy
6. Use environment variables for sensitive data
7. Set up SSL certificate

Example Gunicorn command:
```bash
gunicorn humanoid.wsgi:application --bind 0.0.0.0:8000
```
