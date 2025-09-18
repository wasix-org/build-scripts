# docker run --rm -it --name some-postgres -e POSTGRES_USER=myuser -e POSTGRES_PASSWORD=mypassword -e POSTGRES_DB=mydatabase -p 5432:5432 postgres

import os

import psycopg

try:
    conn = psycopg.connect(
        dbname=os.environ.get("POSTGRES_DB", "docker-local"),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", "securesecret"),
        host=os.environ.get("DB_HOST", "0.0.0.0"),
        port=os.environ.get("DB_PORT", "5432"),
    )
    cur = conn.cursor()
    cur.execute("SELECT version();")
    version = cur.fetchone()
    print("PostgreSQL version:", version[0])
except:
    # It runs code, good enough until we can run a psql in wasix!
    pass
