import streamlit as st
import requests
import uuid
from datetime import datetime
import re

# Initialize session state keys if not already present
if "chat_id" not in st.session_state:
    st.session_state["chat_id"] = str(uuid.uuid4())  # Generate a unique ID for the chat
if "conversation_step" not in st.session_state:
    st.session_state["conversation_step"] = 0  # Track the step in the move-related conversation
if "query_type" not in st.session_state:
    st.session_state["query_type"] = None  # Identify if it's a move-related or general query
if "move_details" not in st.session_state:
    st.session_state["move_details"] = {
        "origin": None,
        "destination": None,
        "distance": None,  # Store the calculated distance
        "name": None,
        "contact_no": None,
        "date": None,
        "move_size": None,
        "additional_services": []
    }
if "general_response" not in st.session_state:
    st.session_state["general_response"] = None  # Store response for general queries

# Define the API URL
api_url = "https://3c03-39-37-133-73.ngrok-free.app"

# Set Streamlit page configuration
st.set_page_config(page_title="Chatbot - Move Planner", page_icon="🤖", layout="wide")

# Helper function to reset the conversation
def reset_conversation():
    st.session_state["chat_id"] = str(uuid.uuid4())  # Generate a new unique chat_id
    st.session_state["conversation_step"] = 0
    st.session_state["query_type"] = None
    st.session_state["move_details"] = {
        "origin": None,
        "destination": None,
        "distance": None,
        "name": None,
        "contact_no": None,
        "date": None,
        "move_size": None,
        "additional_services": []
    }
    st.session_state["general_response"] = None

# Helper function to parse locations from a query
def parse_locations(query):
    location_pattern = r"from\s([\w\s,]+)\sto\s([\w\s,]+)"
    match = re.search(location_pattern, query.lower())
    if match:
        origin = match.group(1).strip().title()
        destination = match.group(2).strip().title()
        return origin, destination
    return None, None

# Helper function to calculate and fetch distance
def fetch_distance(origin, destination):
    try:
        payload = {"origin": origin, "destination": destination}
        response = requests.post(f"{api_url}/calculate_distance", json=payload)
        response.raise_for_status()
        data = response.json()
        return data.get("distance", None)
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching distance: {e}")
        return None

# Reset button for testing
if st.button("Home"):
    reset_conversation()

# Step 0: Identify Query Type
if st.session_state["conversation_step"] == 0:
    st.title("Chatbot - Move Planner 🤖")
    st.write("**Bot:** Hey! How may I help you?")
    user_query = st.text_input("Your query:")
    if st.button("Submit Query"):
        if user_query.strip():
            # Classify query
            move_keywords = ["move", "relocation", "transfer", "moving", "from", "to"]
            if any(keyword in user_query.lower() for keyword in move_keywords):
                st.session_state["query_type"] = "move"
                # Extract locations from the query
                origin, destination = parse_locations(user_query)
                if origin:
                    st.session_state["move_details"]["origin"] = origin
                if destination:
                    st.session_state["move_details"]["destination"] = destination

                # If both origin and destination are provided, calculate distance
                if origin and destination:
                    distance = fetch_distance(origin, destination)
                    if distance:
                        st.session_state["move_details"]["distance"] = distance
                        st.success(f"The distance between {origin} and {destination} is {distance} miles.")
                    st.session_state["conversation_step"] = 3  # Proceed to the next step
                elif not st.session_state["move_details"]["origin"]:
                    st.session_state["conversation_step"] = 1  # Ask for origin
                elif not st.session_state["move_details"]["destination"]:
                    st.session_state["conversation_step"] = 2  # Ask for destination
            else:
                st.session_state["query_type"] = "general"
                # Fetch GPT response for general query
                try:
                    payload = {"message": user_query, "chat_id": st.session_state["chat_id"]}
                    response = requests.post(f"{api_url}/general_query", json=payload)
                    response.raise_for_status()
                    data = response.json()
                    st.session_state["general_response"] = data.get("reply", "No response available.")
                except requests.exceptions.RequestException as e:
                    st.session_state["general_response"] = f"Error fetching general response: {e}"

# Handle General Query
if st.session_state["query_type"] == "general":
    st.write("**Bot:** Here’s what I found:")
    st.write(st.session_state["general_response"])

# Handle Move-Related Query
elif st.session_state["query_type"] == "move":
    if st.session_state["conversation_step"] == 1:
        st.write("**Bot:** Where are you moving from?")
        origin = st.text_input("Enter your starting location:")
        if st.button("Next"):
            if origin:
                st.session_state["move_details"]["origin"] = origin
                if st.session_state["move_details"]["destination"]:
                    # Calculate distance if destination is already provided
                    distance = fetch_distance(origin, st.session_state["move_details"]["destination"])
                    if distance:
                        st.session_state["move_details"]["distance"] = distance
                        st.success(f"The distance between {origin} and {st.session_state['move_details']['destination']} is {distance} miles.")
                st.session_state["conversation_step"] = 2  # Ask for destination
            else:
                st.error("Please provide your starting location.")
    elif st.session_state["conversation_step"] == 2:
        st.write("**Bot:** Where are you moving to?")
        destination = st.text_input("Enter your destination:")
        if st.button("Next"):
            if destination:
                st.session_state["move_details"]["destination"] = destination
                if st.session_state["move_details"]["origin"]:
                    # Calculate distance if origin is already provided
                    distance = fetch_distance(st.session_state["move_details"]["origin"], destination)
                    if distance:
                        st.session_state["move_details"]["distance"] = distance
                        st.success(f"The distance between {st.session_state['move_details']['origin']} and {destination} is {distance} miles.")
                st.session_state["conversation_step"] = 3  # Proceed to next step
            else:
                st.error("Please provide your destination.")
    elif st.session_state["conversation_step"] == 3:
        st.write("**Bot:** May I know your name?")
        name = st.text_input("Enter your name:")
        if st.button("Next"):
            if name:
                st.session_state["move_details"]["name"] = name
                st.session_state["conversation_step"] = 4  # Ask for contact number
            else:
                st.error("Please provide your name.")
    elif st.session_state["conversation_step"] == 4:
        st.write(f"**Bot:** Thanks, {st.session_state['move_details']['name']}! Can I have your contact number?")
        contact_no = st.text_input("Enter your contact number:")
        if st.button("Next"):
            if contact_no:
                st.session_state["move_details"]["contact_no"] = contact_no
                st.session_state["conversation_step"] = 5  # Proceed to move date
            else:
                st.error("Please provide your contact number.")
    elif st.session_state["conversation_step"] == 5:
        st.write("**Bot:** When do you want to move?")
        move_date = st.date_input("Select your moving date:", min_value=datetime.today())
        if st.button("Next"):
            st.session_state["move_details"]["date"] = move_date
            st.session_state["conversation_step"] = 6  # Proceed to move size
    elif st.session_state["conversation_step"] == 6:
        st.write("**Bot:** What is your move size?")
        move_size = st.selectbox(
            "Select your move size:",
            options=["Studio Apartment", "1-Bedroom", "2-Bedroom", "3-Bedroom", "4-Bedroom", "4+ Bedrooms", "Office", "Car"]
        )
        if st.button("Next"):
            st.session_state["move_details"]["move_size"] = move_size
            st.session_state["conversation_step"] = 7  # Proceed to additional services
    elif st.session_state["conversation_step"] == 7:
        st.write("**Bot:** Do you want any additional services?")
        packing = st.checkbox("Packing")
        storage = st.checkbox("Storage")
        if st.button("Get Estimate"):
            st.session_state["move_details"]["additional_services"] = []
            if packing:
                st.session_state["move_details"]["additional_services"].append("packing")
            if storage:
                st.session_state["move_details"]["additional_services"].append("storage")
            st.session_state["conversation_step"] = 8  # Proceed to estimate
    elif st.session_state["conversation_step"] == 8:
        st.write("**Bot:** Let me calculate the estimated cost of your move...")

        # Prepare API payload
        move_details = st.session_state["move_details"]
        payload = {
            "chat_id": st.session_state["chat_id"],
            "origin": move_details["origin"],
            "destination": move_details["destination"],
            "move_size": move_details["move_size"],
            "additional_services": move_details["additional_services"],
            "username": move_details["name"],  # Pass username
            "contact_no": move_details["contact_no"],  # Pass contact number
            "move_date": str(move_details["date"])  # Pass moving date
        }

        # Fetch cost estimate from API
        try:
            response = requests.post(f"{api_url}/estimate_cost", json=payload)
            response.raise_for_status()
            data = response.json()
            estimated_cost = data.get("estimated_cost", "No estimate available.")

        # Display the cost prominently
            st.markdown(
                f"""
                <div style="text-align: center; font-size: 1.5em; margin-top: 20px; margin-bottom: 20px; color: #4CAF50;">
                    <b>Bot:</b> The estimated cost of your move is: <b style="color: #E91E63;">{estimated_cost}</b>
                </div>
                """,
                unsafe_allow_html=True
            )
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching cost estimate: {e}")
