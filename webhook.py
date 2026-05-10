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

SHIFT_KEYWORDS = ['MORNING', 'EVENING', 'NIGHT']
PREF_KEYWORDS = ['WANT', 'CAN', 'NO']

def get_sheet(sheet_name):
    credentials, _ = google.auth.default(scopes=[
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ])
    gc = gspread.authorize(credentials)
    return gc.open('Nurse Shift Scheduler').worksheet(sheet_name)

def get_active_sheet():
    credentials, _ = google.auth.default(scopes=[
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ])
    gc = gspread.authorize(credentials)
    spreadsheet = gc.open('Nurse Shift Scheduler')
    worksheets = spreadsheet.worksheets()
    for ws in worksheets:
        if ws.title != 'Sheet1':
            return ws
    return None

def parse_preferences(message):
    """
    Parse messages like:
    WANT 10 morning, 13 night
    CAN 11 evening, 14 morning
    NO 15 night, 16 morning
    Returns list of tuples: [(day, shift, preference)]
    """
    preferences = []
    lines = message.strip().upper().split('\n')
    
    for line in lines:
        line = line.strip()
        current_pref = None
        
        for pref in PREF_KEYWORDS:
            if line.startswith(pref):
                current_pref = pref
                line = line.replace(pref, '').strip()
                break
        
        if not current_pref:
            continue
        
        entries = line.split(',')
        for entry in entries:
            entry = entry.strip()
            day_match = re.search(r'\d+', entry)
            if not day_match:
                continue
            day = int(day_match.group())
            
            shift = None
            for s in SHIFT_KEYWORDS:
                if s in entry:
                    shift = s.capitalize()
                    break
            
            if day and shift:
                preferences.append((day, shift, current_pref))
    
    return preferences

def find_nurse_row(sheet, from_number):
    phones = sheet.col_values(2)
    for i, phone in enumerate(phones):
        clean_phone = phone.replace('+', '').replace(' ', '')
        if clean_phone == from_number:
            return i + 1
    return None

def find_column(sheet, day, shift):
    headers = sheet.row_values(1)
    for i, header in enumerate(headers):
        parts = header.split(' ')
        if len(parts) >= 3:
            header_day = parts[1]
            header_shift = parts[2]
            if str(day) == header_day and shift == header_shift:
                return i + 1
    return None

@app.route('/webhook', methods=['POST', 'GET'])
def webhook():
    try:
        incoming_msg = request.form.get('Body', '').strip()
        from_number = request.form.get('From', '').replace('whatsapp:', '').replace('+', '')
        
        logger.info(f"Received: '{incoming_msg}' from '{from_number}'")
        
        if incoming_msg and from_number:
            sheet = get_active_sheet()
            if not sheet:
                logger.error("No active sheet found")
            else:
                logger.info(f"Using sheet: {sheet.title}")
                nurse_row = find_nurse_row(sheet, from_number)
                
                if nurse_row is None:
                    logger.info(f"Nurse not found for {from_number}")
                else:
                    preferences = parse_preferences(incoming_msg)
                    logger.info(f"Parsed: {preferences}")
                    
                    for day, shift, pref_type in preferences:
                        col = find_column(sheet, day, shift)
                        if col:
                            sheet.update_cell(nurse_row, col, pref_type)
                            logger.info(f"Updated day {day} {shift} to {pref_type}")
                        else:
                            logger.info(f"Column not found for day {day} {shift}")

    except Exception as e:
        logger.error(f"Error: {e}")
        logger.error(traceback.format_exc())
    
    return Response('<?xml version="1.0" encoding="UTF-8"?><Response></Response>', 
                   mimetype='text/xml', status=200)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)