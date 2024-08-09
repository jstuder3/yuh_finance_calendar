from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import os
import sys

from utils.yuh_pdf_converter import YuhPdfConverter

from dotenv import load_dotenv
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
print("Finished!")