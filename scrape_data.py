#!/usr/bin/env python3
"""
Standalone scraper script for HHS OIG Enforcement Actions
Run this script to create enforcement_actions_2022_1.csv

Usage: python scrape_data.py
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from datetime import datetime

def scrape_enforcement_actions(month, year):
    """
    Scrape HHS OIG enforcement actions from a given month/year to today.
    """
    
    print(f"Starting to scrape from {month}/{year} to today...")
    print("This will take several minutes...\n")
    
    # Validate year
    if year < 2013:
        print(f"Error: Year must be >= 2013")
        return None
    
    # Initialize
    target_date = datetime(year, month, 1)
    all_actions = []
    base_url = "https://oig.hhs.gov/fraud/enforcement/"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    page_num = 0
    should_continue = True
    
    # Loop through pages
    while should_continue and page_num < 100:
        # Construct URL
        url = base_url if page_num == 0 else f"{base_url}?page={page_num}"
        print(f"Scraping page {page_num + 1}... ", end="")
        
        # Make request
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
        except Exception as e:
            print(f"\nError: {e}")
            break
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        h2_tags = soup.find_all('h2')
        items = [h2.parent for h2 in h2_tags if h2.parent]
        
        if not items:
            print("No items found.")
            break
        
        print(f"Found {len(items)} items")
        
        # Extract data
        items_added = 0
        for item in items:
            # Title and link
            heading = item.find(['h2', 'h3'])
            if not heading:
                continue
                
            link_element = heading.find('a')
            if link_element:
                title = link_element.get_text(strip=True)
                link = link_element.get('href')
                if link and not link.startswith('http'):
                    link = 'https://oig.hhs.gov' + link
            else:
                continue
            
            # Date
            date_element = item.find('time')
            if date_element:
                date_str = date_element.get_text(strip=True)
            else:
                text = item.get_text()
                match = re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}', text)
                date_str = match.group(0) if match else None
            
            # Parse date for comparison
            if date_str:
                try:
                    article_date = datetime.strptime(date_str, "%B %d, %Y")
                except:
                    article_date = datetime.now()
            else:
                article_date = datetime.now()
            
            # Check date range
            if article_date >= target_date:
                # Categories
                categories = []
                for cat in item.find_all('li'):
                    cat_text = cat.get_text(strip=True)
                    if cat_text:
                        categories.append(cat_text)
                category = ', '.join(categories) if categories else None
                
                all_actions.append({
                    'title': title,
                    'date': date_str,
                    'category': category,
                    'link': link
                })
                items_added += 1
            else:
                if items_added == 0:
                    print("  Reached target date. Stopping.")
                    should_continue = False
                break
        
        # Next page
        page_num += 1
        
        # Delay between requests
        if should_continue and page_num < 100:
            time.sleep(1)
    
    # Create DataFrame and save
    if all_actions:
        df = pd.DataFrame(all_actions)
        filename = f"enforcement_actions_{year}_{month}.csv"
        df.to_csv(filename, index=False)
        
        print(f"\n{'='*70}")
        print(f"SUCCESS!")
        print(f"{'='*70}")
        print(f"Total actions collected: {len(df)}")
        print(f"Saved to: {filename}")
        print(f"\nDate range:")
        print(f"  Earliest: {df['date'].iloc[-1]}")
        print(f"  Latest: {df['date'].iloc[0]}")
        print(f"{'='*70}")
        
        return df
    else:
        print("\nNo data collected.")
        return None

if __name__ == "__main__":
    print("="*70)
    print("HHS OIG Enforcement Actions Scraper")
    print("="*70)
    print()
    
    # Scrape from January 2022 to today
    df = scrape_enforcement_actions(month=1, year=2022)
    
    if df is not None:
        print("\nScraping complete! You can now render your Quarto document.")
    else:
        print("\nScraping failed. Check error messages above.")
