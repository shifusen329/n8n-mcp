import os
import requests
from dotenv import load_dotenv

load_dotenv()

class N8nApiClient:
    def __init__(self):
        self.base_url = os.getenv("N8N_HOST", "http://localhost:5678")
        self.api_key = os.getenv("N8N_API_KEY")
        if not self.api_key:
            raise ValueError("N8N_API_KEY not found in .env file")
        self.headers = {
            "Accept": "application/json",
            "X-N8N-API-KEY": self.api_key,
        }

    def get_workflows(self):
        workflows = []
        cursor = None
        while True:
            params = {}
            if cursor:
                params["cursor"] = cursor
            
            try:
                response = requests.get(f"{self.base_url}/api/v1/workflows", headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()
                
                if "data" in data and data["data"]:
                    workflows.extend(data["data"])
                
                cursor = data.get("nextCursor")
                if not cursor:
                    break
            except requests.exceptions.RequestException as e:
                print(f"Error fetching workflows: {e}")
                break
        
        return workflows

    def create_workflow(self, workflow_data):
        try:
            response = requests.post(f"{self.base_url}/api/v1/workflows", headers=self.headers, json=workflow_data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error creating workflow: {e}")
            return None

    def get_workflow(self, workflow_id: str):
        try:
            response = requests.get(f"{self.base_url}/api/v1/workflows/{workflow_id}", headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching workflow {workflow_id}: {e}")
            return None

    def update_workflow(self, workflow_id: str, workflow_data: dict):
        try:
            response = requests.put(f"{self.base_url}/api/v1/workflows/{workflow_id}", headers=self.headers, json=workflow_data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error updating workflow {workflow_id}: {e}")
            return None

if __name__ == "__main__":
    client = N8nApiClient()
    all_workflows = client.get_workflows()
    if all_workflows:
        print(f"Successfully retrieved {len(all_workflows)} workflows.")
        # print(all_workflows[0])
