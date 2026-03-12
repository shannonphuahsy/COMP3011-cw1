# COMP3011-cw1
# Geospatial Risk Analysis for Public WiFi Networks

This API provides safety analytics for public WiFi hotspots, including:
- Crime risk within 500m
- Security classification (Open/WPA2/WPA3)
- Device density exposure
- BSSID-triggered safety assessment
- User-reported incidents (CRUD)

## Installation
pip install fastapi uvicorn asyncpg python-dotenv

## Running
uvicorn app.main:app --reload

## Environment
Copy `.env.example` → `.env`
Set `DATABASE_URL`

## API Docs
Available at `/docs`

## Structure
