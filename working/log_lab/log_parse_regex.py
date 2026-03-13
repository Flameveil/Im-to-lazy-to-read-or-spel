import re

log_line = "[2026-02-10 19:18:21] ERROR - CRITICAL_MISALIGNMENT: Part_ID 8829-X at +2.10mm offset."
pattern = r"^\[(?P<date>\d{4}-\d{2}-\d{2})\s(?P<time>\d{2}:\d{2}:\d{2})\]\s(?P<level>[A-Z]+)\s+-\s+(?P<text>.*)$"

m = re.match(pattern, log_line)
if m:
    # Converting to a structured list or dict
    fields = m.groups()
    print(f"Fields extracted: {fields}")


    log_dict = m.groupdict() # creates a dictionary based on the field names
    print(f"Dictionary extracted: {log_dict}") 
else:
    print("No match found.")    