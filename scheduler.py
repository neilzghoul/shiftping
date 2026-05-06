import gspread
from twilio.rest import Client
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

# Twilio setup
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_WHATSAPP_NUMBER = os.getenv('TWILIO_WHATSAPP_NUMBER')

# Google Sheet ID
SHEET_ID = os.getenv('SHEET_ID')

def send_shift_request(nurse_name, nurse_phone, shift_date, shift_time):
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    message = client.messages.create(
        body=f"Hi {nurse_name}, are you available for the {shift_time} shift on {shift_date}? Please reply YES or NO.",
        from_=TWILIO_WHATSAPP_NUMBER,
        to=f'whatsapp:{nurse_phone}'
    )
    print(f"Message sent to {nurse_name}: {message.sid}")

def send_requests_to_all_nurses():
    gc = gspread.oauth()
    sheet = gc.open('Nurse Shift Scheduler').sheet1
    nurses = sheet.get_all_records()
    
    for nurse in nurses:
        if nurse['Available'] == '':
            send_shift_request(
                nurse['Name'],
                nurse['Phone'],
                nurse['Shift Date'],
                nurse['Shift Time']
            )

if __name__ == '__main__':
    send_requests_to_all_nurses()