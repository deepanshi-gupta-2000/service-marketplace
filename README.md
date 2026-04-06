# Service Marketplace

Full-stack service marketplace demo project built with Django and React.

## Environment Setup

Keep all secrets and machine-specific settings in `.env` files and never commit the real files.

Backend:
- copy `backend/.env.example` to `backend/.env`
- fill in your Django secret key and database credentials

Frontend:
- copy `frontend/.env.example` to `frontend/.env`
- set `REACT_APP_API_BASE_URL` if your backend is not running on the default local address

## Demo Notes

- Authentication uses JWT access and refresh tokens.
- Payments are dummy/demo-only for portfolio purposes.
- Provider onboarding, request approval, booking lifecycle, reviews, and provider management are implemented as product flows.
