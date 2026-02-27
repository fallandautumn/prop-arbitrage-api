from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def force_reset():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as connection:
        # トランザクションを開始して全データを削除
        with connection.begin():
            connection.execute(text("TRUNCATE TABLE properties;"))
            print("Success: The 'properties' table has been cleared.")

if __name__ == "__main__":
    force_reset()