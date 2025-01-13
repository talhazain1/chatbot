from flask import Flask, request, jsonify
from redis_manager import RedisManager
from openai_manager import OpenAIManager
from maps_manager import MapsManager
from faq_manager import FAQManager
from flask_cors import CORS
import uuid  

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "https://chatbot-mygoodmovers.streamlit.app"}})
redis_manager = RedisManager()
openai_manager = OpenAIManager()
maps_manager = MapsManager()

@app.route("/", methods=["GET"])
def home():
    return "Chatbot API is running."

@app.route("/general_query", methods=["POST"])
def general_query():
    data = request.json
    user_input = data.get("message", "")
    chat_id = data.get("chat_id", str(uuid.uuid4()))
    
    redis_manager.init_chat(chat_id)  # Ensure the chat session is initialized

    # Retrieve previous context
    previous_context = redis_manager.get_context(chat_id, "context")
    if previous_context:
        combined_input = f"{previous_context}\nUser: {user_input}"
    else:
        combined_input = user_input

    # Generate response
    response = openai_manager.get_general_response(combined_input)
    
    # Update Redis with new context
    redis_manager.update_context(chat_id, "context", f"{combined_input}\nAssistant: {response}")

    redis_manager.add_message(chat_id, user_input, response)  # Save message history
    return jsonify({"reply": response})


@app.route("/estimate_cost", methods=["POST"])
def estimate_cost():
    data = request.json
    chat_id = data.get("chat_id", str(uuid.uuid4()))  
    origin = data.get("origin")
    destination = data.get("destination")
    move_size = data.get("move_size")
    additional_services = data.get("additional_services", [])
    # username = data.get("username", "Unknown")
    # contact_no = data.get("contact_no", "Unknown")
    move_date = data.get("move_date", "Unknown")

    if not (origin and destination and move_size):
        return jsonify({"error": "Missing required fields."}), 400

    distance, cost_range_or_error = maps_manager.estimate_cost(origin, destination, move_size, additional_services)
    if distance is None:
        return jsonify({"error": cost_range_or_error}), 400

    min_cost, max_cost = cost_range_or_error
    estimated_cost = f"${min_cost} - ${max_cost}"

    # Store all details in Redis
    move_details = {
        # "name": username,
        # "contact_no": contact_no,
        "origin": origin,
        "destination": destination,
        "date": move_date,
        "move_size": move_size,
        "additional_services": additional_services
    }
    redis_manager.store_move_details(chat_id, move_details, estimated_cost)

    return jsonify({"estimated_cost": estimated_cost})

faq_manager = FAQManager()
faq_manager.load_faqs("/Users/TalhaZain/chatbot/backend/data/faqs.jsonl")  # Replace with your dataset path

@app.route("/faq_query", methods=["POST"])
def faq_query():
    data = request.json
    user_question = data.get("message", "")

    if not user_question:
        return jsonify({"error": "No question provided"}), 400

    print(f"Received FAQ Query: {user_question}")  # Debugging

    # Find the best match
    answer = faq_manager.find_best_match(user_question)
    print(f"FAQ Answer: {answer}")  # Debugging
    return jsonify({"reply": answer})


@app.route("/calculate_distance", methods=["POST"])
def calculate_distance():
    data = request.json
    origin = data.get("origin")
    destination = data.get("destination")

    if not (origin and destination):
        return jsonify({"error": "Missing required fields: origin and destination"}), 400

    try:
        distance = maps_manager.calculate_distance(origin, destination)
        if distance is None:
            return jsonify({"error": "Unable to calculate distance. Please check the locations."}), 400
        return jsonify({"distance": distance})
    except Exception as e:
        return jsonify({"error": f"An error occurred: {e}"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

