# -*- coding: utf-8 -*-https://github.com/Kwan-Yiu/mr.arixv
import os
from datetime import datetime

PAPER_DIR = "papers"
README_FILE = "README.md"

def generate_readme_content():
    """Generates the content for the README.md file."""
    
    # Header of the README file
    header = "# VDB & ANNS Papers\n\n"
    header += "A curated list of papers related to vector search and ANNS, automatically updated.\n\n"
    header += "Last updated: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n\n"
    header += "---\n\n"
    
    papers = []
    if not os.path.exists(PAPER_DIR):
        print(f"Warning: Directory '{PAPER_DIR}' not found.")
        return header + "No papers found yet. The 'paper' directory is missing."

    # List all files, filter for PDFs, and sort them with the newest first
    try:
        filenames = sorted([f for f in os.listdir(PAPER_DIR) if f.endswith('.pdf')], reverse=True)
    except FileNotFoundError:
        return header + "No papers found yet."

    for filename in filenames:
        try:
            # Parse filename: YYYYMMDD_Title.pdf
            parts = filename.split('_', 1)
            date_str = parts[0]
            title_with_ext = parts[1]
            
            # Format date for better readability
            date_obj = datetime.strptime(date_str, '%Y%m%d')
            formatted_date = date_obj.strftime('%Y-%m-%d')
            
            # Clean up the title by removing the .pdf extension
            title = os.path.splitext(title_with_ext)[0]
            
            # Create the markdown list item
            papers.append(f"- **{formatted_date}**: {title}")
        except (IndexError, ValueError):
            print(f"Skipping malformed filename: {filename}")
            continue

    if not papers:
        return header + "No papers found in the 'paper' directory."

    return header + "\n".join(papers)

def main():
    """Main function to update the README.md file."""
    print("Starting README update...")
    content = generate_readme_content()
    with open(README_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Successfully updated {README_FILE}.")

if __name__ == '__main__':
    main()
