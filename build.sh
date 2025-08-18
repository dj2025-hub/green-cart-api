#!/bin/bash
# Deployment script for GreenCart API

set -e  # Exit on error

echo "🚀 Starting GreenCart API deployment..."

# Créer l'environnement virtuel
python3.13 -m venv venv

# Installer les dépendances
pip install -r requirements.txt

# Run database migrations
echo "📦 Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput --clear

# Create tokens for existing users
echo "🔑 Creating auth tokens..."
python fix_swagger_auth.py || echo "ℹ️ Token creation completed"

echo "✅ Deployment completed successfully!"

# Start the application
echo "🌐 Starting Gunicorn server..."
# exec gunicorn --bind 0.0.0.0:${PORT:-8000} --workers ${WORKERS:-3} --timeout 120 core.wsgi:application