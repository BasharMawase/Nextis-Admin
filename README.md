# Nextis Admin Dashboard

Nextis is a powerful Point of Sale (POS) and administrative management system designed for restaurants, coffee shops, and retail businesses. This repository contains the source code for the Nextis Admin Dashboard.

## Features

*   **Client Management**: Add, edit, delete, and view detailed client information.
*   **Data Analysis**: Visual analytics for client distribution by location.
*   **File Uploads**: Bulk import client data via Excel/CSV files.
*   **Search**: Advanced search functionality to quickly find clients.
*   **Portfolio Management**: Manage and showcase project portfolios.
*   **Contact Messages**: View and manage messages from the "Contact Us" form.
*   **Role-Based Access**: Secure login for administrators.

## Tech Stack

*   **Backend**: Python (Flask)
*   **Database**: SQLite
*   **Frontend**: HTML, CSS, JavaScript
*   **Data Processing**: Pandas

## Local Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/BasharMawase/Nextis-Admin.git
    cd Nextis-Admin
    ```

2.  **Create a virtual environment (optional but recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the application:**
    ```bash
    python app.py
    ```
    The application will behave running at `http://127.0.0.1:5001`.

## Deployment

For detailed instructions on how to deploy this application to the internet, please refer to [DEPLOYMENT.md](DEPLOYMENT.md).
