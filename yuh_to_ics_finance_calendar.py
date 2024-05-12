from ics import Calendar, Event
from datetime import datetime, timedelta

from utils.yuh_pdf_converter import YuhPdfConverter

pdf_path_list = ["pdfs/yuh_jan_2024.pdf", "pdfs/yuh_feb_2024.pdf", "pdfs/yuh_mar_2024.pdf", "pdfs/yuh_apr_2024.pdf"]
converter = YuhPdfConverter(pdf_path_list)
transactions = converter.get_all_transactions()

# Create a new calendar
calendar = Calendar()

# Add events (transactions) to the calendar
for transaction in transactions:
    event = Event()
    event.name = f"{'+' if transaction['amount'] > 0 else ''}{transaction['amount']:.2f} {transaction['currency']} - {transaction['info']}"

    # Format the date string (YYYY-MM-DD) into a datetime object
    date_obj = datetime.strptime(transaction['date'], '%Y-%m-%d').date()
    event.begin = date_obj 
    event.make_all_day()
    
    event.description = f"Amount: {'+' if transaction['amount'] > 0 else ''}{transaction['amount']:.2f} {transaction['currency']}\nSaldo: {'+' if transaction['saldo'] > 0 else ''}{transaction['saldo']:.2f} {transaction['currency']}"
    calendar.events.add(event)

# Write the ICS file
with open('yuh_transactions_calendar.ics', 'w') as file:
    file.writelines(calendar.serialize_iter())