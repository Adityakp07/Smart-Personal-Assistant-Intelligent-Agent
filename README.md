# Smart Personal Assistant – Intelligent Agent

## Introduction

The Smart Personal Assistant is a Python-based intelligent agent that understands user input and performs different actions based on the user's intent.

The agent follows the Perceive → Decide → Act model. It can handle greetings, date and time requests, calculations, notes, reminders, and unknown inputs.

## Features

- Greeting detection
- Date and time display
- Simple calculator
- Add and view notes
- Add and view reminders
- Persistent data storage using JSON
- Fallback response for unknown inputs
- Perceive → Decide → Act intelligent-agent model

## Intelligent Agent Model

The assistant follows the Perceive → Decide → Act cycle:

| Stage | Description |
|---|---|
| Perceive | Takes and processes the user's input. |
| Decide | Identifies the user's intent and selects an action. |
| Act | Performs the selected action and gives the response. |

This cycle continues until the user enters `exit`.

## Intent → Action Mapping

| Intent | Action |
|---|---|
| Greeting | Displays a greeting message |
| Date/Time | Displays the current date and time |
| Calculator | Performs a mathematical calculation |
| Add Note | Saves a note to the JSON file |
| View Notes | Displays all saved notes |
| Add Reminder | Saves a reminder to the JSON file |
| View Reminders | Displays all saved reminders |
| Unknown | Displays a fallback response |

## Persistent Data

The assistant uses a JSON file to store notes and reminders.

The data is stored in:

`data/assistant_data.json`

Example structure:

```json
{
    "notes": [],
    "reminders": []
}
Smart-Personal-Assistant-Intelligent-Agent/
│
├── data/
│   └── assistant_data.json
│
├── docs/
│   └── report.md
│
├── src/
│   └── main.py
│
├── tests/
│   └── test_main.py
│
├── README.md
└── requirements.txt