# COMP3011‑cw1
***
# Geospatial Risk Analysis for Public WiFi Networks

*A Cyber‑Exposure Scoring & Hotspot Intelligence API*

***

#  Table of Contents

*   1.  Project Title
*   2.  Overview
*   3.  Live Documentation
*   4.  Key Features
*   5.  Design Decisions & Tech Stack
*   6.  Deployment
*   7.  Setup & Installation
*   8.  Database Schema
*   9.  Data Sources & Justification
*   10. System Architecture
*   11. Authentication & Authorization
*   12. How to Use the API
*   13. API Endpoints
*   14. Cyber Exposure Score
*   15. Caching Strategy
*   16. Rate Limiting
*   17. Testing
*   18. Error Codes & Debugging Guide
*   19. Project Structure
*   20. Design Trade-offs & Challenges
*   21. Limitations
*   22. Future Work
*   23. References

***

# 1. Project Title

# **Geospatial Risk Analysis for Public WiFi Networks**

Real‑time hotspot intelligence, cyber‑exposure scoring, and risk analytics.

***

# 2. Overview


This project implements a **Geospatial Risk Analysis API** for public Wi‑Fi networks.  
It is capable of:

*   Analysing Wi‑Fi hotspot risk using geospatial crime data
*   Assessing network security posture (Open/WPA2/WPA3)
*   Detecting SSID spoofing likelihood
*   Collecting and analysing user‑reported incidents
*   Computing a unified **0–100 Cyber Exposure Score**
*   Providing both public endpoints and admin‑restricted operations

### **Project Structure**

    app/
      ├── core/
      │     ├── __init__.py
      │     ├── config.py
      │     └── limiter.py
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
    .env
    .env.example    
    .gitattributes
    .gitignore
    pytest.ini
    README.md  
    requirements.txt 
    requirements-dev.txt 
***

# 3. Live Documentation

*   **Swagger UI:** <http://localhost:8000/docs>
*   **ReDoc:** <http://localhost:8000/redoc>
*   **OpenAPI Spec:** <http://localhost:8000/openapi.json>

***

# 4. Key Features
*   **Wi‑Fi hotspot browsing & search** (name, city, postcode)
*   **Geospatial analysis** (nearest, near radius, KNN)
*   **Security posture evaluation** (Open/WPA2/WPA3)
*   **User‑reported incidents (CRUD, JWT‑protected)**
*   **SSID spoofing classification**
*   **Crime analytics (12‑month, 500m)**
*   **Cyber Exposure Score (0–100)**
*   **API key–secured internal endpoints**
*   **Comprehensive pytest suite**
*   **Rate‑limited assessment endpoints**
***

# 5. Design Decisions & Tech Stack

### **Programming Language**

*   **Python 3.11** – modern async features, strong libraries.

### **Tech Stack**

| **Technology**           | **Purpose**                  | **Justification**                                                                                             |
| ------------------------ | ---------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| **FastAPI**              | Web framework                | High‑performance async framework with automatic OpenAPI docs and clean structure.                                     |
| **PostgreSQL + PostGIS** | Database & geospatial engine | Provides reliable relational storage and powerful geospatial functions needed for crime radius and proximity queries. |
| **asyncpg**              | Async database driver        | Extremely fast, lightweight, and integrates naturally with FastAPI’s async execution.                                 |
| **Pydantic v2**          | Data validation              | Ensures strict, efficient validation and produces clean, auto‑documented API schemas.                                 |


### **Database**

**PostgreSQL 18 + PostGIS**  
Chosen due to:

*   Geospatial types (`geography`, `geometry`)
*   Efficient spatial indexing (GiST, SP‑GiST)
*   Advanced functions (`ST_DWithin`, KNN-distance, clustering)

### **DB Access Layer**

**asyncpg**

*   Very fast
*   Full async support
*   Lower overhead than SQLAlchemy ORM

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

# 6. Deployment

**This section is in progress.**  
A placeholder for:

*   Docker deployment
*   Railway/Render deployment
*   Systemd service setup
*   Production environment variables
*   SSL certificates / reverse proxy

***

# 7. Setup & Installation

### **Prerequisites**

*   Python **3.11+**
*   PostgreSQL **18** with **PostGIS**
*   (Optional) Redis

### **Installation**

```bash
pip install -r requirements.txt
```

### **Environment Variables**

Copy `.env.example` → `.env`:

    DATABASE_URL=postgres://...
    JWT_SECRET=your_secret
    API_KEY=admin_key

### **Run the Server**

```bash
uvicorn app.main:app --reload
```

### **Run Tests**

```bash
pytest -q
```

***

# 8. Database Schema

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

# 9. Data Sources 

### **Summary**

This API is built using a creative, multi‑dataset, geospatially‑aware pipeline that combines:

*   Public Wi‑Fi datasets (multiple councils)
*   Police crime data
*   ONS Postcode Directory
*   LSOA boundaries & population
*   Derived merged LSOA context (device density, area, geometry)

### **9.1 Wi-Fi Hotspot Datasets**
Includes UK councils such as:
*   Leeds Free WiFi
*   Leicester Public WiFi
*   Calderdale Public WiFi
*   Camden Public WiFi
*   Cambridgeshire Public WiFi

### **9.2 Crime Dataset — UK Police**

Provides:
*   Geolocated crime points
*   LSOA codes for normalisation
***

### **9.3 ONS Postcode Directory**
Crosswalk that maps:
*   Postcode → LSOA → Ward → Authority
***

### **9.4 LSOA Boundaries & Geometry**
Provides:
*   Area
*   Polygons
*   Centroids
***

### **9.5 LSOA Population**
Population density → device density → risk of opportunistic cyber events.
***

### **9.6 Merged LSOA Context Dataset**
A custom ETL product combining all of the above.

***

# 10. System Architecture
Below is an ASCII diagram of the system architecture

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

# 11. Authentication & Authorization

### **JWT Authentication**

Used for:

*   `/incidents` CRUD
*   Admin hotspot updates

### **API Key Authentication**

Used for:

*   `/internal/stats`
*   `/internal/version`

***

# 12. How to Use the API

### 1. **Signup**

```bash
POST /auth/signup
```

### 2. **Login**

```bash
POST /auth/login
```

Response:

```json
{ "access_token": "..." }
```

### 3. **Use the Token**

    Authorization: Bearer <token>

### 4. **Make Requests**

Examples:

```bash
GET /hotspots/search?name=library
GET /assessments/safety?ssid=FreeWifi&lat=53.8&lon=-1.55
POST /incidents/?wifi_id=abc123&description=Suspicious activity
```

***

# 13. API Endpoints

Absolutely — here is the **API Endpoints section rewritten in clean README‑friendly Markdown**, ready to paste directly into your `README.md`.

All formatting is Markdown‑native, with headings, tables, spacing, and structure that GitHub will render perfectly.

***

# **13. API Endpoints**

Below is the complete list of endpoints, fully aligned with the **API Documentation**.

***

## **Hotspot Endpoints (Public)**

| Method    | Endpoint                                            | Description                                     |
| --------- | --------------------------------------------------- | ----------------------------------------------- |
| **GET**   | `/hotspots/`                                        | Return all Wi‑Fi hotspots.                      |
| **GET**   | `/hotspots/{wifi_id}`                               | Return full details for a specific hotspot.     |
| **GET**   | `/hotspots/search?name=`                            | Search hotspots by name (case‑insensitive).     |
| **GET**   | `/hotspots/city?city=`                              | Filter hotspots by city.                        |
| **GET**   | `/hotspots/nearest?lat=&lon=`                       | Return the nearest hotspot to a location.       |
| **GET**   | `/hotspots/nearest/knn?lat=&lon=&k=`                | Return the *k* nearest hotspots.                |
| **GET**   | `/hotspots/near?lat=&lon=&radius=`                  | Return hotspots within a radius (meters).       |
| **PATCH** | `/hotspots/{wifi_id}/status?status=`                | Update hotspot status (Admin‑only, JWT).        |
| **PATCH** | `/hotspots/{wifi_id}/security?security_protection=` | Update hotspot security mode (Admin‑only, JWT). |

***

## **Assessment Endpoints (Public)**

These endpoints evaluate network security, crime exposure, spoofing, and produce the final cyber‑exposure score.

| Method  | Endpoint                                   | Description                                         |
| ------- | ------------------------------------------ | --------------------------------------------------- |
| **GET** | `/assessments/security?ssid=&lat=&lon=`    | Evaluate hotspot security level.                    |
| **GET** | `/assessments/crime?ssid=&lat=&lon=`       | Retrieve crime incidents within hotspot vicinity.   |
| **GET** | `/assessments/incidents?ssid=&lat=&lon=`   | Retrieve historical user‑reported incidents.        |
| **GET** | `/assessments/ssid_risk?ssid=&lat=&lon=`   | Detect likelihood of SSID spoofing.                 |
| **GET** | `/assessments/environment?ssid=&lat=&lon=` | Return environmental/venue context.                 |
| **GET** | `/assessments/safety?ssid=&lat=&lon=`      | Compute the final **Cyber Exposure Score (0–100)**. |

***

## **Analytics Endpoints (Public)**

| Method  | Endpoint                         | Description                                    |
| ------- | -------------------------------- | ---------------------------------------------- |
| **GET** | `/analytics/ranked?city=&limit=` | Rank hotspots by cyber exposure score.         |
| **GET** | `/analytics/crime/{wifi_id}`     | Retrieve crime metrics for a specific hotspot. |

> **Note:** `/analytics/nearby` does **not** exist in the final API specification.

***

## **Incident Endpoints (JWT Required)**

| Method     | Endpoint                                   | Description                       |
| ---------- | ------------------------------------------ | --------------------------------- |
| **POST**   | `/incidents/?wifi_id=&bssid=&description=` | Create a new incident report.     |
| **GET**    | `/incidents/{wifi_id}`                     | List all incidents for a hotspot. |
| **PATCH**  | `/incidents/{incident_id}?description=`    | Update an existing incident.      |
| **DELETE** | `/incidents/{incident_id}`                 | Delete an incident.               |

Authentication header:

    Authorization: Bearer <jwt-token>

***

##**Internal Admin Endpoints (API Key Required)**

| Method  | Endpoint            | Description                                       |
| ------- | ------------------- | ------------------------------------------------- |
| **GET** | `/internal/stats`   | System statistics and internal telemetry.         |
| **GET** | `/internal/version` | API version, PostgreSQL version, PostGIS version. |

Header:

    X-API-Key: <your-key>

***

## **System Health Endpoints**

| Method  | Endpoint   | Description                           |
| ------- | ---------- | ------------------------------------- |
| **GET** | `/livez`   | Service liveness probe.               |
| **GET** | `/readyz`  | Readiness probe (database available). |
| **GET** | `/healthz` | General system status.                |

***

# 14. Cyber Exposure Score


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

# 17. Rate Limiting

Assessment endpoints are protected:

    30 requests / minute per IP

This prevents automated hotspot scanning.
***

# 18. Testing

### Run the test suite:

```bash
pytest -q
```

### Tests include:

*   JWT auth
*   API key checks
*   Hotspot geospatial operations
*   Assessment scoring
*   Internal diagnostics
*   OpenAPI contract stability

***

# 18. Error Codes & Debugging Guide

| Status  | Meaning             | Common Causes                   |
| ------- | ------------------- | ------------------------------- |
| **400** | Bad Request         | Invalid parameters              |
| **401** | Unauthorized        | Missing/invalid JWT             |
| **403** | Forbidden           | Missing API key                 |
| **404** | Not Found           | Invalid wifi\_id / no incidents |
| **409** | Conflict            | Duplicate signup                |
| **422** | Validation error    | Wrong types, missing fields     |
| **500** | Server error        | Uncaught exceptions             |
| **503** | Service unavailable | DB offline                      |

### **Windows Issues & Fixes**

**Problem:** Redis unavailable  
**Fix:** System gracefully degrades to no‑op cache.

**Problem:** PostGIS installation  
Use Postgres installer with PostGIS bundle.

**Problem:** Long filepaths\*\*  
Enable:

    HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\FileSystem\LongPathsEnabled = 1

***

# 23. References


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

