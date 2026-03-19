FROM postgis/postgis:16-3.4

ENV POSTGRES_DB=wifi_risk_db
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=postgres

# Allow Railway to expose port 5432
EXPOSE 5432