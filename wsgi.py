"""Gunicorn entrypoint: gunicorn -w 3 -b 127.0.0.1:5200 wsgi:app"""
from app import create_app

app = create_app()
