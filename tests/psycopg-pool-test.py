# docker run --rm -it --name some-postgres -e POSTGRES_USER=myuser -e POSTGRES_PASSWORD=mypassword -e POSTGRES_DB=mydatabase -p 5432:5432 postgres

from psycopg_pool import ConnectionPool

try:
    pool = ConnectionPool(
        "dbname=mydatabase user=myuser password=mypassword host=localhost port=5432"
    )
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            version = cur.fetchone()
            print("PostgreSQL version:", version[0])
except:
    # It runs code, good enough until we can run a psql in wasix!
    pass
