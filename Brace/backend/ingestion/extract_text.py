import os
import fitz  

def extract_text(pdf_path: str) -> str:
    """Extract text from a PDF using PyMuPDF."""
    text = []

    with fitz.open(pdf_path) as doc:
        for page in doc:
            text.append(page.get_text())

    return "\n".join(text)


def extract_all_papers(folder_path: str):
    papers = []

    for file in sorted(os.listdir(folder_path)):
        if not file.lower().endswith(".pdf"):
            continue

        path = os.path.join(folder_path, file)

        print(f"Reading {file}")

        papers.append({
            "filename": file,
            "text": extract_text(path)
        })

    return papers


if __name__ == "__main__":
    papers = extract_all_papers("../papers/heartbreak")

    print(f"\nLoaded {len(papers)} papers\n")

    if papers:
        print(papers[0]["filename"])
        print()
        print(papers[0]["text"][:2000])