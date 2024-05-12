from googleapiclient.discovery import build

from utils.yuh_pdf_converter import YuhPdfConverter

pdf_path_list = ["pdfs/yuh_jan_2024.pdf", "pdfs/yuh_feb_2024.pdf", "pdfs/yuh_mar_2024.pdf", "pdfs/yuh_apr_2024.pdf"]
converter = YuhPdfConverter(pdf_path_list)
transactions = converter.get_all_transactions()

# Replace with your actual scopes and credentials setup
SCOPES = ['https://www.googleapis.com/auth/calendar']
creds = ""
service = build('calendar', 'v3', credentials=creds)

#for transaction in transactions:
transaction = transactions[0]
summary = f"{'+' if transaction['amount'] > 0 else ''}{transaction['amount']:.2f} {transaction['currency']} - {transaction['info']}"
description = f"Amount: {'+' if transaction['amount'] > 0 else ''}{transaction['amount']:.2f} {transaction['currency']}\nSaldo: {'+' if transaction['saldo'] > 0 else ''}{transaction['saldo']:.2f} {transaction['currency']}"
event = {
    'summary': summary,
    'description': description,  # Optional description
    'start': {
        'date': transaction['date'],
        'timeZone': 'Europe/Zurich',  # Set your appropriate time zone
    },
    'end': {
        'date': transaction['date'],
        'timeZone': 'Europe/Zurich',
    },
}

created_event = service.events().insert(calendarId='', body=event).execute()
print(f"Event created: {created_event.get('htmlLink')}")