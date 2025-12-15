import undetected_chromedriver as uc
import time
import json
import re
from urllib.parse import quote_plus
import random

def get_html(url, driver):
    """Get HTML using existing driver, simulating human behavior"""
    driver.get(url)
    
    # Random wait for page load (3-6 seconds)
    time.sleep(random.uniform(3, 6))
    
    # Simulate scrolling (like a human checking results)
    try:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(random.uniform(0.5, 1.5))
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(random.uniform(0.3, 0.8))
    except:
        pass  # If scroll fails, just continue
    
    # Random "reading" time (2-5 seconds)
    time.sleep(random.uniform(2, 5))
    
    return driver.page_source

def is_blocked(html):
    """Check if blocked by Google Scholar"""
    # Check HTML size (usually small when blocked)
    if len(html) < 10000:
        return True
    
    # Check for CAPTCHA or reCAPTCHA
    html_lower = html.lower()
    if "captcha" in html_lower or "recaptcha" in html_lower:
        return True
    
    return False

def smart_delay(base_delay=3):
    """Smart delay: random delay + occasional long delay"""
    # Base random delay (base_delay ± 50%)
    delay = base_delay * random.uniform(0.5, 1.5)
    
    # 10% chance for longer delay (simulate human behavior)
    if random.random() < 0.1:
        delay += random.uniform(5, 10)

    if random.random() < 0.02:
        delay += random.uniform(120, 180)
    
    return delay

def extract_scholar_ids(html):
    """Extract all Google Scholar IDs from HTML"""
    pattern = r'/citations\?user=([^&]+)&'
    matches = re.findall(pattern, html)
    return list(set(matches))  # Remove duplicates

def build_scholar_url(title):
    """Build Google Scholar search URL"""
    # URL encode title, automatically converts spaces to +
    encoded_title = quote_plus(title)
    return f"https://scholar.google.com/scholar?hl=en&as_sdt=0%2C5&q={encoded_title}&btnG="



def main():

    print(" - - - - - - - - - - Loading paper titles - - - - - - - - - - -")
    with open('cvpr_titles.json', 'r', encoding='utf-8') as f:
        titles = json.load(f)
    print(f"Total: {len(titles)} papers")
    

    print(" - - - - - - - - - - Auto resume - - - - - - - - - - -")
    results = {}
    all_scholar_ids = set()    
    try:
        with open('scholar_results.json', 'r', encoding='utf-8') as f:
            results = json.load(f)
        with open('all_scholar_ids.txt', 'r', encoding='utf-8') as f:
            all_scholar_ids = set(line.strip() for line in f if line.strip())
        print(f"✓ Found existing progress: {len(results)} processed, {len(all_scholar_ids)} unique IDs")
    except FileNotFoundError:
        print("No existing progress found, starting from scratch")

    remaining_titles = [t for t in titles if t not in results]
    print(f"Remaining to process: {len(remaining_titles)} papers\n")
    
    if not remaining_titles:
        print("All papers have been processed! Exit...")
        return
    

    # Start browser (only once, reuse)
    print(" - - - - - - - - - - Starting browser - - - - - - - - - - ")
    options = uc.ChromeOptions()
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-plugins')
    options.add_argument('--headless=new')  
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    driver = uc.Chrome(options=options)
    
    try:
        consecutive_blocks = 0  # Count consecutive blocks
        
        for i, title in enumerate(remaining_titles):
            total_processed = len(results) + i + 1
            print(f"\n[{total_processed}/{len(titles)}] Processing: {title[:60]}...")
            
            # Build URL
            url = build_scholar_url(title)

            # Get HTML
            try:
                html = get_html(url, driver)
                
                # Check if blocked
                blocked = is_blocked(html)
                if blocked:
                    consecutive_blocks += 1
                    print(f"  Blocked {consecutive_blocks} times consecutively")
                    
                    if consecutive_blocks >= 3:
                        print("\n" + "="*60)
                        print("❌ Blocked 3 times consecutively, likely banned by Google Scholar")
                        print("\nExiting program...")
                        print("="*60 + "\n")
                        save_progress(results, all_scholar_ids)
                        break  # Exit for loop, browser will be closed in finally block
                    
                    
                    # Wait longer after being blocked
                    wait_time = 30 * consecutive_blocks
                    print(f"  Waiting {wait_time} seconds before continuing...")
                    time.sleep(wait_time)
                    continue
                
                # Success, reset counter
                consecutive_blocks = 0
                
                # Extract Scholar IDs
                scholar_ids = extract_scholar_ids(html)
                
                if scholar_ids:
                    results[title] = scholar_ids
                    all_scholar_ids.update(scholar_ids)
                    print(f"  ✓ Found {len(scholar_ids)} IDs: {scholar_ids}")
                else:
                    results[title] = []  # Mark as processed but no IDs found
                    print(f"  - No IDs found")
                
                # Save progress every 10 papers
                if (i + 1) % 10 == 0:
                    save_progress(results, all_scholar_ids)
                
                # Smart delay
                delay = smart_delay(base_delay=4) 
                time.sleep(delay)
                
            except Exception as e:
                print(f"  ❌ Error: {e}")
                time.sleep(5)  # Wait 5 seconds after error
                continue
        
        # Final save
        save_progress(results, all_scholar_ids)
        
    finally:
        driver.quit()
        print("\nBrowser closed")


def save_progress(results, all_ids):
    """Save progress"""
    # Save detailed results (paper -> IDs mapping)
    with open('scholar_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Save all unique IDs
    with open('all_scholar_ids.txt', 'w', encoding='utf-8') as f:
        for scholar_id in sorted(all_ids):
            f.write(scholar_id + '\n')
    
    print(f"\nProgress saved")


if __name__ == '__main__':
    main()
