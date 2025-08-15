import json

def save_json(data, file):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)
