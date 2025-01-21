# Django Real-Time Chat Application

A feature-rich real-time chat application built with Django and Channels, supporting WebSocket connections for instant messaging.

## Features

- Real-time messaging using WebSocket connections
- Multiple chat rooms support
- File sharing capabilities
- Message read status
- Message editing and deletion
- Reply to messages
- User authentication
- Modern and responsive UI

## Tech Stack

- **Backend**: Django 4.2+
- **WebSocket**: Django Channels 4.0+
- **Database**: PostgreSQL (Production), SQLite (Development)
- **Cache & WebSocket Backend**: Redis
- **Frontend**: HTML, CSS, JavaScript
- **Deployment**: Render.com

## Local Development Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd chatdb
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Run migrations:
```bash
python manage.py migrate
```

6. Create a superuser:
```bash
python manage.py createsuperuser
```

7. Run the development server:
```bash
python manage.py runserver
```

Visit http://localhost:8000 to access the application.

## Production Deployment

This application is configured for deployment on Render.com with the following services:
- Web Service (Django application)
- PostgreSQL Database
- Redis Instance

The `render.yaml` file contains all necessary configuration for deployment.

### Deployment Steps

1. Push your code to a Git repository
2. Create a Render account
3. Create a new "Blueprint" instance
4. Connect your repository
5. Render will automatically configure the services

## Environment Variables

Required environment variables in production:
- `DJANGO_SECRET_KEY`: Django secret key
- `DATABASE_URL`: PostgreSQL database URL (provided by Render)
- `REDIS_URL`: Redis connection URL (provided by Render)
- `DJANGO_DEBUG`: Set to 'False' in production

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
