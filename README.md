# Taxi Service API
## Description
Taxi Service API is a backend solution for managing a taxi service. 
It allows clients to request and pay for taxi rides. Regular users can apply to become drivers, 
and admins can review and approve these applications. Drivers can add their cars, 
update the status of rides, and view active orders. 
Payments are required before drivers can accept ride requests. Users can rate drivers,
and admins have control over cities and can manage driver applications. 
Notifications are sent via Telegram for driver applications, ride completion, order creation, 
successful payments, and payment cancellations.

## Features
- Users can order and pay for taxis.
- Drivers can apply to be verified, manage their cars, and accept orders.
- Admins can add new cities and manage driver applications.
- Notifications through Telegram for key events.
- Drivers can update the status of their rides and receive ratings from users.
- Payment integration with Stripe API.
- Daily revenue notifications to Telegram via scheduled tasks.
## Technologies Used
- Django
- Django Rest Framework (DRF)
- PostgreSQL
- Docker
- Celery
- Redis
- Stripe API
- JWT for authentication
## Setup and Installation
- Clone the repository.
- Copy environment variables from .env.sample to a new .env file and update the values.
- Build and start the services with Docker:
```bash
docker compose up --build
```
The application should now be running and accessible.
## API Documentation
The project includes API documentation powered by Swagger. To access it, go to:

```/api/v1/doc/swagger/```
## Key Endpoints
### Payment

- GET api/v1/payment/ - View your payments (admins can see all payments).
### Cars

- GET api/v1/taxi/cars/ - Drivers can view their cars (admins can see all).
- POST api/v1/taxi/cars/ - Add a new car.
### Cities

- GET api/v1/cities/ - View all cities.
- POST api/v1/cities/ - Admins can add new cities.
### Driver Applications

- GET api/v1/driver_application/ - View your applications (admins can see all).
- POST api/v1/driver_application/ - Apply to become a driver.
- GET api/v1/taxi/driver_application/{id}/apply/ - Admin can approve an application.
- GET api/v1/taxi/driver_application/{id}/reject/ - Admin can reject an application.
### Orders

- GET api/v1/orders - View your orders (admins see all, drivers see active).
- POST api/v1/orders - Create a new order.
### Rides

- GET api/v1/rides/ - View your rides (admins see all rides).
- GET api/v1/taxi/rides/{id}/finished/ - Mark a ride as finished.
- GET api/v1/taxi/rides/{id}/in_process/ - Mark a ride as in process.
- POST api/v1/taxi/rides/{id}/rate_ride/ - Rate a ride.
### User

- GET api/v1/user/me/ - View your profile.
- POST api/v1/user/register/ - Register a new user.
- POST api/v1/user/token/ - Get a JWT token.
- POST api/v1/user/token/refresh/ - Refresh a token.
### Authentication
JWT is used for user authentication. To obtain a token:

- Register a user: POST api/v1/user/register/
- Login: POST api/v1/user/token/
- Refresh token: POST api/v1/user/token/refresh/
## Running Tests
To run tests, use the following command:

```bash
python manage.py test
```
To check code coverage:

```bash
coverage manage.py test
```
```bash
coverage report
```
The project has 96% test coverage.

## Scheduled Tasks
There is a default scheduled task that sends a daily revenue report to Telegram at 23:59. To configure this, create a superuser and set up the task in the admin panel.