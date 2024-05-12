from dotenv import load_dotenv
import sys
import time

from notion_communicator import NotionCommunicator
from utils.yuh_pdf_converter import YuhPdfConverter

# load .env file
load_dotenv()

def calculate_expense_size(amount, currency):
    if currency == "DKK":
        amount = amount / 7.5
    if amount < 50:
        return "Small"
    elif amount < 200:
        return "Medium"
    elif amount < 2000:
        return "Large"
    else:
        return "Very Large"

pdf_base_path = "./pdfs/"
pdf_files = ["yuh_jan_2024.pdf", "yuh_feb_2024.pdf", "yuh_mar_2024.pdf", "yuh_apr_2024.pdf"]
pdf_files = [pdf_base_path + pdf_file for pdf_file in pdf_files]

print("Converting PDFs to transactions...")

pdf_converter = YuhPdfConverter(pdf_files)
all_transactions = pdf_converter.get_all_transactions()

print(all_transactions)

print("Adding transactions to Notion...")

# clear out the database
notion = NotionCommunicator()
notion.clear_notion_database()

for i, transaction in enumerate(all_transactions):
    print(f"Adding transaction {i+1}/{len(all_transactions)} to Notion...", end='\r')
    sys.stdout.flush()

    notion.add_transaction_to_notion(
        title=f"{transaction['amount']} {transaction['currency']} - {transaction['info']}",
        amount=transaction['amount'],
        currency=transaction['currency'],
        transaction_date=transaction['date'],
        expense_size=calculate_expense_size(transaction['amount'], transaction['currency'])
    )
    time.sleep(1 / 3.0) # notion's api is rate limited to 3 requests per second

print("All transactions added to Notion!")