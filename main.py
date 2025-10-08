# -*- coding: utf-8 -*-
import os
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, date, timedelta
import time
import re

# --- Configuration ---
# Basic search query. You can modify or add more keywords.
# ti: title, abs: abstract, OR: logical OR
BASE_SEARCH_QUERY = '(ti:"vector search" OR abs:"vector search" OR ti:"ANNS" OR abs:"ANNS" OR ti:"approximate nearest neighbor" OR abs:"approximate nearest neighbor")'
# Search start date
START_DATE = date(2025, 1, 1)
# Directory to save the results
OUTPUT_DIR = "papers"
# Log file to record completed dates
COMPLETED_DATES_LOG = "completed_dates.txt"
# arXiv API URL
ARXIV_API_URL = "http://export.arxiv.org/api/query"
# Number of results per API request
RESULTS_PER_REQUEST = 100

def load_completed_dates():
    """Loads completed dates from the log file."""
    if not os.path.exists(COMPLETED_DATES_LOG):
        return set()
    with open(COMPLETED_DATES_LOG, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f)

def mark_date_as_completed(day_str):
    """Marks a date as completed and writes it to the log file."""
    with open(COMPLETED_DATES_LOG, 'a', encoding='utf-8') as f:
        f.write(day_str + '\n')

def sanitize_filename(title):
    """Cleans the title to be used as a safe filename."""
    # 1. Remove characters from the title that are not suitable for a filename
    sanitized = re.sub(r'[\\/*?:"<>|]', "", title)
    # 2. Replace multiple spaces with a single space
    sanitized = " ".join(sanitized.split())
    # 3. Truncate long filenames to avoid errors (keep 150 characters)
    max_len = 150
    if len(sanitized) > max_len:
        # Avoid cutting words in the middle
        sanitized = sanitized[:max_len].rsplit(' ', 1)[0] 
    return sanitized.strip()

def search_and_download_for_day(current_date):
    """Searches and downloads papers for a specific date."""
    date_str_compact = current_date.strftime('%Y%m%d')
    # arXiv API requires the date range format to be YYYYMMDDHHMMSS
    start_of_day = f"{date_str_compact}000000"
    end_of_day = f"{date_str_compact}235959"
    
    # Construct the final search query including the date range
    date_query = f'submittedDate:[{start_of_day} TO {end_of_day}]'
    full_query = f'({BASE_SEARCH_QUERY}) AND {date_query}'
    
    print(f"Search query: {full_query}")

    start_index = 0
    total_downloaded_today = 0
    
    while True:
        params = {
            'search_query': full_query,
            'start': start_index,
            'max_results': RESULTS_PER_REQUEST,
            'sortBy': 'submittedDate',
            'sortOrder': 'ascending'
        }

        print(f"  Requesting from index {start_index}...")

        try:
            response = requests.get(ARXIV_API_URL, params=params)
            response.raise_for_status()

            root = ET.fromstring(response.content)
            entries = root.findall('{http://www.w3.org/2005/Atom}entry')

            if not entries:
                print("  No more papers for this date or page.")
                break

            for entry in entries:
                title = entry.find('{http://www.w3.org/2005/Atom}title').text.strip().replace('\n', ' ')
                arxiv_id = entry.find('{http://www.w3.org/2005/Atom}id').text.split('/abs/')[-1]
                pdf_link_element = entry.find('{http://www.w3.org/2005/Atom}link[@title="pdf"]')
                
                if pdf_link_element is None:
                    print(f"    Warning: PDF link not found for paper '{title}' (ID: {arxiv_id}). Skipping.")
                    continue
                    
                pdf_url = pdf_link_element.get('href')
                
                # Build the filename using the correct date prefix and the sanitized title
                sanitized_title = sanitize_filename(title)
                filename = f"{current_date.strftime('%Y%m%d')}_{sanitized_title}.pdf"
                filepath = os.path.join(OUTPUT_DIR, filename)

                if not os.path.exists(filepath):
                    print(f"    -> Preparing to download: '{title}'")
                    try:
                        pdf_response = requests.get(pdf_url)
                        pdf_response.raise_for_status()
                        with open(filepath, 'wb') as f:
                            f.write(pdf_response.content)
                        print(f"       Successfully downloaded: {filename}")
                        total_downloaded_today += 1
                    except requests.exceptions.RequestException as e:
                        print(f"       Download failed for: {title}. Error: {e}")
                else:
                    print(f"    -> File already exists, skipping: '{title}'")
            
            # If the number of results returned is less than requested, it's the last page
            if len(entries) < RESULTS_PER_REQUEST:
                break
            
            start_index += len(entries)
            time.sleep(3) # Adhere to API usage rules

        except requests.exceptions.RequestException as e:
            print(f"  An error occurred while requesting the arXiv API: {e}")
            break
        except ET.ParseError as e:
            print(f"  An error occurred while parsing XML data: {e}")
            break
            
    return total_downloaded_today

def main():
    """Main function to loop through days and execute download tasks."""
    print("Script started...")
    print(f"Base search query: {BASE_SEARCH_QUERY}")
    print("-" * 30)

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Created directory: {OUTPUT_DIR}")

    completed_dates = load_completed_dates()
    print(f"Loaded {len(completed_dates)} completed dates.")

    current_date = START_DATE
    end_date = date.today()
    total_downloaded_all_time = 0

    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        
        if date_str in completed_dates:
            print(f"\nDate {date_str} has already been processed. Skipping.")
            current_date += timedelta(days=1)
            continue
            
        print(f"\n===== Processing date: {date_str} =====")
        
        downloaded_today = search_and_download_for_day(current_date)
        
        mark_date_as_completed(date_str)
        print(f"===== Finished processing date {date_str}. Newly downloaded {downloaded_today} papers today. =====")
        
        total_downloaded_all_time += downloaded_today
        current_date += timedelta(days=1)
        time.sleep(3) # Pause briefly after processing a day

    print("-" * 30)
    print("All tasks completed!")
    print(f"A total of {total_downloaded_all_time} new papers were downloaded in this run.")

if __name__ == '__main__':
    main()

