import openai
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
class OpenAIManager:
    def __init__(self):
        # Set your OpenAI API key
        openai.api_key = os.getenv("OPENAI_API_KEY")

    def get_general_response(self, prompt):
        """
        Fetch a response from OpenAI GPT for general queries.
        """
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",  # Use the correct model available for your API plan
                messages=[
                    {"role": "system", "content": "You are a helpful assistant and a representative of My Good Movers. Provide summarize responses to user queries. Also you have to provide the best possible solution to the user. And try to stay on topic that we are a moving company. And try to convince the user to take our services."},                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.7
            )
            # Extract and return the assistant's reply
            return response["choices"][0]["message"]["content"].strip()
        except openai.AuthenticationError:
            return "Error: Invalid API key. Please check your OpenAI API key."
        except openai.BadRequestError as e:
            return f"Error: Bad request. Details: {e}"
        except openai.RateLimitError:
            return "Error: Rate limit exceeded. Please try again later."
        except openai.APIError as e:
            return f"Error: OpenAI API error. Details: {e}"
        except Exception as e:
            return f"An unexpected error occurred: {e}"
