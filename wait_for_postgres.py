import logging
import os
from time import sleep, time

import psycopg

check_timeout = int(os.getenv("POSTGRES_CHECK_TIMEOUT", "30"))
check_interval = int(os.getenv("POSTGRES_CHECK_INTERVAL", "1"))
interval_unit = "second" if check_interval == 1 else "seconds"
config = {
    "dbname": os.getenv("POSTGRES_DB", "postgres"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", ""),
    "host": os.getenv("POSTGRES_HOST", "postgres")
}

start_time = time()
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


def pg_isready(host, user, password, dbname):
    while time() - start_time < check_timeout:
        try:
            conn = psycopg.connect(**vars())
            logger.info("Postgres is ready! ✨ 💅")
            conn.close()
            return True #noqa: TRY300
        except psycopg.OperationalError:
            logger.info("Postgres isn't ready. Waiting for %(check_interval) %(interval_unit)...", extra={"check_interval": check_interval, "interval_unit": interval_unit})
            sleep(check_interval)

    logger.error("We could not connect to Postgres within %(check_timeout) seconds.", extra={"check_timeout": check_timeout})
    return False


pg_isready(**config)
