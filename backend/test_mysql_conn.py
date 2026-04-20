import os
from sqlalchemy import create_engine
from sqlalchemy.sql import text

# Test MySQL connection using the URL from docker-compose
DATABASE_URL = "mysql+mysqlconnector://root:root@localhost:3306/crm_hcp"

def test_conn():
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("Successfully connected to MySQL in Docker!")
    except Exception as e:
        print(f"Failed to connect to MySQL: {e}")

if __name__ == "__main__":
    test_conn()
