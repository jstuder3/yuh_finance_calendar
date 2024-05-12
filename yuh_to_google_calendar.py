from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import os
import sys

from utils.yuh_pdf_converter import YuhPdfConverter

from dotenv import load_dotenv
load_dotenv()

pdf_path_list = ["pdfs/yuh_jan_2024.pdf", "pdfs/yuh_feb_2024.pdf", "pdfs/yuh_mar_2024.pdf", "pdfs/yuh_apr_2024.pdf"]
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
        flow = InstalledAppFlow.from_client_secrets_file('client_secrets.json', SCOPES)  
        creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open('token.json', 'w') as token:
        token.write(creds.to_json())

service = build('calendar', 'v3', credentials=creds)

# uncomment to find ID of your calendar
# calendars = service.calendarList().list().execute()

# for calendar_list_entry in calendars['items']:
#     print(f"Calendar Name: {calendar_list_entry['summary']}, ID: {calendar_list_entry['id']}")

# remove all events from the calendar, then add new events
page_token = None
while True:
    events_result = service.events().list(calendarId=CALENDAR_ID, pageToken=page_token).execute()  # Adjust calendarId if needed
    events = events_result.get('items', [])
    for i, event in enumerate(events):
        print(f"Deleting event {i+1}/{len(events)}...", end='\r')
        sys.stdout.flush()
        service.events().delete(calendarId=CALENDAR_ID, eventId=event['id']).execute()
    page_token = events_result.get('nextPageToken')
    if not page_token:
        break
print("All events deleted!")

color_map = {
    'small': 5,   # Example: Lavender
    'medium': 6,
    'large': 11,  # Example: Grape
    #'very_large': 11, # Example: Tomato
    "income": 10,
}

for i, transaction in enumerate(transactions):
    print(f"Adding event {i+1}/{len(transactions)}...", end='\r')
    sys.stdout.flush()
    
    event = {
        'summary': f"{'+' if transaction['amount'] > 0 else ''}{transaction['amount']:.2f} {transaction['currency']} - {transaction['info']}",
        'start': {'date': transaction['date'], 'timeZone': 'Europe/Zurich'},
        'end': {'date': transaction['date'], 'timeZone': 'Europe/Zurich'},
        'description':f"Amount: {'+' if transaction['amount'] > 0 else ''}{transaction['amount']:.2f} {transaction['currency']}\nSaldo: {'+' if transaction['saldo'] > 0 else ''}{transaction['saldo']:.2f} {transaction['currency']}"
    }

    amount = transaction['amount']
    if amount >= 0:
        event["colorId"] = color_map["income"]
    if amount < 0:
        if amount > -50:
            event['colorId'] = color_map['small']
        elif amount > -200:
            event['colorId'] = color_map['medium']
        else:
            event['colorId'] = color_map['large']

    # print(event)
    created_event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
    
print("Finished!")