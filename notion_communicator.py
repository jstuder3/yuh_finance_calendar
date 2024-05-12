import notion_client
import sys

import os

# Notion Configuration (replace with your own)
class NotionCommunicator:
    def __init__(self):
        # to use your own notion token and database, create a .env file in the same directory as this file and add the following lines:
        # NOTION_TOKEN=ADD_YOUR_NOTION_TOKEN_HERE
        # DATABASE_ID=ADD_YOUR_DATABASE_ID_HERE

        self.NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
        self.DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")
        self.client = notion_client.Client(auth=self.NOTION_TOKEN)

        # Example usage:

        # notion = NotionCommunicator()
        # notion.clear_notion_database()
        # notion.add_transaction_to_notion(
        #     title="24.25 CHF - Grocery Shopping",
        #     amount=24.25,   
        #     currency="CHF", 
        #     transaction_date="2024-05-10",
        #     tag="Small"
        # )

    def clear_notion_database(self):
        # Get all pages in the database
        pages = []
        has_more = True
        next_cursor = None
        while has_more:
            query_result = self.client.databases.query(
                database_id=self.DATABASE_ID,
                start_cursor=next_cursor
            )
            pages.extend(query_result["results"])
            has_more = query_result["has_more"]
            next_cursor = query_result["next_cursor"]

        # Archive (delete) all pages
        for i, page in enumerate(pages):
            print(f"Deleting page {i+1}/{len(pages)}...", end='\r')
            sys.stdout.flush()
            self.client.blocks.delete(block_id=page["id"])

    def add_transaction_to_notion(self, title, amount, currency, transaction_date, category=None, payment_method=None, notes=None, expense_size=None):

        new_page = {
            "parent": { "database_id": self.DATABASE_ID },
            "properties": {
                "Title": { "title": [{"text": {"content": title}}] },
                "Amount": { "number": amount },
                "Currency": { "rich_text": [{"text": {"content": currency}}] },
                # "Currency": { "select": {"name": currency} },
                "Date": { "date": {"start": transaction_date}},
            }
        }

        # Optional Properties
        if category:
            new_page["properties"]["Category"] = { "select": {"name": category} }
        if notes:
            new_page["properties"]["Notes"] = { "rich_text": [{"text": {"content": notes}}] }
        if expense_size:
            new_page["properties"]["Expense Size"] = {"select": {"name": expense_size}}

        self.client.pages.create(**new_page)

