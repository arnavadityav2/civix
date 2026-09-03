"""
CIVIX 2.0 — Golden Evidence Package Generator
Round 2A

Generates synthetic evidence files for the Round 2A E2E test.
All entities in these files are fictional.

Files produced:
  civix_golden_evidence/
    FIR_001.pdf              — Text-extractable FIR with 3 persons, 1 vehicle, 1 org, 2 locations
    FORENSIC_REPORT_001.pdf  — Second document with overlapping persons
    INTELLIGENCE_001.txt     — Plain text intelligence report

Usage:
  python scratch/create_golden_evidence.py
"""
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

OUTPUT_DIR = Path(__file__).parent.parent / "civix_golden_evidence"


def make_paragraph(text, style):
    return Paragraph(text, style)


def create_fir_001():
    """
    Synthetic FIR Report with multiple extractable entities.

    Entities embedded:
      PERSON:   Rajesh Kumar Verma (suspect), Ananya Singh (witness), Suresh Babu Yadav (victim)
      VEHICLE:  RJ14-CB-2847 (Maruti Swift, white)
      ORG:      Verma Traders Private Limited
      LOCATION: Godown No. 7, Sanganer Industrial Area, Jaipur
      LOCATION: 45-B, Gandhi Nagar, Jaipur

    Relationships:
      Rajesh Kumar Verma OWNS RJ14-CB-2847
      Rajesh Kumar Verma EMPLOYED_BY Verma Traders Private Limited
      Rajesh Kumar Verma SEEN_AT Godown No. 7, Sanganer Industrial Area, Jaipur
      Suresh Babu Yadav RESIDED_AT 45-B, Gandhi Nagar, Jaipur

    Temporal facts:
      Rajesh Kumar Verma seen at godown on 15 June 2026 at 23:45 hours
    """
    path = OUTPUT_DIR / "FIR_001.pdf"
    doc = SimpleDocTemplate(str(path), pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2.5*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    heading = styles["Heading1"]
    heading2 = styles["Heading2"]

    story = []

    # Header
    story.append(Paragraph("RAJASTHAN POLICE — FIRST INFORMATION REPORT", heading))
    story.append(Paragraph("FIR No: JAIPUR/SANGANER/2026/00447", normal))
    story.append(Paragraph("Date: 16 June 2026 | Time: 02:30 hrs", normal))
    story.append(Paragraph("Police Station: Sanganer, District: Jaipur, Rajasthan", normal))
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("1. COMPLAINANT DETAILS", heading2))
    story.append(Paragraph(
        "Complainant: Ananya Singh, Age: 34 years, Occupation: Shopkeeper, "
        "Address: Shop No. 12, Sanganer Market, Jaipur. "
        "Contact: 9414XXXXXX",
        normal
    ))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("2. ACCUSED / SUSPECT", heading2))
    story.append(Paragraph(
        "Name: Rajesh Kumar Verma, Age: 42 years, Gender: Male, "
        "Occupation: Businessman, Date of Birth: 12 March 1984, "
        "Nationality: Indian (IND). "
        "Permanent Address: H.No. 78, Pratap Nagar, Jaipur, Rajasthan. "
        "Known Associates: Suresh Babu Yadav.",
        normal
    ))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("3. VICTIM / AFFECTED PARTY", heading2))
    story.append(Paragraph(
        "Victim: Suresh Babu Yadav, Age: 29 years, Gender: Male. "
        "Permanent Residence: 45-B, Gandhi Nagar, Jaipur, Rajasthan. "
        "Occupation: Driver.",
        normal
    ))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("4. INCIDENT DESCRIPTION", heading2))
    story.append(Paragraph(
        "On 15 June 2026 at approximately 23:45 hours, the witness Ananya Singh "
        "observed a white Maruti Swift bearing registration number RJ14-CB-2847 "
        "parked outside Godown No. 7, Sanganer Industrial Area, Jaipur. "
        "The vehicle is registered to Rajesh Kumar Verma. "
        "Rajesh Kumar Verma was seen entering the godown premises. "
        "Goods of suspicious nature were being loaded into the vehicle.",
        normal
    ))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("5. COMPANY AFFILIATION", heading2))
    story.append(Paragraph(
        "Rajesh Kumar Verma is the proprietor of Verma Traders Private Limited, "
        "a registered company with CIN: U52190RJ2015PTC047921, "
        "operating from Godown No. 7, Sanganer Industrial Area, Jaipur. "
        "The company is primarily engaged in trading of industrial chemicals.",
        normal
    ))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("6. IPC SECTIONS INVOKED", heading2))
    story.append(Paragraph(
        "Sections 420 (Cheating), 467 (Forgery), 471 (Using forged documents) "
        "of the Indian Penal Code, 1860.",
        normal
    ))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("7. INVESTIGATING OFFICER", heading2))
    story.append(Paragraph("SI Ramesh Chand Sharma, Badge No. RPL-44821, PS Sanganer.", normal))
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph(
        "This FIR has been registered based on the oral complaint of Ananya Singh "
        "and is being investigated under the supervision of the Station House Officer.",
        normal
    ))

    doc.build(story)
    print(f"Created: {path}")
    return path


def create_forensic_report_001():
    """
    Synthetic Forensic Report — overlapping persons with FIR_001.
    Tests cross-document entity co-reference.

    Additional entities:
      PERSON:   Mohit Vyas (forensic expert)
      LOCATION: FSL Jaipur, Sector 11, Pratap Nagar, Jaipur

    Overlapping entities from FIR_001:
      PERSON:   Rajesh Kumar Verma (mentioned as suspect in forensic analysis)
      VEHICLE:  RJ14-CB-2847 (forensic samples taken from vehicle)
    """
    path = OUTPUT_DIR / "FORENSIC_REPORT_001.pdf"
    doc = SimpleDocTemplate(str(path), pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2.5*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    heading = styles["Heading1"]
    heading2 = styles["Heading2"]

    story = []

    story.append(Paragraph("RAJASTHAN FORENSIC SCIENCE LABORATORY — EXAMINATION REPORT", heading))
    story.append(Paragraph("Report No: FSL/JAI/2026/3891", normal))
    story.append(Paragraph("Date of Examination: 20 June 2026", normal))
    story.append(Paragraph("Location: FSL Jaipur, Sector 11, Pratap Nagar, Jaipur", normal))
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("1. CASE REFERENCE", heading2))
    story.append(Paragraph(
        "This forensic examination is conducted in connection with FIR No. "
        "JAIPUR/SANGANER/2026/00447. Suspect: Rajesh Kumar Verma.",
        normal
    ))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("2. EXAMINING OFFICER", heading2))
    story.append(Paragraph(
        "Forensic Expert: Mohit Vyas, Designation: Senior Scientific Officer, "
        "Specialisation: Chemical Analysis, "
        "Laboratory: Rajasthan FSL, Sector 11, Pratap Nagar, Jaipur.",
        normal
    ))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("3. MATERIAL EXAMINED", heading2))
    story.append(Paragraph(
        "3.1 Swabs collected from the interior of vehicle registration number RJ14-CB-2847 "
        "(a white Maruti Swift belonging to Rajesh Kumar Verma). "
        "3.2 Powder samples recovered from Godown No. 7, Sanganer Industrial Area, Jaipur.",
        normal
    ))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("4. FINDINGS", heading2))
    story.append(Paragraph(
        "Chemical analysis of the powder samples revealed the presence of restricted substances "
        "consistent with industrial solvent precursors. "
        "Traces of the same chemical compounds were detected in the vehicle swabs. "
        "This indicates a high probability that the vehicle was used to transport the material "
        "from the godown premises.",
        normal
    ))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("5. CONCLUSION", heading2))
    story.append(Paragraph(
        "Based on the forensic evidence, the material recovered from Godown No. 7 and "
        "the vehicle RJ14-CB-2847 are chemically linked. "
        "Report prepared by Mohit Vyas, Senior Scientific Officer, FSL Jaipur.",
        normal
    ))

    doc.build(story)
    print(f"Created: {path}")
    return path


def create_intelligence_001():
    """
    Plain text intelligence report — simple text extraction test.
    """
    path = OUTPUT_DIR / "INTELLIGENCE_001.txt"
    content = """CIVIX INTELLIGENCE NOTE — UNCLASSIFIED
Report ID: INTL/JAI/2026/0088
Date: 22 June 2026

SUBJECT: Activities of Rajesh Kumar Verma

Source intelligence indicates that Rajesh Kumar Verma, a known businessman
operating through Verma Traders Private Limited, has been observed making
repeated visits to the Sanganer Industrial Area in Jaipur after midnight.

A white Maruti Swift vehicle (registration RJ14-CB-2847) was observed parked
at multiple locations in the area between 22:00 and 02:00 hours.

Suresh Babu Yadav, residing at 45-B Gandhi Nagar, Jaipur, is believed to be
a known associate of Rajesh Kumar Verma. Yadav frequently visited the godown
premises during the same period.

The organization Verma Traders Private Limited appears to be a front for
illicit transport activities. Its godown at Sanganer Industrial Area, Jaipur
has been identified as a point of interest.

This note is for investigative purposes only and does not constitute evidence.
"""
    path.write_text(content, encoding="utf-8")
    print(f"Created: {path}")
    return path


if __name__ == "__main__":
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Creating Golden Evidence Package in: {OUTPUT_DIR}")
    print()
    create_fir_001()
    create_forensic_report_001()
    create_intelligence_001()
    print()
    print("Golden Evidence Package created successfully.")
    print("Expected entities in FIR_001.pdf:")
    print("  PERSON: Rajesh Kumar Verma, Ananya Singh, Suresh Babu Yadav")
    print("  VEHICLE: RJ14-CB-2847")
    print("  ORG: Verma Traders Private Limited")
    print("  LOCATION: Godown No. 7 Sanganer, 45-B Gandhi Nagar")
    print("  RELATIONSHIPS: OWNS, EMPLOYED_BY, SEEN_AT, RESIDED_AT")
    print("  TEMPORAL: 15 June 2026 23:45 hrs event")
