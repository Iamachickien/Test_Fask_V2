ESP32 Control Web App
A Flask-based web application to control an ESP32 device remotely, with user authentication, password change, and user management features.
Features

Control ESP32 LED (ON/OFF) via a web interface.
View LED status history.
User authentication with password hashing.
Change password for logged-in users.
Admin panel to manage user accounts (add, update, delete).
Uses PostgreSQL for persistent data storage.
Styled with Bulma CSS for a modern, responsive UI.
Dockerized for easy deployment.

Prerequisites

Docker and Docker Compose (for local testing)
GitHub account
Railway account (for deployment)

Setup Instructions
1. Clone the Repository
git clone <your-repo-url>
cd esp32-control

2. Run Locally with Docker Compose

Ensure Docker and Docker Compose are installed.
Run the application:docker-compose up --build


Access the app at http://localhost:5000.
Default admin credentials:
Username: admin
Password: 12345678



3. Deploy to Railway

Push the code to a GitHub repository.
Create a new project on Railway (https://railway.app).
Link the project to your GitHub repository.
Add a PostgreSQL service in Railway.
Set the following environment variables in Railway:
SECRET_KEY: A random string (e.g., mysecretkey123)
DATABASE_URL: Provided by Railway's PostgreSQL service


Deploy the app. Railway will use the Dockerfile to build and run.
Access the deployed URL provided by Railway.

4. ESP32 Integration

Configure your ESP32 to send POST requests to /report-status with JSON payload:{"status": "ON"}


Poll /get-command to retrieve commands (ON or OFF).

Routes

/: Main page to control ESP32 (requires login).
/login: Login page.
/logout: Log out.
/history: View LED status history.
/change-password: Change user password.
/manage-users: Manage user accounts (admin only).
/set-command/<cmd>: Set ESP32 command (ON or OFF).
/get-command: Get current command.
/report-status: ESP32 reports status (POST).
/get-real-status: Get current ESP32 status.

File Structure
esp32-control/
├── app.py                # Main Flask application
├── templates/            # HTML templates with Bulma CSS
│   ├── index.html
│   ├── login.html
│   ├── history.html
│   ├── change_password.html
│   ├── manage_users.html
├── static/               # Empty (uses Bulma CDN)
├── requirements.txt      # Python dependencies
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Docker Compose configuration
├── README.md             # Project documentation

Notes

Passwords are hashed using bcrypt for security.
History is limited to 100 records to prevent database overflow.
Admin users (role='admin') can manage other accounts.
Deployed app uses Railway's PostgreSQL for persistent storage.

