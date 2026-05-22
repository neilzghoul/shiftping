import gspread
from twilio.rest import Client
from dotenv import load_dotenv
import os

load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_WHATSAPP_NUMBER = os.getenv('TWILIO_WHATSAPP_NUMBER')
SERVICE_ACCOUNT_FILE = os.getenv('SERVICE_ACCOUNT_FILE', '/Users/neilz./Documents/Projects/nurse-shift-scheduler/service_account.json')
SCHEDULE_URL = os.getenv('SCHEDULE_URL', 'http://localhost:8080/schedule')

SHIFT_TIMES = {
    'Morning': '07:00-15:00',
    'Evening': '15:00-23:00',
    'Night':   '23:00-07:00',
}

def get_all_staff():
    gc = gspread.service_account(filename=SERVICE_ACCOUNT_FILE)
    spreadsheet = gc.open('Nurse Shift Scheduler')
    worksheets = spreadsheet.worksheets()
    pref_sheet = None
    for ws in worksheets:
        if ws.title not in ['Sheet1', 'Proposed Schedule']:
            pref_sheet = ws
            break
    if not pref_sheet:
        return []
    rows = pref_sheet.get_all_values()[1:]
    staff = []
    for row in rows:
        if row[0] and row[1]:
            staff.append({
                'name': row[0],
                'phone': row[1],
                'role': row[2],
                'type': row[3],
            })
    return staff

def get_week_label():
    gc = gspread.service_account(filename=SERVICE_ACCOUNT_FILE)
    spreadsheet = gc.open('Nurse Shift Scheduler')
    sheet = spreadsheet.worksheet('Proposed Schedule')
    headers = sheet.row_values(1)[1:]
    if not headers:
        return "This Week"
    first = headers[0].split(' ')
    last = headers[-1].split(' ')
    return f"{first[0]} {first[1]} — {last[0]} {last[1]}"

def send_whatsapp(phone, message):
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    phone = phone.replace(' ', '').replace('-', '')
    if not phone.startswith('+'):
        phone = '+' + phone
    try:
        msg = client.messages.create(
            body=message,
            from_=TWILIO_WHATSAPP_NUMBER,
            to=f'whatsapp:{phone}'
        )
        print(f"✅ Sent to {phone}: {msg.sid}")
    except Exception as e:
        print(f"❌ Failed to send to {phone}: {e}")

def publish_schedule():
    print("📤 Reading proposed schedule...")
    week_label = get_week_label()

    message = (
        f"📋 *Weekly Schedule — {week_label}* is ready!\n\n"
        f"View your schedule here:\n{SCHEDULE_URL}\n\n"
        f"💬 To request a shift swap, reply:\n"
        f"SWAP [your name] WITH [other name] [day] [shift]\n"
        f"Example: SWAP Dana Levi WITH Sarah Cohen 12 Morning"
    )

    print("\n=== MESSAGE PREVIEW ===\n")
    print(message)
    print("\n=======================\n")

    confirm = input("Send this to all staff? (yes/no): ").strip().lower()
    if confirm != 'yes':
        print("Cancelled.")
        return

    staff = get_all_staff()
    if not staff:
        print("❌ No staff found.")
        return

    print(f"\n📨 Sending to {len(staff)} staff members...")
    for person in staff:
        send_whatsapp(person['phone'], message)

    print("\n✅ Schedule published to all staff.")

if __name__ == '__main__':
    publish_schedule()