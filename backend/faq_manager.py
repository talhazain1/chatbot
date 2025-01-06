import openai
import numpy as np
import json

class FAQManager:
    def __init__(self, embedding_model="text-embedding-ada-002"):
        self.embedding_model = embedding_model
        self.faq_data = []
        self.embeddings = []

    def load_faqs(self, dataset_path):
        """
        Load FAQs from a JSONL or CSV file and compute embeddings.
        """
        with open(dataset_path, "r") as file:
            self.faq_data = [json.loads(line) for line in file]

        # Generate embeddings for all questions
        self.embeddings = [
            self.get_embedding(faq["question"]) for faq in self.faq_data
        ]

    def get_embedding(self, text):
        """
        Get the embedding for a given text using OpenAI.
        """
        response = openai.Embedding.create(
            model=self.embedding_model,
            input=text
        )
        return np.array(response["data"][0]["embedding"])

    def find_best_match(self, user_question):
        """
        Find the most similar FAQ question to the user's query.
        """
        user_embedding = self.get_embedding(user_question)

        # Calculate cosine similarity with all stored embeddings
        similarities = [
            np.dot(user_embedding, faq_embedding) /
            (np.linalg.norm(user_embedding) * np.linalg.norm(faq_embedding))
            for faq_embedding in self.embeddings
        ]

        # Find the best match
        best_match_idx = np.argmax(similarities)
        best_match_score = similarities[best_match_idx]

        # Set a threshold for matching
        if best_match_score > 0.75:  # Adjust threshold as needed
            return self.faq_data[best_match_idx]["answer"]
        return "I'm sorry, I don't have an answer for that."

