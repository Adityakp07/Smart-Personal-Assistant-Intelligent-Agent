from datetime import datetime
import json
def load_data():
    with open("data/assistant_data.json", "r") as file:
        return json.load(file)


def save_data(data):
    with open("data/assistant_data.json", "w") as file:
        json.dump(data, file, indent=4)
def perceive(user_input):
    """Understand what the user wants."""
    return user_input.lower().strip()


def decide(user_input):
    """Decide which action to perform."""
    if "hello" in user_input or "hi" in user_input:
        return "greeting"
    elif "time" in user_input or "date" in user_input:
        return "datetime"
    elif "add note" in user_input:
        return "add_note"
    elif "show notes" in user_input or "view notes" in user_input:
        return "view_notes"
    elif "calculate" in user_input:
        return "calculator"
    else:
        return "unknown"


def act(intent):
    """Perform the selected action."""
    if intent == "greeting":
        return "Hello! How can I help you?"

    elif intent == "datetime":
        now = datetime.now()
        return now.strftime("Current date and time: %d-%m-%Y %I:%M %p")

    elif intent == "calculator":
        expression = input("Enter calculation: ")

        try:
            result = eval(expression, {"__builtins__": {}}, {})
            return f"Result: {result}"
        except:
            return "Sorry, I could not calculate that."

    elif intent == "add_note":
        note = input("Enter your note: ")

        data = load_data()
        data["notes"].append(note)
        save_data(data)

        return "Note saved successfully."

    elif intent == "view_notes":
        data = load_data()

        if not data["notes"]:
            return "You have no saved notes."

        return "Your notes:\n" + "\n".join(
            f"{i + 1}. {note}" for i, note in enumerate(data["notes"])
        )

    else:
        return "Sorry, I don't understand that request."
def run_agent():
    print("Smart Personal Assistant")
    print("Type 'exit' to stop.")

    while True:
        user_input = input("\nYou: ")

        if user_input.lower() == "exit":
            print("Assistant: Goodbye!")
            break

        # Perceive → Decide → Act
        perceived_input = perceive(user_input)
        intent = decide(perceived_input)
        response = act(intent)

        print("Assistant:", response)


if __name__ == "__main__":
    run_agent()