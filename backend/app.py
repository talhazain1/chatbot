from flask import Flask, request, jsonify
from redis_manager import RedisManager
from openai_manager import OpenAIManager
from maps_manager import MapsManager
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
    user_input = request.json.get("message", "")
    chat_id = request.json.get("chat_id", str(uuid.uuid4()))  
    redis_manager.init_chat(chat_id, None, None)  
    response = openai_manager.get_general_response(user_input)
    redis_manager.add_message(chat_id, user_input, response)
    return jsonify({"reply": response})

@app.route("/estimate_cost", methods=["POST"])
def estimate_cost():
    data = request.json
    chat_id = data.get("chat_id", str(uuid.uuid4()))  
    origin = data.get("origin")
    destination = data.get("destination")
    move_size = data.get("move_size")
    additional_services = data.get("additional_services", [])
    username = data.get("username", "Unknown")
    contact_no = data.get("contact_no", "Unknown")
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
        "name": username,
        "contact_no": contact_no,
        "origin": origin,
        "destination": destination,
        "date": move_date,
        "move_size": move_size,
        "additional_services": additional_services
    }
    redis_manager.store_move_details(chat_id, move_details, estimated_cost)

    return jsonify({"estimated_cost": estimated_cost})
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
