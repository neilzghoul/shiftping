import gspread

SERVICE_ACCOUNT_FILE = os.getenv('SERVICE_ACCOUNT_FILE', '/Users/neilz./Documents/Projects/nurse-shift-scheduler/service_account.json')

SHIFT_REQUIREMENTS = {
    'Morning': {'nurses': 4, 'assistants': 2},
    'Evening': {'nurses': 2, 'assistants': 1},
    'Night':   {'nurses': 2, 'assistants': 1},
}

def get_spreadsheet():
    gc = gspread.service_account(filename=SERVICE_ACCOUNT_FILE)
    return gc.open('Nurse Shift Scheduler')

def get_active_preferences_sheet():
    spreadsheet = get_spreadsheet()
    worksheets = spreadsheet.worksheets()
    for ws in worksheets:
        if ws.title not in ['Sheet1', 'Proposed Schedule']:
            return ws
    return None

def generate_schedule():
    pref_sheet = get_active_preferences_sheet()
    if not pref_sheet:
        print("No preferences sheet found.")
        return

    all_data = pref_sheet.get_all_values()
    headers = all_data[0]
    rows = all_data[1:]

    # Parse staff
    staff = []
    for row in rows:
        if not row[0]:
            continue
        staff.append({
            'name': row[0],
            'phone': row[1],
            'role': row[2],   # Senior / Junior / Assistant
            'type': row[3],   # Nurse / Assistant
        })

    # Parse shift columns (col index 4 onwards)
    shift_columns = []
    for i, header in enumerate(headers[4:], start=4):
        parts = header.split(' ')
        if len(parts) >= 3:
            shift_columns.append({
                'col_index': i,
                'day_name': parts[0],
                'day_num': parts[1],
                'shift': parts[2],
                'header': header,
            })

    # Build preference map: {staff_name: {col_index: WANT/CAN/NO}}
    pref_map = {}
    for row in rows:
        if not row[0]:
            continue
        name = row[0]
        pref_map[name] = {}
        for sc in shift_columns:
            col_i = sc['col_index']
            val = row[col_i] if col_i < len(row) else ''
            pref_map[name][col_i] = val if val in ['WANT', 'CAN', 'NO'] else ''

    # Generate schedule
    schedule = {}

    for sc in shift_columns:
        col_i = sc['col_index']
        shift = sc['shift']
        req = SHIFT_REQUIREMENTS.get(shift, {'nurses': 2, 'assistants': 1})

        def rank(person, col_i=col_i):
            pref = pref_map[person['name']].get(col_i, '')
            if pref == 'WANT':
                return 0
            elif pref == 'CAN':
                return 1
            elif pref == 'NO':
                return 3
            else:
                return 2  # No response = treat like CAN

        nurses = [s for s in staff if s['type'] == 'Nurse']
        assistants = [s for s in staff if s['type'] == 'Assistant']

        nurses_sorted = sorted(nurses, key=rank)
        assistants_sorted = sorted(assistants, key=rank)

        # Pick nurses (exclude NO if possible)
        available_nurses = [n for n in nurses_sorted if pref_map[n['name']].get(col_i, '') != 'NO']
        if len(available_nurses) < req['nurses']:
            available_nurses = nurses_sorted

        assigned_nurses = available_nurses[:req['nurses']]

        # Pick head shift nurse from seniors in assigned nurses
        seniors = [n for n in assigned_nurses if n['role'] == 'Senior']
        head = seniors[0] if seniors else assigned_nurses[0] if assigned_nurses else None

        # Pick assistants
        available_asst = [a for a in assistants_sorted if pref_map[a['name']].get(col_i, '') != 'NO']
        if len(available_asst) < req['assistants']:
            available_asst = assistants_sorted
        assigned_asst = available_asst[:req['assistants']]

        schedule[col_i] = {
            'header': sc['header'],
            'nurses': assigned_nurses,
            'head': head,
            'assistants': assigned_asst,
        }

    # Print proposed schedule
    print("\n=== PROPOSED SCHEDULE ===\n")
    for col_i, slot in schedule.items():
        print(f"📅 {slot['header']}")
        for n in slot['nurses']:
            head_marker = " ⭐ HEAD" if slot['head'] and n['name'] == slot['head']['name'] else ""
            print(f"   👩‍⚕️ {n['name']}{head_marker}")
        for a in slot['assistants']:
            print(f"   🧹 {a['name']} (Assistant)")
        print()

    # Write to Proposed Schedule sheet
    try:
        spreadsheet = get_spreadsheet()

        try:
            old = spreadsheet.worksheet('Proposed Schedule')
            spreadsheet.del_worksheet(old)
        except:
            pass

        out_sheet = spreadsheet.add_worksheet(title='Proposed Schedule', rows=50, cols=50)

        headers_out = ['Shift'] + [slot['header'] for _, slot in schedule.items()]
        rows_out = []

        for role_label, role_filter in [('Nurses', 'Nurse'), ('Assistants', 'Assistant')]:
            max_count = max(
                (len(slot['nurses']) if role_filter == 'Nurse' else len(slot['assistants']))
                for slot in schedule.values()
            ) if schedule else 0

            for i in range(max_count):
                row = []
                for col_i, slot in schedule.items():
                    people = slot['nurses'] if role_filter == 'Nurse' else slot['assistants']
                    if i < len(people):
                        person = people[i]
                        label = person['name']
                        if role_filter == 'Nurse' and slot['head'] and person['name'] == slot['head']['name']:
                            label += ' (HEAD)'
                        row.append(label)
                    else:
                        row.append('')
                rows_out.append([f'{role_label} {i+1}'] + row)

        out_sheet.update([headers_out] + rows_out)
        print("✅ Proposed Schedule written to Google Sheet.")

    except Exception as e:
        print(f"❌ Could not write to sheet: {e}")

if __name__ == '__main__':
    generate_schedule()