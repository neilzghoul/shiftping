ShiftPing — WhatsApp Shift Availability Scheduler
ShiftPing automates shift scheduling for medical teams by sending WhatsApp messages to staff and automatically updating a Google Sheet when they respond. Built to solve a real pain point in clinical environments where shift coordination happens through fragmented group chats and manual spreadsheets.
What It Does
A manager runs the scheduler, which reads staff data from a Google Sheet and sends each person a WhatsApp message asking if they're available for an upcoming shift. When a staff member replies YES or NO, the sheet updates automatically in real time — including the response timestamp.
The Problem It Solves
Shift scheduling in hospitals and clinics is notoriously chaotic. Coordinators chase staff through WhatsApp groups, manually track responses in spreadsheets, and constantly reconcile conflicting information. ShiftPing replaces that process with a simple automated loop: ask → receive → record.
How It Works

Manager adds staff names, phone numbers, and shift details to the Google Sheet
Runs scheduler.py to send WhatsApp messages to all unconfirmed staff
Staff reply YES or NO on WhatsApp
webhook.py receives the reply via Twilio and updates the Google Sheet instantly

Tech Stack

Python — core scripting language
Twilio — WhatsApp messaging API
Google Sheets API + gspread — spreadsheet read/write
Flask — lightweight webhook server
ngrok — local tunnel for receiving webhook callbacks

Project Files

scheduler.py — reads the Google Sheet and sends WhatsApp shift requests
webhook.py — Flask server that receives replies and updates the sheet

Setup

Install dependencies: pip3 install twilio gspread google-auth flask
Add your Twilio credentials and Google Sheet ID to scheduler.py
Authenticate Google OAuth: run scheduler.py once to complete the browser flow
Start the webhook server: python3 webhook.py
Start ngrok: ngrok http 5001
Set the ngrok URL as the Twilio sandbox webhook
Run scheduler.py to send shift requests

Status
Working prototype tested with live WhatsApp messages and real-time Google Sheet updates. Next phase: web interface for managers, automated daily scheduling, and deployment to Google Cloud Run.
Built With
Python · Twilio · Google Sheets API · Flask · ngrok
