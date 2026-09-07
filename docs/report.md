# Smart Personal Assistant – Intelligent Agent

## 1. Objective

To develop a simple intelligent agent that understands user inputs, identifies the user's intent, and performs the appropriate action.

## 2. Introduction

The Smart Personal Assistant is a Python-based intelligent agent designed to interact with users through text input. It recognizes different types of requests and performs suitable actions based on the detected intent.

## 3. Intelligent Agent Architecture

The system follows the Perceive → Decide → Act model.

- **Perceive:** Receives and processes the user's input.
- **Decide:** Identifies the user's intent and selects the appropriate action.
- **Act:** Performs the selected action and provides a response.

## 4. Implemented Intents

The assistant supports the following intents:

1. Greeting
2. Date and Time
3. Calculator
4. Add Note
5. View Notes
6. Add Reminder
7. View Reminders
8. Unknown Input / Fallback

## 5. Intent → Action Mapping

| Intent | Action |
|---|---|
| Greeting | Displays a greeting |
| Date and Time | Displays the current date and time |
| Calculator | Performs a calculation |
| Add Note | Saves a note |
| View Notes | Displays saved notes |
| Add Reminder | Saves a reminder |
| View Reminders | Displays saved reminders |
| Unknown | Provides a fallback response |

## 6. Procedure / Working

1. The user enters a request.
2. The **Perceive** stage processes the input.
3. The **Decide** stage identifies the user's intent.
4. The **Act** stage performs the corresponding action.
5. The assistant displays the result.
6. The process repeats until the user enters `exit`.

## 7. Persistent Storage

Notes and reminders are stored in a JSON file named `assistant_data.json`.

The JSON file contains separate lists for notes and reminders. This allows saved information to remain available even after the program is closed and restarted.

## 8. Testing

Automated tests were created using `pytest` to verify intent detection.

The test suite contains 8 tests covering greetings, date/time, notes, reminders, calculator requests, and unknown input.

All tests passed successfully.

## 9. Applications

The assistant can be used for:

- Personal note management
- Reminder management
- Basic calculations
- Date and time information
- Demonstrating intelligent-agent concepts
- Learning Python-based AI agent design

## 10. Conclusion

The project demonstrates the basic working of an intelligent agent using Python. It successfully perceives user input, decides the appropriate intent, performs an action, and provides a response. Persistent JSON storage also allows notes and reminders to be retained between program sessions.

## 11. References

- Python Documentation
- Pytest Documentation
- Git and GitHub Documentation

