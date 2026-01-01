# Humanoid - AI Chat Assistant

A modern, full-stack AI chatbot application with a sleek interface similar to DeepSeek AI. Built with Django REST Framework backend and React + TypeScript frontend, powered by Hugging Face's Qwen1.5-110B model.

![Humanoid](https://img.shields.io/badge/AI-Chatbot-blue)
![Django](https://img.shields.io/badge/Django-4.2-green)
![React](https://img.shields.io/badge/React-18.2-blue)
![TypeScript](https://img.shields.io/badge/TypeScript-5.2-blue)

## Features

- 🤖 **AI-Powered Chat**: Integrated with Hugging Face's Qwen1.5-110B model
- 🔐 **Authentication**: Secure login and registration with JWT tokens
- 💬 **Chat History**: Persistent chat conversations with sidebar navigation
- 🎨 **Theme Toggle**: Dark/Light mode with user preferences saved
- 📱 **Responsive Design**: Mobile-friendly interface
- ⚡ **Modern Stack**: Django REST Framework + React + TypeScript + Tailwind CSS
- 🗄️ **MySQL Database**: Robust data persistence

## Tech Stack

### Backend
- Django 4.2
- Django REST Framework
- MySQL Database
- JWT Authentication
- Hugging Face API Integration

### Frontend
- React 18
- TypeScript
- Vite
- Tailwind CSS
- React Router
- Axios
- Lucide React Icons

## Project Structure

```
humanoid/
├── backend/              # Django backend
│   ├── humanoid/        # Django project settings
│   ├── api/             # API app (models, views, serializers)
│   ├── manage.py
│   └── requirements.txt
├── frontend/            # React frontend
│   ├── src/
│   │   ├── components/  # Reusable components
│   │   ├── contexts/    # React contexts
│   │   ├── pages/       # Page components
│   │   ├── types/       # TypeScript types
│   │   └── utils/       # Utility functions
│   ├── package.json
│   └── vite.config.ts
└── README.md
```

## Prerequisites

- Python 3.8+
- Node.js 16+
- MySQL 8.0+
- Hugging Face API Key

## Quick Start

### 1. Clone the Repository

```bash
cd /home/fardin-ibrahimi/Desktop/humanoid
```

### 2. Set Up MySQL Database

```bash
mysql -u root -p
```

```sql
CREATE DATABASE humanoid_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database credentials and Hugging Face API key

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

Backend will run on `http://localhost:8000`

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will run on `http://localhost:5173`

## Environment Variables

### Backend (.env)

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=humanoid_db
DB_USER=root
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=3306

HUGGINGFACE_API_KEY=your-huggingface-api-key-here
```

### Get Hugging Face API Key

1. Go to [Hugging Face](https://huggingface.co/)
2. Create an account or login
3. Go to Settings > Access Tokens
4. Create a new token with read permissions
5. Copy the token to your `.env` file

## API Endpoints

### Authentication
- `POST /api/auth/register/` - Register new user
- `POST /api/auth/login/` - Login user
- `POST /api/auth/refresh/` - Refresh JWT token
- `GET /api/auth/user/` - Get current user

### Chat
- `GET /api/chats/` - List all chats
- `POST /api/chats/` - Create new chat
- `GET /api/chats/{id}/` - Get specific chat
- `POST /api/chats/{id}/send_message/` - Send message
- `GET /api/chats/history/` - Get chat history

### Settings
- `GET /api/settings/` - Get user settings
- `PUT /api/settings/` - Update user settings

## Usage

1. **Register**: Create a new account at `/register`
2. **Login**: Sign in at `/login`
3. **Start Chatting**: 
   - Click "New Chat" to start a conversation
   - Type your message and press Send
   - View chat history in the sidebar
4. **Settings**: 
   - Toggle between Dark/Light theme
   - Logout from the settings menu

## Features in Detail

### Authentication System
- JWT-based authentication
- Secure password hashing
- Token refresh mechanism
- Protected routes

### Chat Interface
- Real-time messaging
- Message history
- Auto-scrolling to latest message
- Optimistic UI updates
- Error handling

### Theme System
- Dark/Light mode toggle
- User preference persistence
- System-wide theme application

### Responsive Design
- Mobile-first approach
- Collapsible sidebar on mobile
- Touch-friendly interface

## Development

### Backend Development

```bash
cd backend
source venv/bin/activate

# Run tests
python manage.py test

# Create new migrations
python manage.py makemigrations

# Access admin panel
# http://localhost:8000/admin
```

### Frontend Development

```bash
cd frontend

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

## Troubleshooting

### MySQL Connection Error
- Ensure MySQL is running
- Verify database credentials in `.env`
- Check database exists: `SHOW DATABASES;`

### Hugging Face API Error
- Verify API key is correct
- Check API rate limits
- Ensure model name is correct

### CORS Issues
- Backend must be running on port 8000
- Frontend must be running on port 5173
- Check CORS settings in `backend/humanoid/settings.py`

### Missing Dependencies
```bash
# Backend
pip install -r requirements.txt

# Frontend
npm install
```

## Production Deployment

### Backend
1. Set `DEBUG=False` in production
2. Configure proper `SECRET_KEY`
3. Set up Gunicorn/uWSGI
4. Configure Nginx as reverse proxy
5. Use environment variables for sensitive data

### Frontend
1. Build production bundle: `npm run build`
2. Serve static files with Nginx/Apache
3. Configure API endpoint for production backend

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the MIT License.

## Credits

- Built with ❤️ by a developer with 30+ years of experience
- Powered by Hugging Face's Qwen1.5-110B model
- UI inspired by DeepSeek AI

## Support

For issues and questions, please open an issue on the repository.

## Roadmap

- [ ] Message editing and deletion
- [ ] File attachments
- [ ] Code syntax highlighting
- [ ] Export chat history
- [ ] User profile management
- [ ] Multi-language support
