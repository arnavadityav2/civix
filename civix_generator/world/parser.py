import re
import json

def parse_markdown_table(text, heading=None):
    """
    Finds a heading in the text, then parses the first markdown table it finds
    immediately after that heading. Returns a list of dictionaries.
    """
    if heading:
        heading_pattern = re.compile(re.escape(heading) + r'.*?(?=\n## |\Z)', re.DOTALL | re.IGNORECASE)
        match = heading_pattern.search(text)
        if not match:
            return []
        section_text = match.group(0)
    else:
        section_text = text
        
    lines = section_text.strip().split('\n')
    table_lines = []
    in_table = False
    
    # We might have multiple tables in a section if heading is generic, 
    # but this function only extracts the FIRST table it finds.
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('|'):
            in_table = True
            table_lines.append(stripped)
        elif in_table and stripped == '':
            # Ignore blank lines inside table
            continue
        elif in_table:
            break
            
    if not table_lines or len(table_lines) < 3:
        return []
        
    headers = [col.strip() for col in table_lines[0].split('|')[1:-1]]
    
    results = []
    for row in table_lines[2:]:
        cols = [col.strip() for col in row.split('|')[1:-1]]
        row_dict = dict(zip(headers, cols))
        results.append(row_dict)
        
    return results

def parse_persons(text):
    """
    Finds all #### P-XX headings and parses the table immediately following it.
    Returns a dictionary of PID -> Person Data.
    """
    results = []
    
    # Find all #### P-XX blocks
    pattern = re.compile(r'#### (P-\d{2}.*?)(?=\n#### P-|\n## |\Z)', re.DOTALL)
    matches = pattern.findall(text)
    
    for match in matches:
        lines = match.strip().split('\n')
        header_line = lines[0]
        # Example: P-01: Vikram Malhotra  Primary Suspect
        parts = header_line.split(':', 1)
        pid = parts[0].strip()
        name_part = re.split(r'[-—]', parts[1])[0].strip() if len(parts) > 1 else ""
        
        # Skip bulk headings
        if '–' in pid or '-' in pid[2:]:
            continue
            
        # Now find the table in the match block
        table_data = parse_markdown_table(match)
        # The table is a key-value vertical table for persons: Field | Value
        person_dict = {"ID": pid, "Name": name_part}
        for row in table_data:
            field = row.get("Field", "").replace("**", "").strip()
            value = row.get("Value", "").strip()
            if field:
                person_dict[field] = value
                
        results.append(person_dict)
        
    return results
    

def extract_json_block(text, heading):
    heading_pattern = re.compile(re.escape(heading) + r'.*?(?=\n## |\Z)', re.DOTALL | re.IGNORECASE)
    match = heading_pattern.search(text)
    if not match:
        return None
        
    section_text = match.group(0)
    json_match = re.search(r'```json\n(.*?)\n```', section_text, re.DOTALL)
    
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except:
            return None
    return None

def extract_yaml_block(text, heading):
    heading_pattern = re.compile(re.escape(heading) + r'.*?(?=\n## |\Z)', re.DOTALL | re.IGNORECASE)
    match = heading_pattern.search(text)
    if not match:
        return None
        
    section_text = match.group(0)
    yaml_match = re.search(r'```yaml\n(.*?)\n```', section_text, re.DOTALL)
    
    if yaml_match:
        lines = yaml_match.group(1).split('\n')
        result = {}
        for line in lines:
            if ':' in line:
                parts = line.split(':', 1)
                key = parts[0].strip()
                val = parts[1].strip()
                if key != 'generator' and key != 'date_range':
                    result[key] = val
        return result
    return None
