# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Update Prompts module (huey/memory/PY)

import csv
import os
import re

INPUT_FILE = os.path.join("prompts", "pygpt_prompts.csv")
OUTPUT_FILE = os.path.join("prompts", "pygpt_prompts.csv")  # overwrite

with open(INPUT_FILE, newline="", encoding="utf-8") as f:
    lines = f.readlines()

# first line is a comment
comment = lines[0].rstrip("\n")
header = lines[1].strip().split(",")
rows = []
for line in lines[2:]:
    line = line.strip()  # remove trailing newline
    if not line:
        continue
    row = next(csv.reader([line]))
    if len(row) < 3:
        continue
    act, prompt, for_devs = row[0], row[1], row[2]
    # remove introductory phrase like "I want you to act as a X." including trailing period
    prompt_clean = re.sub(
        r"^I want you to act as an?[^\.]*\.\s*", "", prompt, flags=re.IGNORECASE
    )
    prompt_clean = re.sub(
        r"^I want you to act as[^\.]*\.\s*", "", prompt_clean, flags=re.IGNORECASE
    )
    prompt_clean = re.sub(
        r"\bI want you to\b", "You should", prompt_clean, flags=re.IGNORECASE
    )
    prefix = "You are "
    prefix += "an " if act and act[0].lower() in "aeiou" else "a "
    prompt_updated = prefix + act + ". " + " ".join(prompt_clean.split())
    rows.append((act, prompt_updated, for_devs))

with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
    f.write(comment + "\n")
    writer = csv.writer(f)
    writer.writerow(header)
    for row in rows:
        writer.writerow(row)
