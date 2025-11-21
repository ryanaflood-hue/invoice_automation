import os
from docx import Document

GENERATED_DIR = r"C:\Development\invoice_automation\generated_invoices"

def check_fonts():
    files = [f for f in os.listdir(GENERATED_DIR) if f.endswith('.docx')]
    files.sort(key=lambda x: os.path.getmtime(os.path.join(GENERATED_DIR, x)), reverse=True)
    
    if not files:
        print("No invoices found.")
        return

    latest_file = files[0]
    path = os.path.join(GENERATED_DIR, latest_file)
    print(f"Checking fonts in {latest_file}...")
    
    doc = Document(path)
    
    # We expect some runs to be Calibri 14
    calibri_14_found = False
    
    for p in doc.paragraphs:
        for run in p.runs:
            if run.font.name == 'Calibri' and run.font.size and run.font.size.pt == 14.0:
                calibri_14_found = True
                # print(f"Found Calibri 14 run: '{run.text}'")
    
    if calibri_14_found:
        print("SUCCESS: Found text with Calibri 14pt font.")
    else:
        print("WARNING: Did not find any text explicitly set to Calibri 14pt.")

if __name__ == "__main__":
    check_fonts()
