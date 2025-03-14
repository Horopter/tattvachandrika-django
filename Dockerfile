# Use an official Python runtime as the base image
FROM python:3.12-slim

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies required for building psycopg2 and other packages
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file and install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the Django project code
COPY . /app/

# Collect static files (if applicable)
RUN python manage.py collectstatic --noinput

# Expose the Django port
EXPOSE 8000

# Run migrations and start Gunicorn (adjust the WSGI path as needed)
CMD ["gunicorn", "magazine.wsgi:application", "--bind", "0.0.0.0:8000", "--timeout", "300", "--log-file", "-"]

