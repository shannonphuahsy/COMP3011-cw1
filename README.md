# COMP3011‑cw1
***

## 1. Project Title

## **Geospatial Risk Analysis for Public WiFi Networks**

Real‑time hotspot intelligence, cyber‑exposure scoring, and risk analytics.

***

## 2. Table of Contents
### I. Overview
### II. Live Documentation
### III. Key Features
### IV. Design Decisions & Tech Stack
### V. System Architecture
### VI. Setup Instructions
### VII. Database Schema
### VIII. Authentication & Authorization
### IX. API Endpoints
#### - Hotspots
#### - Assessments
#### - Analytics
#### - Incidents
#### - Internal Admin
### X. Cyber Exposure Score
### XI. Caching Strategy
### XII. Rate Limiting
### XIII. Testing
### XIV. Project Structure
### XV. Design Trade‑offs & Challenges
### XVI. Limitations
### XVII. Future Work
### XVIII. References
***
## 3. Overview

This project implements a **Geospatial Risk Analysis API** for public Wi‑Fi networks.  
It is capable of:

*   Analysing Wi‑Fi hotspot risk using geospatial crime data
*   Assessing network security posture (Open/WPA2/WPA3)
*   Detecting SSID spoofing likelihood
*   Collecting and analysing user‑reported incidents
*   Resolving hotspot identity via BSSID
*   Computing a unified **0–100 Cyber Exposure Score**
*   Providing both public endpoints and admin‑restricted operations

### **Project Structure**

    app/
      ├── core/
      │     ├── __init__.py
      │     ├── config.py
      │     └── limiter.py
      ├── data/
      │     └── clean_data/
      │           ├── crime_hotspot_cities_clean.csv
      │           ├── dim_postcode.csv
      │           ├── lsoa_2021_locations_minimal.csv
      │           ├── lsoa_context_2021.csv
      │           ├── lsoa_population_summary_2021.csv
      │           └── wifi_hotspots_clean.csv
      │     └── crime_raw
      │           └── ...
      │     ├── LSOA.xlsx
      │     └── LSOA (2).xlsx
      ├── db/ 
      │     ├── __init__.py
      │     ├── bootstrap_all.sql
      │     ├── database.py
      │     └── models.py
      ├── routers/   
      │     ├── __init__.py
      │     ├── analytics.py
      │     ├── assessments.py
      │     ├── auth.py
      │     ├── incidents.py
      │     ├── internal.py
      │     └── wifi_networks.py
      ├── schemas/   
      │     ├── __init__.py 
      │     ├── analytics.py
      │     ├── assessment.py
      │     ├── auth.py
      │     ├── hotspot.py
      │     └── incident.py
      ├── services/ 
      │     ├── __init__.py 
      │     ├── api_key.py
      │     ├── auth_utils.py
      │     ├── dependencies.py
      │     ├── jwt_service.py
      │     └── scoring.py
      ├── tests/ 
      │     ├── __init__.py 
      │     ├── conftest.py
      │     ├── test_analytics.py
      │     ├── test_assessments.py
      │     ├── test_auth.py
      │     ├── test_incidents_crud.py
      │     ├── test_internal.py
      │     ├── test_openapi_contract.py
      │     ├── test_system.py
      │     └── test_wifi_patch.py
      ├── __init__.py
      ├── cache.py                
      ├── main.py
    scripts/
      ├── clean_merge_lsoa.py
      ├── clean_ons_dataset.py 
      ├── merge_crime_datasets.py
      └── merge_wifi_datasets.py
    .coverage
    .env
    .env.example    
    .gitattributes
    .gitignore
    pytest.ini
    README.md  
    requirements.txt 
    requirements-dev.txt 
***

## 4. Live Documentation

The API exposes fully interactive documentation via FastAPI:

*   **Swagger UI**  
    `http://localhost:8000/docs`

*   **ReDoc**  
    `http://localhost:8000/redoc`

*   **OpenAPI Spec**  
    `http://localhost:8000/openapi.json`

***

## 5. Key Features

*   **Wi‑Fi hotspot browsing & search** (name, city, postcode)
*   **Geospatial analysis** (nearest, near radius, KNN)
*   **Security posture evaluation** (Open/WPA2/WPA3)
*   **User‑reported incidents (CRUD, JWT‑protected)**
*   **SSID spoofing classification**
*   **Crime analytics (12‑month, 500m)**
*   **Cyber Exposure Score (0–100)**
*   **Caching layer** for hotspot details
*   **API key–secured internal endpoints**
*   **Comprehensive pytest suite**
*   **Rate‑limited assessment endpoints**

***

## 6. Design Decisions & Tech Stack

### **Programming Language**

*   **Python 3.11** – modern async features, strong libraries.

### **Tech Stack**

| **Technology**           | **Purpose**                  | **Justification (Short)**                                                                                             |
| ------------------------ | ---------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| **FastAPI**              | Web framework                | High‑performance async framework with automatic OpenAPI docs and clean structure.                                     |
| **PostgreSQL + PostGIS** | Database & geospatial engine | Provides reliable relational storage and powerful geospatial functions needed for crime radius and proximity queries. |
| **asyncpg**              | Async database driver        | Extremely fast, lightweight, and integrates naturally with FastAPI’s async execution.                                 |
| **Pydantic v2**          | Data validation              | Ensures strict, efficient validation and produces clean, auto‑documented API schemas.                                 |


### **Database**

**PostgreSQL 15 + PostGIS**  
Chosen due to:

*   Geospatial types (`geography`, `geometry`)
*   Efficient spatial indexing (GiST, SP‑GiST)
*   Advanced functions (`ST_DWithin`, KNN-distance, clustering)

### **DB Access Layer**

**asyncpg**

*   Very fast
*   Full async support
*   Lower overhead than SQLAlchemy ORM

### **Caching**

*   Redis originally planned
*   Disabled for Windows compatibility
*   Cache adapter gracefully no‑ops when Redis is unavailable

### **Authentication**

*   JWT for user accounts
*   API key for admin endpoints

### **Rate Limiting**

*   SlowAPI for IP‑based rate control

### **Testing**

*   pytest
*   httpx (sync + async clients)
*   Database cleanup for deterministic results

### **Test Coverage**

**1. Authentication Tests (`test_auth.py`)**  
Validate user signup, login, and JWT issuance. Ensures secure access to protected routes.

**2. Incident CRUD Tests (`test_incidents_crud.py`)**  
Verify creation, reading, updating, and deletion of incidents using JWT authentication.

**3. Hotspot Update Tests (`test_wifi_patch.py`)**  
Check admin‑only PATCH operations for hotspot status and security mode, including proper permission checks.

**4. Assessment Tests (`test_assessments.py`)**  
Validate structure and fields of the final BSSID‑based safety assessment, including score, verdict, and context.

**5. Analytics Tests (`test_analytics.py`)**  
Ensure geospatial queries (nearby, ranked, crime-by-hotspot) return correct results and ordering.

**6. Internal Admin Tests (`test_internal.py`)**  
Confirm API‑key protection and that system stats/version endpoints operate correctly.

**7. OpenAPI Contract Test (`test_openapi_contract.py`)**  
Checks that required paths exist and the API specification remains stable.

**8. Health Check (`test_system.py`)**  
Confirms the app starts and responds correctly.

### **Deterministic Behaviour**

*   Temporary test users are cleaned before each test.
*   Hotspot updates use backup/restore fixtures.
*   Caching is bypassed during tests to avoid stale data.

***

## 7. System Architecture

Below is an ASCII diagram to ensure **GitHub renders it correctly**:

                        ┌───────────────────────┐
                        │      API Client       │
                        │  (Browser / Mobile)   │
                        └──────────┬────────────┘
                                   │  HTTPS
                                   ▼
                       ┌─────────────────────────┐
                       │        FastAPI           │
                       │  Routers / Services      │
                       └──────────┬──────────────┘
                                  │
             ┌────────────────────┼────────────────────┐
             │                    │                    │
             ▼                    ▼                    ▼
    ┌────────────────┐   ┌──────────────────┐   ┌───────────────────┐
    │  JWT Service   │   │   Cache Layer    │   │    PostGIS DB     │
    │ Token signing  │   │ Redis / No-op    │   │  Hotspots, Crime  │
    └────────────────┘   └──────────────────┘   │ Incidents, BSSIDs │
                                                 └───────────────────┘

***

## 8. Setup Instructions

### **Prerequisites**

*   Python **3.11+**
*   PostgreSQL **15** with **PostGIS**
*   Optional: Redis (disabled by default on Windows)

### **Install dependencies**

    pip install -r requirements.txt

### **Run the server**

    uvicorn app.main:app --reload

### **Run tests**

    pytest -q

### **Environment variables**

Copy `.env.example` → `.env` and set:

    DATABASE_URL=
    JWT_SECRET=
    API_KEY=

***

## 9. Database Schema

The system uses a clean, normalised schema:

### **Tables**

*   `core_wifi_hotspot`: Raw hotspot rows
*   `api_wifi_hotspot_risk`: Enriched hotspot + geospatial fields
*   `api_wifi_bssid_map`: Maps BSSID → wifi\_id
*   `api_user_incidents`: User‑reported incidents
*   `core_crime`: Geospatial crime dataset

### **Relationships**

*   Hotspot → Crime is computed via geospatial radius, not FK
*   Hotspot → Incidents uses `wifi_id`
*   BSSID → Hotspot uses 1:N mapping

***

## 10. Authentication & Authorization

### **JWT Endpoints**

*   **POST `/auth/signup`**
*   **POST `/auth/login`**

Header:

    Authorization: Bearer <token>

### **Protected Endpoints**

*   Incidents CRUD
*   Hotspot updates (`status`, `security`)

### **Internal Admin (API key)**

*   `/internal/stats`
*   `/internal/version`

Header:

    X-API-Key: <your key>

***

## 11. API Endpoints

Create a table in your final submission (example):

### Hotspots

*   `/hotspots/`
*   `/hotspots/{wifi_id}`
*   `/hotspots/search`
*   `/hotspots/nearest`
*   `/hotspots/near`

### Assessments

*   `/assessments/security`
*   `/assessments/crime`
*   `/assessments/incidents`
*   `/assessments/ssid_risk`
*   `/assessments/environment`
*   `/assessments/safety` (final composite)

### Analytics

*   `/analytics/nearby`
*   `/analytics/ranked`
*   `/analytics/crime/{wifi_id}`

### Incidents (JWT)

*   Create, update, delete, list

### Internal Admin (API key)

*   `/internal/stats`
*   `/internal/version`

***

## 12. Cyber Exposure Score

A single **0–100** metric summarising hotspot safety.

### 🟢 **0–30: Low Risk**

*   WPA2/WPA3
*   Low crime
*   No suspicious incidents

### 🟡 **31–60: Medium Risk**

*   Older encryption
*   Moderate crime
*   Some suspicious activity

### 🔴 **61–100: High Risk**

*   Open Wi‑Fi
*   High crime
*   Spoofing or phishing reports

### Score is computed from:

*   Security mode
*   Crime last 12 months
*   Incident history
*   SSID spoofing likelihood
*   Environmental status

***

## 13. Caching Strategy

*   `/hotspots/{wifi_id}` cached for 300 seconds
*   Redis optional
*   Automatic fallback to no‑cache on unsupported platforms
*   Prevents repeated PostGIS calls

***

## 14. Rate Limiting

Assessment endpoints are protected:

    30 requests / minute per IP

This prevents automated hotspot scanning.

***

## 15. Testing

The test suite verifies:

*   JWT authentication
*   API key authentication
*   Hotspot search & geospatial endpoints
*   Incidents CRUD
*   Safety assessment format
*   Internal diagnostics

Run with:

    pytest -q

Fixtures include DB cleanup to prevent duplicate user errors.

***

## 16. Project Structure

    app/
      routers/
      services/
      db/
      schemas/
      cache.py
      main.py
    tests/
      test_auth.py
      test_incidents_crud.py
      test_wifi_patch.py
      ...

***

## 17. Design Trade‑offs & Challenges

*   Redis removed for Windows compatibility
*   Materialized view refresh removed for performance
*   Score model simplified due to coursework constraints
*   PostGIS operations tuned for speed, not ultimate accuracy

***

## 18. Limitations

*   Static crime dataset
*   No frontend or visual dashboard
*   Score is heuristic, not ML‑driven
*   No real‑time threat feeds

***

## 19. Future Work

*   Live cyber‑threat intelligence integration
*   ML anomaly detection
*   GeoJSON export endpoints
*   Public dashboard UI
*   Automated materialized view pipeline

***

## 20. References

### Documentation

*   FastAPI — <https://fastapi.tiangolo.com/>
*   PostgreSQL — <https://www.postgresql.org/docs/>
*   PostGIS — <https://postgis.net/documentation/>
*   asyncpg — <https://magicstack.github.io/asyncpg/current/>

### Security References

*   NCSC Public Wi‑Fi Guidance
*   OWASP Mobile & Wi‑Fi Security
*   RFC 7519 (JWT)

### Dataset Sources

*   UK Police Crime Data
*   Council Wi‑Fi Open Datasets

### Tech Stack

*   Pydantic v2
*   SlowAPI
*   httpx / pytest

***

If you want, I can **generate a PDF** of this README or produce a **short summary version for your coursework report** — just tell me!
