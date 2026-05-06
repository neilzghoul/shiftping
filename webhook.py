from flask import Flask, request, Response
import gspread
from datetime import datetime
from dotenv import load_dotenv
import os
import traceback
import logging
import google.auth

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

SHEET_ID = os.getenv('SHEET_ID')

def get_sheet():
    credentials, _ = google.auth.default(scopes=[
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ])
    gc = gspread.authorize(credentials)
    return gc.open('Nurse Shift Scheduler').sheet1

@app.route('/webhook', methods=['POST', 'GET'])
def webhook():
    try:
        incoming_msg = request.form.get('Body', '').strip().upper()
        from_number = request.form.get('From', '').replace('whatsapp:', '').replace('+', '')
        
        logger.info(f"Received: '{incoming_msg}' from '{from_number}'")
        
        if incoming_msg and from_number:
            sheet = get_sheet()
            nurses = sheet.get_all_records()
            
            for i, nurse in enumerate(nurses):
                nurse_phone = str(nurse['Phone']).replace('+', '').replace(' ', '')
                logger.info(f"Comparing {nurse_phone} with {from_number}")
                if nurse_phone == from_number:
                    row = i + 2
                    sheet.update_cell(row, 5, incoming_msg)
                    sheet.update_cell(row, 6, datetime.now().strftime('%Y-%m-%d %H:%M'))
                    logger.info(f"Updated {nurse['Name']}: {incoming_msg}")
                    break
    except Exception as e:
        logger.error(f"Error: {e}")
        logger.error(traceback.format_exc())
    
    return Response('<?xml version="1.0" encoding="UTF-8"?><Response></Response>', 
                   mimetype='text/xml', status=200)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)