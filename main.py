# -*- coding: utf-8 -*-
import os
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import time

# --- Configuration ---
# Search keywords. You can modify or add more keywords.
# ti: title, abs: abstract, OR means or
SEARCH_QUERY = '(ti:"vector search" OR abs:"vector search" OR ti:"ANNS" OR abs:"ANNS" OR ti:"approximate nearest neighbor" OR abs:"approximate nearest neighbor")'
# Target year
TARGET_YEAR = 2025
# Output directory for saving results
OUTPUT_DIR = "arxiv_vector_search_papers_" + str(TARGET_YEAR)
# arXiv API URL
ARXIV_API_URL = "http://export.arxiv.org/api/query"
# Number of papers to fetch per API request
RESULTS_PER_REQUEST = 100

def search_and_download_papers():
    """
    Search and download papers that match the criteria
    """
    print("Script started...")
    print(f"Search year: {TARGET_YEAR}")
    print(f"Search keywords: {SEARCH_QUERY}")
    print("-" * 30)

    # 1. Create directory for saving PDFs
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Created directory: {OUTPUT_DIR}")

    start_index = 0
    total_downloaded = 0
    
    while True:
        # 2. Build API request parameters
        params = {
            'search_query': SEARCH_QUERY,
            'start': start_index,
            'max_results': RESULTS_PER_REQUEST,
            'sortBy': 'submittedDate',
            'sortOrder': 'descending'
        }

        print(f"\nRequesting {RESULTS_PER_REQUEST} papers starting from index {start_index}...")

        try:
            # 3. Send request to arXiv API
            response = requests.get(ARXIV_API_URL, params=params)
            response.raise_for_status() # Raise exception if request fails

            # 4. Parse returned XML data
            root = ET.fromstring(response.content)
            entries = root.findall('{http://www.w3.org/2005/Atom}entry')

            if not entries:
                print("No more papers found.")
                break

            found_in_year = 0
            for entry in entries:
                # Extract paper publication date
                published_date_str = entry.find('{http://www.w3.org/2005/Atom}published').text
                published_date = datetime.strptime(published_date_str, '%Y-%m-%dT%H:%M:%SZ')

                # 5. Check if paper was published in target year
                if published_date.year == TARGET_YEAR:
                    found_in_year += 1
                    
                    # Extract title, ID and PDF link
                    title = entry.find('{http://www.w3.org/2005/Atom}title').text.strip().replace('\n', ' ')
                    arxiv_id = entry.find('{http://www.w3.org/2005/Atom}id').text.split('/abs/')[-1]
                    pdf_link_element = entry.find('{http://www.w3.org/2005/Atom}link[@title="pdf"]')
                    
                    if pdf_link_element is None:
                        print(f"Warning: Paper '{title}' (ID: {arxiv_id}) has no PDF link, skipping.")
                        continue
                        
                    pdf_url = pdf_link_element.get('href')
                    
                    # Build filename, replace characters that might cause problems
                    sanitized_title = "".join(c for c in title if c.isalnum() or c in (' ', '.', '_')).rstrip()
                    filename = f"{arxiv_id}_{sanitized_title}.pdf"
                    filepath = os.path.join(OUTPUT_DIR, filename)

                    # 6. Download if file doesn't exist
                    if not os.path.exists(filepath):
                        print(f"  -> Preparing to download: '{title}' (ID: {arxiv_id})")
                        try:
                            pdf_response = requests.get(pdf_url)
                            pdf_response.raise_for_status()
                            with open(filepath, 'wb') as f:
                                f.write(pdf_response.content)
                            print(f"     Download successful: {filename}")
                            total_downloaded += 1
                        except requests.exceptions.RequestException as e:
                            print(f"     Download failed: {title}. Error: {e}")
                    else:
                        print(f"  -> File already exists, skipping: '{title}'")

                # If paper publication date is earlier than target year, since results are sorted by date descending, no need to check subsequent papers
                elif published_date.year < TARGET_YEAR:
                    print(f"Found papers from {published_date.year}, stopping search.")
                    # Set a flag to break out of outer loop
                    entries = [] 
                    break

            if not found_in_year and entries:
                 print(f"No papers from {TARGET_YEAR} found in this batch of {len(entries)} papers.")

            # Update start index for next request
            start_index += len(entries)
            
            # Wait between requests to comply with arXiv API usage rules
            time.sleep(3)

        except requests.exceptions.RequestException as e:
            print(f"Error occurred when requesting arXiv API: {e}")
            break
        except ET.ParseError as e:
            print(f"Error occurred when parsing XML data: {e}")
            break

    print("-" * 30)
    print("All tasks completed!")
    print(f"Total downloaded {total_downloaded} new papers.")

if __name__ == '__main__':
    search_and_download_papers()
