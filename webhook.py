from flask import Flask, request, Response
import gspread
from datetime import datetime
from dotenv import load_dotenv
import os
import traceback
import logging
import re

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

SERVICE_ACCOUNT_FILE = '/Users/neilz./Documents/Projects/nurse-shift-scheduler/service_account.json'

SHIFT_KEYWORDS = ['MORNING', 'EVENING', 'NIGHT']
PREF_KEYWORDS = ['WANT', 'CAN', 'NO']

SHIFT_TIMES = {
    'Morning': '07:00–15:00',
    'Evening': '15:00–23:00',
    'Night':   '23:00–07:00',
}
SHIFT_EMOJI = {
    'Morning': '🌅',
    'Evening': '🌆',
    'Night':   '🌙',
}

def get_spreadsheet():
    gc = gspread.service_account(filename=SERVICE_ACCOUNT_FILE)
    return gc.open('Nurse Shift Scheduler')

def get_active_sheet():
    spreadsheet = get_spreadsheet()
    worksheets = spreadsheet.worksheets()
    for ws in worksheets:
        if ws.title not in ['Sheet1', 'Proposed Schedule']:
            return ws
    return None

def parse_preferences(message):
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

@app.route('/', methods=['GET'])
def home():
    return '''
    <h1>ShiftPing</h1>
    <p>WhatsApp-based nurse shift scheduler.</p>
    <p>Service is running.</p>
    ''', 200

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

@app.route('/schedule', methods=['GET'])
@app.route('/schedule', methods=['GET'])
def view_schedule():
    try:
        spreadsheet = get_spreadsheet()
        sheet = spreadsheet.worksheet('Proposed Schedule')
        all_data = sheet.get_all_values()

        if not all_data:
            return '<h2>No schedule available yet.</h2>', 200

        headers = all_data[0][1:]
        rows = all_data[1:]

        days = {}
        day_order = []
        for header in headers:
            parts = header.split(' ')
            if len(parts) < 3:
                continue
            day_label = f"{parts[0]} {parts[1]}"
            if day_label not in days:
                days[day_label] = {}
                day_order.append(day_label)
            days[day_label][parts[2]] = []

        for row in rows:
            row_label = row[0]
            for i, header in enumerate(headers):
                val = row[i + 1] if i + 1 < len(row) else ''
                if not val:
                    continue
                parts = header.split(' ')
                if len(parts) < 3:
                    continue
                day_label = f"{parts[0]} {parts[1]}"
                shift = parts[2]
                is_head = '(HEAD)' in val
                name = val.replace(' (HEAD)', '').strip()
                person_type = 'Assistant' if 'Assistant' in row_label else 'Nurse'
                days[day_label][shift].append({
                    'name': name,
                    'type': person_type,
                    'is_head': is_head,
                })

        if headers:
            first = headers[0].split(' ')
            last = headers[-1].split(' ')
            week_label = f"{first[0]} {first[1]} — {last[0]} {last[1]}"
        else:
            week_label = "This Week"

        SHIFT_TIMES = {
            'Morning': '07:00–15:00',
            'Evening': '15:00–23:00',
            'Night':   '23:00–07:00',
        }
        SHIFT_EMOJI = {
            'Morning': '🌅',
            'Evening': '🌆',
            'Night':   '🌙',
        }

        # Build grid HTML
        shifts_order = ['Morning', 'Evening', 'Night']

        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ShiftPing — Schedule</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f0f4f8; color: #1a1a2e; }}
  header {{ background: #1a1a2e; color: white; padding: 16px 24px; text-align: center; }}
  header h1 {{ font-size: 20px; }}
  header p {{ font-size: 13px; color: #aab; margin-top: 4px; }}
  .wrapper {{ overflow-x: auto; padding: 16px; }}
  table {{ border-collapse: collapse; min-width: 100%; white-space: nowrap; }}
  thead th {{ background: #1a1a2e; color: white; padding: 10px 14px; font-size: 13px; text-align: center; border-right: 1px solid #2a2a4e; }}
  thead th:first-child {{ background: #0f0f1a; min-width: 90px; }}
  tbody tr {{ border-bottom: 1px solid #e2e8f0; }}
  tbody tr:nth-child(odd) {{ background: white; }}
  tbody tr:nth-child(even) {{ background: #f8fafc; }}
  .shift-label {{ padding: 10px 14px; font-weight: 700; font-size: 13px; color: #2563eb; background: #eff6ff; border-right: 2px solid #bfdbfe; text-align: center; }}
  .shift-time {{ display: block; font-size: 10px; color: #888; font-weight: 400; }}
  .cell {{ padding: 8px 10px; text-align: center; border-right: 1px solid #e2e8f0; min-width: 110px; vertical-align: top; }}
  .person {{ font-size: 12px; padding: 2px 0; }}
  .head {{ font-weight: 700; color: #1a1a2e; }}
  .badge {{ display: inline-block; font-size: 9px; background: #fef3c7; color: #92400e; border-radius: 3px; padding: 1px 4px; margin-left: 3px; font-weight: 600; }}
  .asst {{ color: #999; font-size: 11px; }}
  footer {{ text-align: center; padding: 16px; font-size: 11px; color: #aaa; }}
</style>
</head>
<body>
<header>
  <h1>📋 Weekly Schedule</h1>
  <p>{week_label}</p>
</header>
<div class="wrapper">
<table>
  <thead>
    <tr>
      <th>Shift</th>'''

        for day_label in day_order:
            html += f'<th>{day_label}</th>'

        html += '</tr></thead><tbody>'

        for shift in shifts_order:
            emoji = SHIFT_EMOJI.get(shift, '')
            time = SHIFT_TIMES.get(shift, '')
            html += f'<tr><td class="shift-label">{emoji} {shift}<span class="shift-time">{time}</span></td>'

            for day_label in day_order:
                people = days[day_label].get(shift, [])
                html += '<td class="cell">'
                for person in people:
                    if person['type'] == 'Nurse':
                        head_class = ' head' if person['is_head'] else ''
                        head_badge = '<span class="badge">HEAD</span>' if person['is_head'] else ''
                        html += f'<div class="person{head_class}">👩‍⚕️ {person["name"]}{head_badge}</div>'
                    else:
                        html += f'<div class="person asst">🧹 {person["name"]}</div>'
                html += '</td>'

            html += '</tr>'

        html += '''</tbody>
</table>
</div>
<footer>ShiftPing • Meir Medical Center — Orthopedic B</footer>
</body></html>'''

        return html, 200

    except Exception as e:
        logger.error(f"Schedule view error: {e}")
        return f'<h2>Error loading schedule: {e}</h2>', 500
        
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)