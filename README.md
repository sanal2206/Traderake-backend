
# Traderake Backend

This is the backend for the Traderake application built using Django and Django REST Framework with JWT authentication.

## Features

- User registration and login using JWT tokens
- Token refresh and logout functionality
- PostgreSQL as the database
- Custom User model (`CustomUser`)
- Watchlist API (add/remove/list)
- Real-time stock data API integration
- Model support: `Stock`, `Indices`, `Watchlist`
- DRF-powered API endpoints
- Authenticated API access with token
- Modular app structure (`accounts`, etc.)
- Postman collection for testing

## Setup Instructions

1. Clone the repository:
    ```bash
    git clone https://github.com/sanal2206/Traderake-backend.git
    ```

2. Create and activate a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # For Linux/Mac
    venv\Scripts\activate   # For Windows
    ```

3. Install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4. Set up the database and run migrations:
    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```

5. Run the development server:
    ```bash
    python manage.py runserver
    ```



## License

This project is licensed under the MIT License.
