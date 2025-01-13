import redis
from config import Config

class RedisManager:
    def __init__(self):
        self.client = redis.StrictRedis(
            host=Config.REDIS_HOST,
            port=Config.REDIS_PORT,
            password=Config.REDIS_PASSWORD,
            decode_responses=True
        )

    def init_chat(self, chat_id, username=None, contact_no=None):
        """
        Initialize a chat session with user details.
        """
        chat_key = f"chat:{chat_id}"  # Use chat_id passed as an argument
        if not self.client.exists(chat_key):
            self.client.hset(chat_key, mapping={
                "username": username or "Unknown",
                "contact_no": contact_no or "Unknown",
                "index": 0
            })

    def add_message(self, chat_id, user_message, assistant_message):
        """
        Add user and assistant messages to Redis.
        """
        chat_key = f"chat:{chat_id}"  # Use chat_id passed as an argument
        index = int(self.client.hget(chat_key, "index") or 0)

        self.client.hset(chat_key, f"message:{index}", f"User: {user_message}")
        index += 1
        self.client.hset(chat_key, f"message:{index}", f"Assistant: {assistant_message}")
        index += 1

        self.client.hset(chat_key, "index", index)

    def get_chat_history(self, chat_id):
        """
        Retrieve the chat history for a given chat ID.
        """
        chat_key = f"chat:{chat_id}"  # Use chat_id passed as an argument
        if not self.client.exists(chat_key):
            raise ValueError(f"Chat ID {chat_id} does not exist.")

        username = self.client.hget(chat_key, "username")
        contact_no = self.client.hget(chat_key, "contact_no")
        index = int(self.client.hget(chat_key, "index") or 0)

        messages = [self.client.hget(chat_key, f"message:{i}") for i in range(index)]

        return {
            "username": username,
            "contact_no": contact_no,
            "messages": messages
        }
    def store_move_details(self, chat_id, move_details, estimated_cost):
        """
        Store all move-related details in Redis.
        """
        chat_key = f"chat:{chat_id}"
        self.client.hset(chat_key, mapping={
            "username": move_details.get("name", "Unknown"),
            "contact_no": move_details.get("contact_no", "Unknown"),
            "origin": move_details.get("origin", "Unknown"),
            "destination": move_details.get("destination", "Unknown"),
            "move_date": str(move_details.get("date", "Unknown")),
            "move_size": move_details.get("move_size", "Unknown"),
            "additional_services": ", ".join(move_details.get("additional_services", [])),
            "estimated_cost": estimated_cost
        })
    def update_context(self, chat_id, key, value):
        """
        Update a specific context key for the given chat session.
        """
        chat_key = f"chat:{chat_id}"
        self.client.hset(chat_key, key, value)

    def get_context(self, chat_id, key):
        """
        Retrieve a specific context key for the given chat session.
        """
        chat_key = f"chat:{chat_id}"
        return self.client.hget(chat_key, key)


