from flask import Flask, request, Response
import gspread
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

SHEET_ID = os.getenv('SHEET_ID')

@app.route('/webhook', methods=['POST', 'GET'])
def webhook():
    try:
        incoming_msg = request.form.get('Body', '').strip().upper()
        from_number = request.form.get('From', '').replace('whatsapp:', '').replace('+', '')
        
        print(f"Received: '{incoming_msg}' from '{from_number}'")
        
        if incoming_msg and from_number:
            gc = gspread.oauth()
            sheet = gc.open('Nurse Shift Scheduler').sheet1
            nurses = sheet.get_all_records()
            
            for i, nurse in enumerate(nurses):
                nurse_phone = str(nurse['Phone']).replace('+', '').replace(' ', '')
                print(f"Comparing {nurse_phone} with {from_number}")
                if nurse_phone == from_number:
                    row = i + 2
                    sheet.update_cell(row, 5, incoming_msg)
                    sheet.update_cell(row, 6, datetime.now().strftime('%Y-%m-%d %H:%M'))
                    print(f"Updated {nurse['Name']}: {incoming_msg}")
                    break
    except Exception as e:
        print(f"Error: {e}")
    
    return Response('<?xml version="1.0" encoding="UTF-8"?><Response></Response>', 
                   mimetype='text/xml', status=200)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)