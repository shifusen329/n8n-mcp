import os
from pathlib import Path
from collections import defaultdict
from src.workflow_parser import process_all_workflows
from src.embedding_client import EmbeddingClient

def main():
    """Main function to run the workflow vectorization and search process."""
    try:
        print("Step 1: Processing workflows...")
        processed_workflows = process_all_workflows()
        print(f"Successfully processed {len(processed_workflows)} workflows")

        print("\nStep 2: Generating embeddings for workflows...")
        client = EmbeddingClient()
        embeddings = []
        for workflow in processed_workflows:
            embedding = client.get_embedding(workflow["description"])
            if embedding:
                embeddings.append(embedding)
        
        print(f"Successfully generated {len(embeddings)} embeddings.")

        print("\nStep 3: Searching for similar workflows...")
        query = "workflow that handles email automation"
        query_embedding = client.get_embedding(query)

        if query_embedding:
            similar_indices = client.search_similar(query_embedding, embeddings)
            print(f"\nTop {len(similar_indices)} similar workflows for query: '{query}'")
            for i, score in similar_indices:
                print(f"- {processed_workflows[i]['name']} (Score: {score:.4f})")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
