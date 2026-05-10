from flask import Flask, request, Response
import gspread
from datetime import datetime
from dotenv import load_dotenv
import os
import traceback
import logging
import google.auth
import re

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def get_sheet(sheet_name):
    credentials, _ = google.auth.default(scopes=[
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ])
    gc = gspread.authorize(credentials)
    return gc.open('Nurse Shift Scheduler').worksheet(sheet_name)

def parse_preferences(message):
    """
    Parse messages like:
    WANT 5, 10, 15
    CAN 3, 8
    NO 20, 25
    Returns dict: {day_number: preference_type}
    """
    preferences = {}
    lines = message.strip().upper().split('\n')
    
    for line in lines:
        line = line.strip()
        if line.startswith('WANT'):
            pref_type = 'WANT'
            dates_str = line.replace('WANT', '').strip()
        elif line.startswith('CAN'):
            pref_type = 'CAN'
            dates_str = line.replace('CAN', '').strip()
        elif line.startswith('NO'):
            pref_type = 'NO'
            dates_str = line.replace('NO', '').strip()
        else:
            continue
        
        dates = re.findall(r'\d+', dates_str)
        for date in dates:
            day = int(date)
            if 1 <= day <= 31:
                preferences[day] = pref_type
    
    return preferences

def find_nurse_row(sheet, from_number):
    """Find the row index of a nurse by phone number"""
    phones = sheet.col_values(2)
    for i, phone in enumerate(phones):
        clean_phone = phone.replace('+', '').replace(' ', '')
        if clean_phone == from_number:
            return i + 1
    return None

def get_date_column(sheet, day):
    """Find the column number for a given day of the month"""
    headers = sheet.row_values(1)
    target = f"May {day}"
    for i, header in enumerate(headers):
        if header == target:
            return i + 1
    return None

@app.route('/webhook', methods=['POST', 'GET'])
def webhook():
    try:
        incoming_msg = request.form.get('Body', '').strip()
        from_number = request.form.get('From', '').replace('whatsapp:', '').replace('+', '')
        
        logger.info(f"Received: '{incoming_msg}' from '{from_number}'")
        
        if incoming_msg and from_number:
            sheet = get_sheet('May 2026 Preferences')
            
            nurse_row = find_nurse_row(sheet, from_number)
            if nurse_row is None:
                logger.info(f"Nurse not found for number {from_number}")
            else:
                preferences = parse_preferences(incoming_msg)
                logger.info(f"Parsed preferences: {preferences}")
                
                for day, pref_type in preferences.items():
                    col = get_date_column(sheet, day)
                    if col:
                        sheet.update_cell(nurse_row, col, pref_type)
                        logger.info(f"Updated day {day} to {pref_type}")
    
    except Exception as e:
        logger.error(f"Error: {e}")
        logger.error(traceback.format_exc())
    
    return Response('<?xml version="1.0" encoding="UTF-8"?><Response></Response>', 
                   mimetype='text/xml', status=200)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)