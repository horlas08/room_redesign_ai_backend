# Django Backend: Auth, MySQL, OTP, Room Redesign (OpenAI)

## Features
- Email/password register and login
- Email OTP verification and password reset (6-digit, 5 min expiry)
- JWT auth with access/refresh
- MySQL database
- Upload room image, request redesign with style
- Generates redesign via OpenAI Images API (`gpt-image-1`)
- History of redesigns per user

## Tech
- Python 3.10+
- Django 4+
- DRF
- MySQL
- Pillow
- python-dotenv
- openai SDK v1

## Setup
- Create and activate a virtualenv.
- Install deps:
```
pip install -r requirements.txt
```
- Create `.env` using the example below.
- Make migrations and runserver:
```
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

## .env Example
```
SECRET_KEY=change-me
DEBUG=True
ALLOWED_HOSTS=*

OPENAI_API_KEY=sk-...

DB_NAME=your_db
DB_USER=your_user
DB_PASSWORD=your_password
DB_HOST=127.0.0.1
DB_PORT=3306

EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your@email
EMAIL_HOST_PASSWORD=yourpass
DEFAULT_FROM_EMAIL=Your App <no-reply@example.com>
```

## Endpoints
- Auth
  - POST `/auth/register/`
  - POST `/auth/verify-otp/`
  - POST `/auth/login/`
  - POST `/auth/forgot-password/`
  - POST `/auth/reset-password/`
- AI
  - POST `/api/redesign-room/` (multipart: `original_image`, `style_choice`)
  - GET `/api/history/`

## Notes
- Login expects `email` and `password` in body and returns `access` and `refresh`.
- Images are generated from prompts; the uploaded image is stored for history but currently not passed into the image model (OpenAI Images API does not accept reference images in `generate`).
- To return actual image files instead of base64, add storage or download the generated image and save to `result_image`.
