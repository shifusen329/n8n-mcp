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
        self.execute_query("CREATE EXTENSION IF NOT EXISTS vector;")
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
        
        query_embeddings = """
        CREATE TABLE IF NOT EXISTS workflow_embeddings (
            id SERIAL PRIMARY KEY,
            workflow_id VARCHAR(255) NOT NULL,
            embedding vector(384),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (workflow_id) REFERENCES workflows (id) ON DELETE CASCADE
        );
        """
        self.execute_query(query_embeddings)
        print("Tables created or already exist.")

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

    def insert_workflow_embedding(self, workflow_id, embedding):
        query = """
        INSERT INTO workflow_embeddings (workflow_id, embedding)
        VALUES (%s, %s)
        ON CONFLICT (workflow_id) DO UPDATE SET embedding = EXCLUDED.embedding;
        """
        params = (workflow_id, embedding)
        self.execute_query(query, params)

    def search_similar_workflows(self, embedding, top_k=5):
        query = """
        SELECT w.*
        FROM workflows w
        JOIN workflow_embeddings we ON w.id = we.workflow_id
        ORDER BY we.embedding <-> %s
        LIMIT %s;
        """
        params = (embedding, top_k)
        cursor = self.execute_query(query, params)
        if cursor:
            return cursor.fetchall()
        return []

if __name__ == '__main__':
    client = PostgresClient()
    client.connect()
    if client.connection:
        client.create_workflows_table()
        client.disconnect()
