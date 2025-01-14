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
    st.session_state["query_type"] = None  # Identify if it's a move-related, FAQ, or general query
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
if "faq_response" not in st.session_state:
    st.session_state["faq_response"] = None  # Store response for FAQ queries

# NEW: Maintain a chat history for follow-up/context
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

# Define the API URL
api_url = "https://aac7-39-37-170-13.ngrok-free.app"

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
    st.session_state["faq_response"] = None
    st.session_state["chat_history"] = []

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

def classify_query(user_query):
    """
    Classify the query into move-related, FAQ, or general using pattern matching.
    """
    normalized_query = user_query.lower().strip()
    # Patterns for move-related queries
    move_patterns = [
        r"\bmove\b", r"\brelocation\b", r"\btransfer\b", r"\bfrom\b.*\bto\b",
        r"\bestimate\b", r"\bhow far\b", r"\bcost\b"
    ]

    # Patterns for FAQ-related queries
    faq_patterns = [
        # Platform-related patterns
        r"\breviews\b", r"\bratings\b", r"\bprofile\b", r"\blist\b",
        r"\badvertising\b", r"\bcontact\b", r"\baccount\b", r"\bpayment\b",

        # Information request patterns
        r"\bhow\b", r"\bwhat\b", r"\bwhy\b", r"\bcan I\b", r"\bdo you\b",
        r"\bdetails\b", r"\bhelp\b", r"\bassist\b", r"\boffer\b",

        # Movers and safety patterns
        r"\bmovers\b", r"\binsurance\b", r"\bguarantees\b", r"\bdamaged\b",
        r"\btrustworthy\b", r"\bverify\b", r"\bsafe\b",

        # Technical issues and troubleshooting
        r"\bissue\b", r"\bproblem\b", r"\bnot working\b", r"\brefund\b",
        r"\blogin\b", r"\breset\b", r"\btrouble\b", r"\breport\b",

        # Policies and procedures
        r"\bpolicy\b", r"\brules\b", r"\bterms\b", r"\bconditions\b",
        r"\brefund\b", r"\bmodification\b", r"\bcancel\b", r"\bschedule\b"
    ]

    move_matches = [pattern for pattern in move_patterns if re.search(pattern, normalized_query, re.IGNORECASE)]
    faq_matches = [pattern for pattern in faq_patterns if re.search(pattern, normalized_query, re.IGNORECASE)]

    print(f"Move Matches: {move_matches}")
    print(f"FAQ Matches: {faq_matches}")

    # If there's any FAQ match, prioritize FAQ
    if faq_matches:
        return "faq"
    if move_matches:
        return "move"
    else:
        # Default to general query
        return "general"

# Reset button for testing
if st.button("Home"):
    reset_conversation()

# NEW: For backwards compatibility from old code that used st.session_state["context"]
if "context" not in st.session_state:
    st.session_state["context"] = ""

def handle_user_input():
    user_query = st.session_state.get("query_input", "").strip()
    if user_query:
        # Add the user query to chat history
        st.session_state["chat_history"].append({"sender": "user", "content": user_query})
        
        query_type = classify_query(user_query)
        st.session_state["query_type"] = query_type

        if query_type == "move":
            handle_move_query(user_query)
        elif query_type == "faq":
            handle_faq_query(user_query)
        else:
            handle_general_query(user_query)

def handle_general_query(user_query):
    """
    Handle general queries by interacting with the general_query endpoint.
    """
    payload = {"message": user_query, "chat_id": st.session_state["chat_id"]}
    response = requests.post(f"{api_url}/general_query", json=payload)
    response.raise_for_status()
    data = response.json()
    reply = data.get("reply", "No response available.")
    # Store assistant's reply in chat history
    st.session_state["chat_history"].append({"sender": "assistant", "content": reply})
    # Display
    st.write(f"**Bot:** {reply}")

def handle_faq_query(user_query):
    """
    Handle FAQ queries by interacting with the faq_query endpoint.
    """
    payload = {"message": user_query, "chat_id": st.session_state["chat_id"]}
    response = requests.post(f"{api_url}/faq_query", json=payload)
    response.raise_for_status()
    data = response.json()
    reply = data.get("reply", "I'm sorry, I don't have an answer for that.")
    # Store assistant's reply in chat history
    st.session_state["chat_history"].append({"sender": "assistant", "content": reply})
    # Display
    st.write(f"**Bot:** {reply}")

def handle_move_query(user_query):
    """
    Handle move-related queries by guiding the user through a multi-step process.
    """
    origin, destination = parse_locations(user_query)
    if origin:
        st.session_state["move_details"]["origin"] = origin
    if destination:
        st.session_state["move_details"]["destination"] = destination

    if origin and destination:
        distance = fetch_distance(origin, destination)
        if distance:
            st.session_state["move_details"]["distance"] = distance
            # Store the distance message in chat_history
            distance_msg = f"The distance between {origin} and {destination} is {distance} miles."
            st.session_state["chat_history"].append({"sender": "assistant", "content": distance_msg})
            st.success(distance_msg)
        st.session_state["conversation_step"] = 3  # Proceed to move size
    elif not st.session_state["move_details"]["origin"]:
        st.session_state["conversation_step"] = 1  # Ask for origin
    elif not st.session_state["move_details"]["destination"]:
        st.session_state["conversation_step"] = 2  # Ask for destination

# Display the title once at the top
st.title("Chatbot - Move Planner 🤖")

# Always display the chat history so far
for message in st.session_state["chat_history"]:
    if message["sender"] == "user":
        st.write(f"**You:** {message['content']}")
    else:
        st.write(f"**Bot:** {message['content']}")

# Step 0: Identify Query Type / Initial Interaction
if st.session_state["conversation_step"] == 0:
    # Only show the greeting once at the very beginning if there's no user or bot message yet
    if len(st.session_state["chat_history"]) == 0:
        st.write("**Bot:** Hey! How may I help you?")
    
    # Text input that triggers handle_user_input when user presses Enter
    st.text_input(
        "Your query:",
        key="query_input",
        on_change=handle_user_input,
        placeholder="Type your query here..."
    )

    # Button fallback for mouse click
    if st.button("Submit Query", key="submit_query"):
        handle_user_input()

    # (No further logic here, the steps below will handle multi-step flows.)

elif st.session_state["conversation_step"] == 1:
    st.write("**Bot:** Where are you moving from?")
    origin = st.text_input("Enter your starting location:", key="origin_input")
    if st.button("Next", key="origin_next") or origin:
        if origin:
            # Save user input to chat history
            st.session_state["chat_history"].append({"sender": "user", "content": origin})
            st.session_state["move_details"]["origin"] = origin
            st.session_state["conversation_step"] = 2  # Proceed to destination step
            st.rerun()

        else:
            st.error("Please provide your starting location.")

elif st.session_state["conversation_step"] == 2:
    st.write("**Bot:** Where are you moving to?")
    destination = st.text_input("Enter your destination:", key="destination_input")
    if st.button("Next", key="destination_next") or destination:
        if destination:
            # Save user input to chat history
            st.session_state["chat_history"].append({"sender": "user", "content": destination})
            st.session_state["move_details"]["destination"] = destination
            st.session_state["conversation_step"] = 3  # Proceed to name step
            st.rerun()

        else:
            st.error("Please provide your destination.")

# elif st.session_state["conversation_step"] == 3:
#     st.write("**Bot:** May I know your name?")
#     name = st.text_input("Enter your name:", key="name_input")
#     if st.button("Next", key="name_next") or name:
#         if name:
#             # Save user input to chat history
#             st.session_state["chat_history"].append({"sender": "user", "content": name})
#             st.session_state["move_details"]["name"] = name
#             st.session_state["conversation_step"] = 4  # Proceed to contact number step
#             st.rerun()

#         else:
#             st.error("Please provide your name.")

# elif st.session_state["conversation_step"] == 4:
#     st.write(f"**Bot:** Thanks, {st.session_state['move_details']['name']}! Can I have your contact number?")
#     contact_no = st.text_input("Enter your contact number:", key="contact_no_input")
#     if st.button("Next", key="contact_no_next") or contact_no:
#         if contact_no:
#             # Save user input to chat history
#             st.session_state["chat_history"].append({"sender": "user", "content": contact_no})
#             st.session_state["move_details"]["contact_no"] = contact_no
#             st.session_state["conversation_step"] = 5  # Proceed to move date step
#             st.rerun()

#         else:
#             st.error("Please provide your contact number.")

elif st.session_state["conversation_step"] == 3:
    st.write("**Bot:** When do you want to move?")
    move_date = st.date_input("Select your moving date:", min_value=datetime.today(), key="move_date_input")
    if st.button("Next", key="move_date_next"):
        # Save user date selection to chat history (as a string)
        user_date_str = str(move_date)
        st.session_state["chat_history"].append({"sender": "user", "content": user_date_str})
        st.session_state["move_details"]["date"] = move_date
        st.session_state["conversation_step"] = 4  # Proceed to move size step
        st.rerun()


elif st.session_state["conversation_step"] == 4:
    st.write("**Bot:** What is your move size?")
    move_size = st.selectbox(
        "Select your move size:",
        options=["Studio Apartment", "1-Bedroom", "2-Bedroom", "3-Bedroom", "4-Bedroom", "4+ Bedrooms", "Office", "Car"],
        key="move_size_input"
    )
    if st.button("Next", key="move_size_next"):
        # Save user selection to chat history
        st.session_state["chat_history"].append({"sender": "user", "content": move_size})
        st.session_state["move_details"]["move_size"] = move_size
        st.session_state["conversation_step"] = 5  # Proceed to additional services
        st.rerun()


elif st.session_state["conversation_step"] == 5:
    st.write("**Bot:** Do you want any additional services?")
    packing = st.checkbox("Packing", key="packing_checkbox")
    storage = st.checkbox("Storage", key="storage_checkbox")
    if st.button("Get Estimate", key="additional_services_next"):
        chosen_services = []
        if packing:
            chosen_services.append("packing")
        if storage:
            chosen_services.append("storage")

        # Save user checkbox inputs to chat history in a readable format
        if len(chosen_services) == 0:
            st.session_state["chat_history"].append({"sender": "user", "content": "No additional services selected"})
        else:
            st.session_state["chat_history"].append(
                {"sender": "user", "content": f"Additional services: {', '.join(chosen_services)}"}
            )

        st.session_state["move_details"]["additional_services"] = chosen_services
        st.session_state["conversation_step"] = 6  # Proceed to estimate
        st.rerun()


elif st.session_state["conversation_step"] == 6:
    st.write("**Bot:** Let me calculate the estimated cost of your move...")
    move_details = st.session_state["move_details"]
    payload = {
        "chat_id": st.session_state["chat_id"],
        "origin": move_details["origin"],
        "destination": move_details["destination"],
        "move_size": move_details["move_size"],
        "additional_services": move_details["additional_services"],
        "username": move_details["name"],
        "contact_no": move_details["contact_no"],
        "move_date": str(move_details["date"])
    }
    try:
        response = requests.post(f"{api_url}/estimate_cost", json=payload)
        response.raise_for_status()
        data = response.json()
        estimated_cost = data.get("estimated_cost", "No estimate available.")
        cost_msg = f"The estimated cost of your move is: {estimated_cost}"
        
        # Append to chat history
        st.session_state["chat_history"].append({"sender": "assistant", "content": cost_msg})
        
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
