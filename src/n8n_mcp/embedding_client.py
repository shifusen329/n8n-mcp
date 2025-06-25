import requests
import json
import numpy as np

class EmbeddingClient:
    def __init__(self, host="http://192.168.0.100:11434", model_name="qwen3-embedding-0.6b"):
        self.host = host
        self.model_name = model_name
        self.base_url = f"{self.host}/api/embeddings"

    def get_embedding(self, text: str):
        try:
            response = requests.post(
                self.base_url,
                data=json.dumps({
                    "model": self.model_name,
                    "prompt": text
                })
            )
            response.raise_for_status()
            return response.json()["embedding"]
        except requests.exceptions.RequestException as e:
            print(f"Error getting embedding: {e}")
            return None

    def cosine_similarity(self, v1, v2):
        return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

    def search_similar(self, query_embedding, embeddings, top_k=5):
        similarities = [
            (i, self.cosine_similarity(query_embedding, emb))
            for i, emb in enumerate(embeddings)
        ]
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
