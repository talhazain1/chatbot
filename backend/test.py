from openai_manager import OpenAIManager

# Initialize OpenAIManager
manager = OpenAIManager()

# Define a sample prompt
prompt = "What is the capital of France?"

# Fetch the response
try:
    response = openai.chat.completions.create(prompt)  # Use the correct method name
    print(f"Response: {response}")
except AttributeError as e:
    print(f"Error: {e}")
