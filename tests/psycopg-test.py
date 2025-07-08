# docker run --rm -it --name some-postgres -e POSTGRES_USER=myuser -e POSTGRES_PASSWORD=mypassword -e POSTGRES_DB=mydatabase -p 5432:5432 postgres

import psycopg

conn = psycopg.connect("dbname=mydatabase user=myuser password=mypassword host=localhost port=5432")
cur = conn.cursor()
cur.execute("SELECT version();")
version = cur.fetchone()
print("PostgreSQL version:", version[0])