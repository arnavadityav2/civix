import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

OUTPUT_DIR = "scratch/test_docs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def create_pdf(filename, title, lines):
    c = canvas.Canvas(os.path.join(OUTPUT_DIR, filename), pagesize=letter)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, 750, title)
    
    c.setFont("Helvetica", 11)
    y = 710
    for line in lines:
        if line.strip() == "":
            y -= 15
            continue
        c.drawString(50, y, line)
        y -= 15
        if y < 50:
            c.showPage()
            c.setFont("Helvetica", 11)
            y = 750
            
    c.save()

# 1. FIR (Police Report)
fir_text = [
    "FIRST INFORMATION REPORT (FIR)",
    "Police Station: Sector 18, Noida",
    "Date: 2026-09-01",
    "",
    "Complainant: Mr. Amit Sharma",
    "Incident Location: Near DLF Mall of India, Noida",
    "",
    "Details of Incident:",
    "At approximately 22:30 on 2026-08-31, I witnessed a suspicious transaction.",
    "A person later identified as Vikram Singh (alias 'Vicky') was seen exchanging",
    "a heavy duffel bag with an unidentified individual near a black Honda City",
    "bearing license plate DL-9C-AV-4411.",
    "",
    "Vikram Singh is reportedly an associate of Global Exports Pvt Ltd.",
    "The vehicle immediately sped towards the DND flyway."
]
create_pdf("FIR_002_Noida.pdf", "DELHI NCR POLICE - FIR NO. 002/2026", fir_text)

# 2. Intelligence Memo
intel_text = [
    "CONFIDENTIAL INTELLIGENCE MEMO",
    "Source: Field Operative K-9",
    "Location: Gurugram Cyber Hub",
    "Date: 2026-09-02",
    "",
    "Subject: Suspected Financial Irregularities",
    "",
    "Observations:",
    "Target 1, Vikram Singh (Vicky), was observed meeting with Ms. Neha Gupta",
    "at 14:00 hours outside a coffee shop in Cyber Hub, Gurugram.",
    "Ms. Neha Gupta is believed to be the Director of Global Exports Pvt Ltd.",
    "",
    "The conversation appeared tense. Target 1 was heard demanding 'payment for",
    "the Noida drop'. Ms. Gupta was seen handing over a brown envelope.",
    "",
    "It is uncertain whether this is related to the recent narcotics tip-off.",
    "Target 1 later departed in an Ola Cab (White Maruti Dzire, HR-26-XX-1122)."
]
create_pdf("INTEL_004_Gurugram.pdf", "INTEL MEMORANDUM - NCR BRANCH", intel_text)

# 3. Forensic Report
forensic_text = [
    "FORENSIC EVIDENCE ANALYSIS REPORT",
    "Lab: Delhi Central Forensics",
    "Case Ref: FIR 002/2026",
    "",
    "Items Analyzed:",
    "Item 1: Brown Envelope recovered from Vikram Singh's residence during raid.",
    "Item 2: Black Honda City (DL-9C-AV-4411).",
    "",
    "Findings:",
    "The envelope contained Rs. 5,00,000 in cash and a ledger.",
    "The ledger explicitly mentions 'Global Exports Pvt Ltd' and 'Noida Delivery'.",
    "Fingerprints belonging to Neha Gupta were found on the inner flap of the envelope.",
    "",
    "The vehicle (Item 2) is registered to a shell company named 'Vicky Enterprises'.",
    "GPS logs extracted from the vehicle confirm it was at DLF Mall of India, Noida",
    "on 2026-08-31 at 22:30."
]
create_pdf("FORENSIC_008_Delhi.pdf", "FORENSIC ANALYSIS REPORT", forensic_text)

# 4. TXT Intercept
txt_content = """INTERCEPT LOG
Type: SMS
From: +91-9898989898 (Vikram Singh)
To: +91-7777777777 (Neha Gupta)
Time: 2026-08-31 23:05

Message: "Drop complete. The Honda is clean. Need the remaining cash tomorrow at Cyber Hub."
"""
with open(os.path.join(OUTPUT_DIR, "INTERCEPT_012_Delhi.txt"), "w", encoding="utf-8") as f:
    f.write(txt_content)

print("Generated synthetic test documents in scratch/test_docs/")
