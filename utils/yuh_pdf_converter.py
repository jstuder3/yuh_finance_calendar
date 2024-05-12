import pdfplumber
import re

class YuhPdfConverter:
    def __init__(self, pdf_path_list):
        self.pdf_path_list = pdf_path_list

    def get_all_transactions(self):
        all_transactions = []
        for pdf_path in self.pdf_path_list:
            currency = None
            prev_saldo = None
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text_simple()
                    currency_cache = try_find_currency(page_text)
                    if currency_cache is not None:
                        currency = currency_cache

                    all_lines = page_text.split("\n")
                    for i, elem in enumerate(all_lines):
                        if starts_with_date(elem):
                            # extract necessary information
                            elem = re.split(r" (\d{9}) ", elem)
                            info = elem[0][11:]
                            #date = elem[0][:10] # use valuta date and not booking date
                            last_part = elem[-1].split(" ")
                            amount = float(last_part[0].replace("’", ""))
                            date = last_part[1]
                            date = date[-4:] + "-" + date[3:5] + "-" + date[:2]
                            saldo = float(last_part[2].replace("’", ""))

                            if prev_saldo is None or saldo < prev_saldo:
                                amount = -amount
                            prev_saldo = saldo
                            
                            elem = {"date": date, "info": info, "amount": amount, "currency": currency, "saldo": saldo}

                            # check the next lines for more information
                            for j in range(1, 3):
                                if i+j < len(all_lines):
                                    if not starts_with_date(all_lines[i+j]):
                                        elem["info"] += " " + all_lines[i+j]
                                    else:
                                        break
                            elem["info"] = re.sub(r"\(cid:\d{3}\)", "#", elem["info"], flags=re.DOTALL).strip()

                            if elem["info"] != "Transfer" and not elem["info"].startswith("Transfer Total") and not elem["info"].startswith("Transfer Die"):
                                all_transactions.append(elem)
        return all_transactions
    
def starts_with_date(text):
    """Checks if a string starts with a date in the format dd.mm.yyyy."""
    return bool(re.match(r"\d{2}\.\d{2}\.\d{4}", text))

def try_find_currency(text):
    cache = re.search(r"KONTOAUSZUG in(\w{3})", text)
    if cache is None:
        return None
    return cache.group(1)

if __name__ == "__main__":
    pdf_path_list = ["pdfs/yuh_apr_2024.pdf"]
    converter = YuhPdfConverter(pdf_path_list)
    transactions = converter.get_all_transactions()
    print(transactions)