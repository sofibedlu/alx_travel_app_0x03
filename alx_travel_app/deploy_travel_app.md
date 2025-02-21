# ALX Travel App Production Deployment Guide

This document provides step-by-step instructions for deploying the ALX Travel App in production.

---

## 1. System Update & Pre-requisites

1. Update your system and install required packages:
   ```sh
   sudo apt update && sudo apt upgrade -y
   sudo apt install -y build-essential python3-dev python3-venv libpq-dev nginx git

## 2. Install & Configure Database (MySQL)

1. Install MySQL server and client:
   ```sh
   sudo apt update
   sudo apt install -y mysql-server mysql-client libmysqlclient-dev
   sudo mysql_secure_installation

2. Log in to MySQL:
   ```sh
   sudo mysql -u root -p

3. Create a database and user:
   ```sql
   CREATE DATABASE alx_travel_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER 'alx_travel_user'@'localhost' IDENTIFIED BY 'strong_password';
   GRANT ALL PRIVILEGES ON alx_travel_db.* TO 'alx_travel_user'@'localhost';
   FLUSH PRIVILEGES;
   EXIT;

4. Update Django database settings in settings.py:
   ```python
   DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST', default='localhost'),
        'PORT': env('DB_PORT', default='3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

## 3. Install RabbitMQ (Celery Broker)

1. Install and start RabbitMQ:
   ```sh
   sudo apt install -y erlang rabbitmq-server
   sudo systemctl enable rabbitmq-server
   sudo systemctl start rabbitmq-server

## 4. Application Setup

1. Clone the repository and set up the project directory:
   ```sh
   mkdir /var/www && cd /var/www
   sudo chown -R ubuntu:ubuntu /var/www
   git clone your-repo-url alx_travel_app
   cd alx_travel_app

2. Create a virtual environment and install requirements:
   ```sh
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirement.txt

3. (Note: Before installing mysqlclient, you may need to install additional packages:)
   ```sh
   sudo apt install python3-dev default-libmysqlclient-dev build-essential pkg-config -y
   pip install mysqlclient

4. Install Gunicorn:
   ```sh
   pip install gunicorn
   gunicorn --version  # verify installation

## 5. Configure Production Environment

1. Create a .env file in your project root (e.g., alx_travel_app/.env):
   ```ini
   DEBUG=0
   ALLOWED_HOSTS=your-domain.com,server-ip
   DB_NAME=alx_travel_db
   DB_USER=alx_travel_user
   DB_PASSWORD=strong_password
   DB_HOST=localhost
   DB_PORT=3306
   CELERY_BROKER_URL=amqp://localhost
 
   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   EMAIL_HOST=your-smtp-server.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=1
   EMAIL_HOST_USER=your-email@domain.com
   EMAIL_HOST_PASSWORD=your-email-password

   CHAPA_SECRET_KEY=your-chapa-secret-key

2. Run database migrations and collect static files:
   ```sh
   python manage.py migrate
   python manage.py collectstatic --noinput

## 6. Configure Gunicorn as a Systemd Service

1. Create a service file at /etc/systemd/system/gunicorn.service:
   ```ini
   [Unit]
   Description=gunicorn daemon
   After=network.target

   [Service]
   User=ubuntu
   Group=ubuntu
   WorkingDirectory=/var/www/alx_travel_app
   ExecStart=/var/www/alx_travel_app/venv/bin/gunicorn --access-logfile - --workers 3 --bind unix:/var/www/alx_travel_app/alx_travel_app.sock alx_travel_app.wsgi:application

   [Install]
   WantedBy=multi-user.target

2. Start and enable Gunicorn:
   ```sh
   sudo systemctl daemon-reload
   sudo systemctl start gunicorn
   sudo systemctl enable gunicorn

## 7. Configure Nginx

1. Create an Nginx configuration file at /etc/nginx/sites-available/alx_travel_app:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com www.your-domain.com;
    
       location = /favicon.ico { access_log off; log_not_found off; }

       location /static/ {
           alias /var/www/alx_travel_app/staticfiles/;
           expires 30d;
           access_log off;
       }

       location / {
           include proxy_params;
           proxy_pass http://unix:/var/www/alx_travel_app/alx_travel_app.sock;
           proxy_set_header X-Forwarded-Proto $scheme;
      }
   }

2. Enable the site and restart Nginx:
   ```sh
   sudo ln -s /etc/nginx/sites-available/alx_travel_app /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx

## 8. Enable SSL with Certbot

1. Install Certbot and its Nginx plugin:
   ```sh
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com -d www.your-domain.com

## 9. Configure Celery

1. Create a service file for Celery at /etc/systemd/system/celery.service:
   ```ini
   [Unit]
   Description=Celery Service
   After=network.target

   [Service]
   User=ubuntu
   Group=ubuntu
   WorkingDirectory=/var/www/alx_travel_app
   EnvironmentFile=/var/www/alx_travel_app/.env
   ExecStart=/var/www/alx_travel_app/venv/bin/celery -A alx_travel_app worker --loglevel=info
   Restart=always

   [Install]
   WantedBy=multi-user.target

2. Start and enable Celery:
   ```sh
   sudo systemctl daemon-reload
   sudo systemctl start celery
   sudo systemctl enable celery

## 10. Enable Swagger Documentation

1. In your settings.py, configure allowed CORS origins and Swagger settings:
   ```python
   CORS_ALLOWED_ORIGINS = [
    "https://your-domain.com",
    # Add other allowed origins if needed
   ]

   SWAGGER_SETTINGS = {
       'SECURITY_DEFINITIONS': {
           'Basic': {
               'type': 'basic'
           }
       },
       'USE_SESSION_AUTH': False,
   }

## 11. Final Checks

1. Firewall Rules:
   ```sh
   sudo ufw allow 80
   sudo ufw allow 443
   sudo ufw allow ssh
   sudo ufw enable

2. Test Services:
   ```sh
   sudo systemctl status gunicorn
   sudo systemctl status nginx
   sudo systemctl status celery

3. To view logs:
   ```sh
   journalctl -u gunicorn -f
   journalctl -u celery -f

4. Manual Test:
- Test the Django application manually within your virtual environment:
   ```sh
   source /var/www/alx_travel_app/venv/bin/activate
   gunicorn --bind 0.0.0.0:8000 alx_travel_app.wsgi:application

- And test the socket file:
  ```sh
  curl --unix-socket /var/www/alx_travel_app/alx_travel_app.sock http://localhost

## 12. Troubleshooting: Static Files Issue

1. Update Django Settings:
- In settings.py:
   ```ini
   STATIC_URL = '/static/'
   STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
   STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
   DEBUG = False
   ALLOWED_HOSTS = ['your-domain.com', 'localhost']

2. Collect Static Files:
   ```sh
   python manage.py collectstatic --noinput

3. Configure Nginx:
- Ensure the alias in your Nginx config matches your STATIC_ROOT.

4. Set Correct Permissions:
   ```sh
   sudo chown -R www-data:www-data /var/www/alx_travel_app/staticfiles/
   sudo chmod -R 755 /var/www/alx_travel_app/staticfiles/

5. Reload Nginx:
   ```sh
   sudo nginx -t
   sudo systemctl reload nginx

- By following these steps, you will have the ALX Travel App running securely in a production environment. Adjust domain names, file paths, and credentials as needed for your setup.
- Feel free to adjust the content as necessary for your specific deployment requirements.

