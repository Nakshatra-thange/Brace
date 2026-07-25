from extract_text import extract_all_papers
from split_sections import split_sections

papers = extract_all_papers("../papers/heartbreak")

sections = split_sections(papers[0]["text"])

print("\nSections found:\n")

for key in sections:
    print(key)