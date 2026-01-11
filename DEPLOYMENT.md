# Deployment Guide for Nextis Admin

This guide provides instructions for deploying the Nextis Admin application to the internet. We recommend using a Platform as a Service (PaaS) like **Render** for the easiest setup, or a **VPS** (Virtual Private Server) for more control.

---

## Option 1: Deploying on Render (Recommended for Beginners)

Render is a cloud platform that makes it easy to deploy web apps.

1.  **Sign Up**: Create an account at [render.com](https://render.com).
2.  **Connect GitHub**: detailed in the "New Web Service" flow.
3.  **Create New Web Service**:
    *   Click "New +" and select "Web Service".
    *   Connect your `Nextis-Admin` repository.
4.  **Configure Settings**:
    *   **Name**: `nextis-admin` (or your preferred name)
    *   **Region**: Frankfurt (or closest to you/your users)
    *   **Branch**: `main`
    *   **Runtime**: `Python 3`
    *   **Build Command**: `pip install -r requirements.txt`
    *   **Start Command**: `gunicorn app:app` (Note: You may need to add `gunicorn` to your `requirements.txt` first).
5.  **Environment Variables**:
    *   Add `PYTHON_VERSION` with value `3.9.13` (or your local version).
    *   Add `SECRET_KEY` with a secure random string.
6.  **Deploy**: Click "Create Web Service". Render will build and deploy your app.

**Important Note for SQLite**: Render's free tier has an ephemeral filesystem, meaning your SQLite database (`nextis.db`) will be reset every time the app restarts. For production, you should upgrade to a persistent disk or switch to PostgreSQL (Render provides managed PostgreSQL).

---

## Option 2: Deploying on a VPS (DigitalOcean, Linode, etc.)

This method gives you a Linux server where you have full control.

### Prerequisites
*   A VPS (Ubuntu 20.04/22.04 recommended).
*   Domain name pointing to your VPS IP.

### Steps

1.  **SSH into your server**:
    ```bash
    ssh root@your_server_ip
    ```

2.  **Update and Install Dependencies**:
    ```bash
    sudo apt update && sudo apt upgrade -y
    sudo apt install python3-pip python3-venv nginx -y
    ```

3.  **Clone the Repository**:
    ```bash
    cd /var/www
    git clone https://github.com/BasharMawase/Nextis-Admin.git nextis
    cd nextis
    ```

4.  **Setup Virtual Environment**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    pip install gunicorn
    ```

5.  **Configure Gunicorn (Application Server)**:
    Create a systemd service file:
    ```bash
    sudo nano /etc/systemd/system/nextis.service
    ```
    Paste the following (adjust paths/users if necessary):
    ```ini
    [Unit]
    Description=Gunicorn instance to serve Nextis
    After=network.target

    [Service]
    User=root
    Group=www-data
    WorkingDirectory=/var/www/nextis
    Environment="PATH=/var/www/nextis/venv/bin"
    ExecStart=/var/www/nextis/venv/bin/gunicorn --workers 3 --bind unix:nextis.sock -m 007 app:app

    [Install]
    WantedBy=multi-user.target
    ```
    Start and enable the service:
    ```bash
    sudo systemctl start nextis
    sudo systemctl enable nextis
    ```

6.  **Configure Nginx (Web Server)**:
    Create a new site configuration:
    ```bash
    sudo nano /etc/nginx/sites-available/nextis
    ```
    Paste the following:
    ```nginx
    server {
        listen 80;
        server_name your_domain.com www.your_domain.com;

        location / {
            include proxy_params;
            proxy_pass http://unix:/var/www/nextis/nextis.sock;
        }

        location /static {
            alias /var/www/nextis/static;
        }
    }
    ```
    Enable the site:
    ```bash
    sudo ln -s /etc/nginx/sites-available/nextis /etc/nginx/sites-enabled
    sudo nginx -t
    sudo systemctl restart nginx
    ```

7.  **SSL (HTTPS) with Certbot**:
    ```bash
    sudo apt install certbot python3-certbot-nginx
    sudo certbot --nginx -d your_domain.com
    ```

You're done! Your app should be live at `https://your_domain.com`.
