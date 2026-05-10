ShiftPing Pro — Product Brief
Problem
Nursing supervisors manage 20–30 staff across 3 daily shifts, 7 days a week. Each nurse has unique preferences, and manually reconciling competing requests while maintaining fairness is time-consuming, error-prone, and a persistent source of staff friction. There is no systematic way to track whose preferences were honored previously, making equitable scheduling nearly impossible at scale.
Users
Three distinct user types:
Nurses — submit shift preferences for an upcoming scheduling period. Need a simple, fast way to communicate availability and update their requests without learning new software or changing their habits significantly. Already live in WhatsApp.
Supervisors — define the scheduling period, receive all preference data, and build the final schedule. Need a clear overview of who wants what across all shifts and dates, and a way to prioritize fairly across the team over time.
Department administrators (future) — may manage multiple supervisors and departments. Out of scope for V1.
Current State
A blank paper schedule — divided into morning, evening, and night shifts across the week — is placed on the main nursing station counter. Nurses physically write their names into preferred slots whenever they pass by during their shift, until a submission deadline.
This paper-based process has several critical problems:

No editing — if a nurse makes a mistake or their availability changes, they cannot cleanly correct it. Crossing out or covering a pen-written name creates an illegible mess on a shared document that the supervisor must interpret.
No history — there is no record of past allocations, so tracking fairness over time is impossible.
No backup — if the paper is lost, damaged, or filled out illegibly, the entire data collection process breaks down.
No accessibility — nurses who are off-duty during the submission window may miss the deadline entirely simply because they weren't physically present at the desk.

After the deadline, the supervisor collects the paper and manually builds the schedule — a process complicated further by the corrections, scribbles, and illegible entries on the form.
Scheduling context (Israel)
The working week runs Sunday through Saturday. Supervisors typically schedule one week at a time, but occasionally request preferences for two weeks ahead — for example, when the supervisor will be away and needs the schedule prepared in advance. The system must support flexible scheduling periods of 7 or 14 days.
How It Works
For the supervisor:
The supervisor sends a WhatsApp message to initiate a new scheduling round, specifying the start and end dates:
NEW SCHEDULE 11/05 TO 17/05
The system creates the scheduling period and notifies all registered nurses that the preference window is open.
For nurses:
Nurses send WhatsApp messages using a three-tier preference system with date and shift type:

WANT 11 morning, 13 night — first priority, please schedule me here
CAN 12 evening, 14 morning — available if needed, no strong preference
NO 15 night, 16 morning — please do not schedule me here

Nurses can update or change their preferences at any time before the deadline — simply by sending a new message. The system automatically overwrites their previous entry.
For the supervisor:
A Google Sheet updates in real time, showing each nurse's preference (WANT / CAN / NO) for every shift slot across the scheduling period. The supervisor opens one sheet and sees the full picture — who wants what, who's flexible, who's unavailable — without collecting a single piece of paper.
Fairness tracking is built in: nurses who didn't receive their WANT shifts in one period are flagged for priority consideration in the next.
What Success Looks Like

Schedule is filled completely without manual data collection
Nurses can update preferences freely until the deadline without creating confusion
Nurses who submitted WANT requests receive them at a higher rate than random chance
Supervisors spend significantly less time chasing availability and deciphering handwriting
No risk of lost, damaged, or illegible schedules
The system handles both 7-day and 14-day scheduling periods seamlessly
Staff report feeling the process is fair and transparent

V1 Scope

Three-tier preference system (WANT / CAN / NO)
Date and shift-specific preferences (morning / evening / night)
Israeli week format (Sunday to Saturday)
Flexible scheduling periods (7 or 14 days)
WhatsApp input via Twilio
Real-time Google Sheets output with preference overview per nurse per shift slot
Supervisor-initiated scheduling rounds via WhatsApp
Preference updates — nurses can change their submission before the deadline
Basic fairness flag: tracks unmet WANT requests for next period priority

Out of Scope for V1

Automatic schedule generation — supervisor still makes final decisions
Mobile app or web dashboard — the sheet is the interface for now
Hebrew language support — English first, localize later
Integration with hospital HR or payroll systems
Five-tier or granular priority scales