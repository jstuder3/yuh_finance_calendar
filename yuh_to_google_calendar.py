import os
import sys
import calendar

from collections import defaultdict
from datetime import datetime
from dotenv import load_dotenv

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

from utils.yuh_pdf_converter import YuhPdfConverter

load_dotenv()

def listdir_fullpath(d):
    return [os.path.join(d, f) for f in os.listdir(d) if ".gitkeep" not in f]

# pdf_path_list = ["pdfs/yuh_jan_2024.pdf", "pdfs/yuh_feb_2024.pdf", "pdfs/yuh_mar_2024.pdf", "pdfs/yuh_apr_2024.pdf"]
pdf_base_path = os.getenv("PDF_PATH") if os.getenv("PDF_PATH") else "pdfs"
pdf_path_list = list(filter(lambda x: x.endswith(".pdf"), listdir_fullpath(pdf_base_path)))
print(f"Found {len(pdf_path_list)} pdf files in pdfs folder!")
converter = YuhPdfConverter(pdf_path_list)
transactions = converter.get_all_transactions()

# Replace with your actual scopes and credentials setup
SCOPES = ['https://www.googleapis.com/auth/calendar']
CLIENT_SECRET_FILE = 'client_secret.json'
creds=None
CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID")

if os.path.exists('token.json'):  # Check for existing token
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        # Use client_secrets.json here
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)  
        creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open('token.json', 'w') as token:
        token.write(creds.to_json())

service = build('calendar', 'v3', credentials=creds)

# uncomment to find ID of your calendar
# calendars = service.calendarList().list().execute()
# for calendar_list_entry in calendars['items']:
#     print(f"Calendar Name: {calendar_list_entry['summary']}, ID: {calendar_list_entry['id']}")

color_map = {
    'small': 5,
    'medium': 6,
    'large': 11,
    "income": 10,
}

def get_color(amount, currency):
    if currency == "DKK":
        amount = amount / 7.5
    if amount >= 0:
        return color_map["income"]
    if amount < 0:
        if amount > -50:
            return color_map['small']
        elif amount > -200:
            return color_map['medium']
        else:
            return color_map['large']



# Initialize dictionaries to store sums of income and expenses for each month
monthly_income = defaultdict(lambda: defaultdict(float))
monthly_expenses = defaultdict(lambda: defaultdict(float))

# Process each transaction
for transaction in transactions:
    # Extract the month and year from the transaction date
    date = datetime.strptime(transaction['date'], '%Y-%m-%d')
    month_year = date.strftime('%Y-%m')
    currency = transaction['currency']

    # Update the sums based on the transaction amount
    if transaction['amount'] > 0:
        monthly_income[month_year][currency] += transaction['amount']
    else:
        monthly_expenses[month_year][currency] += abs(transaction['amount'])

# Print out the sums for each month and currency
print("Monthly Income and Expenses:")
for month_year in sorted(set(monthly_income.keys()).union(monthly_expenses.keys())):
    print(f"{month_year}:")
    currencies = set(monthly_income[month_year].keys()).union(monthly_expenses[month_year].keys())
    for currency in currencies:
        income = monthly_income[month_year][currency]
        expenses = -monthly_expenses[month_year][currency]
        print(f"  {currency}: Income = {income:.2f}, Expenses = {expenses:.2f}")

page_token = None
all_existing_events = []
print("Fetching all existing events...")
while True:
    existing_events = service.events().list(calendarId=CALENDAR_ID, pageToken=page_token).execute()
    for i, event in enumerate(existing_events["items"]):
        sys.stdout.flush()
        all_existing_events.append(event)
    page_token = existing_events.get('nextPageToken')
    if not page_token:
        break
event_hashes = [hash(event['summary'] + ' ' + event['description']) for event in all_existing_events]
print(f"All events fetched! Found {len(all_existing_events)} existing events in total!")

# optional: delete all previously existing events
delete_all_events = False
if delete_all_events:
    for i, event in enumerate(all_existing_events):
        print(f"Deleting event {i+1}/{len(all_existing_events)}...", end='\r')
        sys.stdout.flush()
        service.events().delete(calendarId=CALENDAR_ID, eventId=event['id']).execute()
    event_hashes = []

for i, transaction in enumerate(transactions):
    print(f"Adding event {i+1}/{len(transactions)}...", end='\r')
    sys.stdout.flush()
    
    event = {
        'summary': f"{'+' if transaction['amount'] > 0 else ''}{transaction['amount']:.2f} {transaction['currency']} - {transaction['info']}",
        'start': {'date': transaction['date'], 'timeZone': 'Europe/Zurich'},
        'end': {'date': transaction['date'], 'timeZone': 'Europe/Zurich'},
        'description':f"Amount: {'+' if transaction['amount'] > 0 else ''}{transaction['amount']:.2f} {transaction['currency']}\nSaldo: {'+' if transaction['saldo'] > 0 else ''}{transaction['saldo']:.2f} {transaction['currency']}"
    }
    
    # skip if event is already in calendar
    event_hash = hash(event['summary'] + ' ' + event['description'])
    if event_hash in event_hashes:
        continue

    event["colorId"] = get_color(transaction['amount'], transaction["currency"])
    
    # print(event)
    created_event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()

print()
print("Finished adding regular events. Adding monthly summaries now...")

for month_year in sorted(set(monthly_income.keys()).union(monthly_expenses.keys())):
    currencies = set(monthly_income[month_year].keys()).union(monthly_expenses[month_year].keys())
    
    # Calculate the last day of the month
    year, month = map(int, month_year.split('-'))
    last_day = calendar.monthrange(year, month)[1]
    last_date = datetime(year, month, last_day).strftime('%Y-%m-%d')

    # Create the description for the summarized monthly expenses
    expense_description = "\n".join([f"{currency}: {monthly_expenses[month_year][currency]:.2f}" for currency in monthly_expenses[month_year]])
    income_description = "\n".join([f"{currency}: {monthly_income[month_year][currency]:.2f}" for currency in monthly_income[month_year]])

    # Check if the expense summary event already exists
    expense_summary = f"Monthly Expenses Summary for {month_year}"
    expense_event_exists = any(event['summary'] == expense_summary and event['start']['date'] == last_date for event in all_existing_events)

    if not expense_event_exists:
        # Create a calendar event for the summarized monthly expenses
        expense_event = {
            'summary': expense_summary,
            'start': {'date': last_date, 'timeZone': 'Europe/Zurich'},
            'end': {'date': last_date, 'timeZone': 'Europe/Zurich'},
            'description': f"Total expenses for {month_year}:\n{expense_description}",
            'colorId': color_map['large']
        }

        # Add the event to the Google Calendar
        created_event = service.events().insert(calendarId=CALENDAR_ID, body=expense_event).execute()

    # Check if the income summary event already exists
    income_summary = f"Monthly Income Summary for {month_year}"
    income_event_exists = any(event['summary'] == income_summary and event['start']['date'] == last_date for event in all_existing_events)

    if not income_event_exists:
        # Create a calendar event for the summarized monthly income
        income_event = {
            'summary': income_summary,
            'start': {'date': last_date, 'timeZone': 'Europe/Zurich'},
            'end': {'date': last_date, 'timeZone': 'Europe/Zurich'},
            'description': f"Total income for {month_year}:\n{income_description}",
            'colorId': color_map['income']
        }

        # Add the event to the Google Calendar
        created_event = service.events().insert(calendarId=CALENDAR_ID, body=income_event).execute()

print("Finished adding summarized monthly income and expenses to the calendar.")