import pickle

data = {
    "user_id": 42,
    "username": "codemaster_99",
    "settings": ["dark_mode", "notifications_on"]
}

# --- SERIALIZING (Writing) ---
with open("user_data.pkl", "wb") as file:
    pickle.dump(data, file)
    print("Data serialized to user_data.pkl")

# --- DESERIALIZING (Reading) ---
with open("user_data.pkl", "rb") as file:
    loaded_data = pickle.load(file)
    print(f"Data deserialized: {loaded_data}")