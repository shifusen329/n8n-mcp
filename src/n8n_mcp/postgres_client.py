import os
import json
import psycopg2
from dotenv import load_dotenv

load_dotenv()

class PostgresClient:
    def __init__(self):
        self.connection = None
        self.user = os.getenv("POSTGRES_USER")
        self.password = os.getenv("POSTGRES_PASSWORD")
        self.db = os.getenv("POSTGRES_DB")
        self.host = os.getenv("POSTGRES_HOST")
        self.port = os.getenv("POSTGRES_PORT")

    def connect(self):
        try:
            self.connection = psycopg2.connect(
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port,
                database=self.db
            )
            print("PostgreSQL database connection successful")
        except (Exception, psycopg2.Error) as error:
            print(f"Error while connecting to PostgreSQL: {error}")
            self.connection = None

    def disconnect(self):
        if self.connection:
            self.connection.close()
            print("PostgreSQL connection closed")

    def execute_query(self, query, params=None):
        if not self.connection:
            print("No connection to the database.")
            return None
        
        cursor = self.connection.cursor()
        try:
            cursor.execute(query, params)
            self.connection.commit()
            return cursor
        except (Exception, psycopg2.Error) as error:
            print(f"Error executing query: {error}")
            self.connection.rollback()
            return None
        finally:
            cursor.close()

    def create_workflows_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS workflows (
            id VARCHAR(255) PRIMARY KEY,
            original_filename TEXT,
            category TEXT,
            name TEXT,
            description TEXT,
            tags TEXT[],
            complexity JSONB,
            original_workflow JSONB
        );
        """
        self.execute_query(query)
        print("Workflows table created or already exists.")

    def insert_workflow(self, workflow):
        query = """
        INSERT INTO workflows (id, original_filename, category, name, description, tags, complexity, original_workflow)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING;
        """
        params = (
            workflow['id'],
            workflow['originalFilename'],
            workflow['category'],
            workflow['name'],
            workflow['description'],
            workflow['tags'],
            json.dumps(workflow['complexity']),
            json.dumps(workflow['originalWorkflow'])
        )
        self.execute_query(query, params)

if __name__ == '__main__':
    client = PostgresClient()
    client.connect()
    if client.connection:
        client.create_workflows_table()
        client.disconnect()
