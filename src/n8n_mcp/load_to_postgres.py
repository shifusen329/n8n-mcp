from src.postgres_client import PostgresClient
from src.workflow_parser import process_all_workflows

def main():
    """
    Processes all workflows and loads them into the PostgreSQL database.
    """
    print("Processing workflows...")
    workflows = process_all_workflows()
    
    if not workflows:
        print("No workflows to process.")
        return

    print(f"Processed {len(workflows)} workflows.")

    pg_client = PostgresClient()
    pg_client.connect()

    if not pg_client.connection:
        print("Could not connect to PostgreSQL. Aborting.")
        return

    pg_client.create_workflows_table()

    print("Loading workflows into PostgreSQL...")
    for workflow in workflows:
        pg_client.insert_workflow(workflow)
    
    print("Workflows loaded successfully.")
    pg_client.disconnect()

if __name__ == "__main__":
    main()
