import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import json

OUTPUT_DIR = "scratch/test_docs_c0"
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

# 1. FIR
fir_text = [
    "FIRST INFORMATION REPORT (FIR)",
    "Jurisdiction: Sector 18, Noida Police",
    "Date of Report: 2026-09-01 10:15 IST",
    "",
    "1. COMPLAINANT/INFORMANT",
    "Name: Inspector Rajeev Kumar (Badge #4412)",
    "",
    "2. INCIDENT CHRONOLOGY",
    "On 2026-08-31 at 22:45, a routine patrol encountered suspicious activity",
    "near the service lane of DLF Mall of India. Two unknown individuals were",
    "observed transferring heavy cardboard boxes between two vehicles.",
    "",
    "3. VEHICLE/DEVICE IDENTIFIERS",
    "Vehicle 1: White Maruti Dzire, Registration: HR-26-XX-1122",
    "Vehicle 2: Black Toyota Fortuner, Registration partially obscured, reading 'DL-9C-AA-'",
    "",
    "4. OFFICER ACTIONS & SEIZURE",
    "Upon approach, individuals fled the scene in the Fortuner.",
    "The Dzire was left abandoned with engine running.",
    "Seized from Dzire trunk: Three cardboard boxes containing Rs. 50,00,000 in cash",
    "and a ledger book. Recovered one mobile handset (Device IMEI: 865443049999111) from",
    "the passenger seat.",
    "",
    "5. SUSPECT DETAILS",
    "Suspects unidentified. Vehicle registry check pending.",
    "",
    "6. SECTIONS/OFFENCES",
    "Section 420, 120B IPC. PMLA violations suspected."
]
create_pdf("FIR_003_Noida.pdf", "DELHI NCR POLICE - FIR NO. 003/2026", fir_text)

# 2. Forensic Report
forensic_text = [
    "FORENSIC SCIENCE LABORATORY - DIGITAL & TRACE DIVISION",
    "Case Ref: FIR 003/2026",
    "Date of Examination: 2026-09-02",
    "",
    "1. EXHIBITS RECEIVED",
    "Exhibit A: Mobile handset, IMEI 865443049999111",
    "Exhibit B: Handwritten ledger",
    "Seal Condition: Intact, received from Ins. R. Kumar.",
    "",
    "2. EXAMINATION METHOD (DIGITAL)",
    "Physical dump of Exhibit A via Cellebrite UFED.",
    "",
    "3. OBSERVATIONS & RESULTS",
    "Exhibit A (Handset):",
    "- SIM IMSI detected: 404450123456789",
    "- Phone number MSISDN: +91-9898989898",
    "- Last call recorded: 2026-08-31 22:30 to +91-7777777777 (Duration: 45s)",
    "- SMS Outbox at 22:35: 'Drop point compromised, fallback to Apex shell.'",
    "",
    "Exhibit B (Ledger):",
    "- Latent prints developed on page 4.",
    "- Print match: AFIS ID #99211 (Subject: Vikram Singh).",
    "- Text extraction: 'GEPL Remittance: 50L. Route via Apex.'",
    "",
    "4. LIMITATIONS & EXPERT CONCLUSION",
    "The presence of Vikram Singh's fingerprints is consistent with handling",
    "the ledger, but does not prove ownership of the cash or vehicle.",
    "The handset subscriber identity remains unverified (prepaid SIM)."
]
create_pdf("FORENSIC_011_Trace.pdf", "FSL EXAMINATION REPORT", forensic_text)

# 3. Intelligence Memo
intel_text = [
    "INTELLIGENCE MEMORANDUM",
    "Source: Confidential Informant (CI-102)",
    "Date: 2026-09-03",
    "",
    "1. OBSERVATION",
    "CI-102 reports that an individual known as 'Vicky' operates a hawala",
    "network in the Delhi NCR region.",
    "Vicky was reportedly seen driving a Black Toyota Fortuner (DL-9C-AA-9988)",
    "frequently visiting an office in Okhla Phase 1.",
    "",
    "2. SOURCE TYPE & CONFIDENCE",
    "Human Intelligence (HUMINT). Source reliability: B (Usually reliable).",
    "Information validity: 3 (Possibly true).",
    "",
    "3. ANALYTICAL ASSESSMENT",
    "Based on prior records, 'Vicky' is a known alias for Vikram Singh.",
    "The Okhla Phase 1 address matches the registered corporate office of",
    "Global Exports Pvt Ltd (GEPL).",
    "",
    "4. ALTERNATIVE EXPLANATIONS",
    "Vicky could be a generic moniker, and the Fortuner is a common vehicle type.",
    "The association with GEPL requires corroboration via financial or",
    "communication records before escalating to a formal target profile."
]
create_pdf("INTEL_009_NCR.pdf", "CONFIDENTIAL INTELLIGENCE MEMO", intel_text)

# 4. Financial Report
financial_text = [
    "SUSPICIOUS ACTIVITY REPORT (SAR) - FINANCIAL INTELLIGENCE UNIT",
    "Date: 2026-09-04",
    "",
    "1. TRANSACTION DETAILS",
    "Txn ID: TXN-884422",
    "Date/Time: 2026-08-30 14:00 IST",
    "Amount: Rs. 50,00,000",
    "Transaction Type: RTGS Transfer",
    "",
    "2. ACCOUNT IDENTIFIERS",
    "Sender Account: 009911223344 (Global Exports Pvt Ltd)",
    "Recipient Account: 556677889900 (Apex Shell Consultants)",
    "",
    "3. SUSPICIOUS INDICATORS",
    "Rapid movement of funds. Apex Shell Consultants was incorporated only",
    "3 weeks prior. The registered director for Apex Shell Consultants is listed",
    "as Neha Gupta. No prior business history between these entities.",
    "",
    "4. SOURCE REFERENCE",
    "Banking node #44, automated alert threshold triggered.",
    "",
    "5. ANALYTICAL CONCLUSION",
    "The transaction exhibits layering characteristics typical of trade-based",
    "money laundering. Strongly recommend verifying the physical addresses",
    "of both sender and recipient entities."
]
create_pdf("FINANCIAL_SAR_044.pdf", "FIU-IND SUSPICIOUS ACTIVITY REPORT", financial_text)

# 5. Interview
interview_text = [
    "WITNESS INTERVIEW TRANSCRIPT",
    "Date: 2026-09-05",
    "Subject: Neha Gupta",
    "Interviewer: Ins. R. Kumar",
    "",
    "Q: Ms. Gupta, can you state your relationship with Apex Shell Consultants?",
    "A: I am a director on paper. It's a consulting firm.",
    "Q: And what consulting do you do for Global Exports Pvt Ltd?",
    "A: [Hesitation] We provide market research.",
    "Q: Are you familiar with a man named Vikram Singh, or 'Vicky'?",
    "A: I don't know anyone named Vikram. I might know a Vicky, he used to be a driver.",
    "Q: Why did +91-9898989898 call your number (+91-7777777777) on Aug 31 at 22:30?",
    "A: I lose my phone all the time. Anyone could have called it.",
    "Q: Where were you on the night of August 31st?",
    "A: I was at home.",
    "Q: We have RTGS records showing 50 Lakhs moving to your firm on Aug 30.",
    "A: That was an advance payment for services. Talk to my CA.",
    "[End of Transcript Excerpt]"
]
create_pdf("INTERVIEW_001_Gupta.pdf", "WITNESS INTERVIEW TRANSCRIPT", interview_text)

print("Generated C0 synthetic test documents in scratch/test_docs_c0/")
