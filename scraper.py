import os
import requests
import json
import traceback
import random
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from dotenv import load_dotenv
from scrapegraphai.graphs import SmartScraperGraph
from utils import clean_html

# Load environment variables
load_dotenv()

def check_link_reachability(links, sample_size=3):
    """
    Randomly checks a few links to ensure they are reachable (not 404).
    Returns True if passed, False if failed.
    """
    if not links:
        return True
    
    sample = random.sample(links, min(len(links), sample_size))
    print(f"🕵️ Verifying link reachability with {len(sample)} samples...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    failures = 0
    for link in sample:
        try:
            # Use HEAD request first, fallback to GET if needed
            response = requests.head(link, headers=headers, timeout=5)
            if response.status_code == 404:
                # Double check with GET in case server blocks HEAD
                response = requests.get(link, headers=headers, timeout=5)
                if response.status_code == 404:
                    print(f"    ❌ Link 404: {link}")
                    failures += 1
            elif response.status_code >= 400:
                 print(f"    ⚠️ Link error {response.status_code}: {link}")
                 # We treat 404 as critical, others as warnings for now
        except Exception as e:
            print(f"    ⚠️ Connection failed for {link}: {e}")
            
    if failures > 0 and failures == len(sample):
        print("❌ All sampled links failed. Aborting.")
        return False
    return True

def make_links_absolute(html_content, base_url):
    """
    Converts all relative links in the HTML to absolute URLs.
    This helps the LLM see the full URL instead of guessing.
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        for a in soup.find_all('a', href=True):
            a['href'] = urljoin(base_url, a['href'])
        return str(soup)
    except Exception as e:
        print(f"⚠️ Error in make_links_absolute: {e}")
        return html_content

def scrape_faculty_list(url: str, url_pattern_hint: str = None):
    """
    Scrapes a faculty list from a given URL.
    Strategies:
    1. Pre-process HTML to make all links absolute (fixes LLM guessing).
    2. Use LLM to extract names and links.
    3. Validate links with Reachability Check and Hint matching.
    
    Args:
        url (str): The URL of the faculty page.
        url_pattern_hint (str): Keyword that MUST be present in valid profile links.
        
    Returns:
        list: A list of faculty members with name, title, and profile_link.
    """
    print(f"🚀 Starting scrape for: {url}")
    
    # 1. Fetch
    print("📥 Fetching HTML...")
    proxy = os.getenv("HTTP_PROXY")
    proxies = {}
    if proxy:
        proxies = {
            "http": proxy,
            "https": proxy
        }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, proxies=proxies, timeout=30)
        response.raise_for_status()
        html_content = response.text
    except requests.RequestException as e:
        print(f"❌ Error fetching URL: {e}")
        return []

    # Strategy: Absolutize Links BEFORE cleaning
    # This ensures the LLM sees "https://cs.byu.edu/.../chris-archibald" instead of "chris-archibald"
    # which prevents it from hallucinating the path.
    print("🔗 Pre-processing: Converting relative links to absolute...")
    html_content = make_links_absolute(html_content, url)

    # 2. Clean (for LLM)
    print("🧹 Cleaning HTML...")
    cleaned_text = clean_html(html_content)
    # print(f"Cleaned Text Preview:\n{cleaned_text[:500]}...") # Debug preview

    # 3. Parse with SmartScraperGraph
    print("🧠 Parsing with DeepSeek...")
    
    deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
    if not deepseek_api_key:
        print("❌ DEEPSEEK_API_KEY not found in .env")
        return []

    # LLM Config for DeepSeek (OpenAI-compatible)
    llm_config = {
        "api_key": os.getenv("DEEPSEEK_API_KEY"),
        "model": "openai/deepseek-chat",
        "model_name": "deepseek-chat",
        "base_url": "https://api.deepseek.com",
    }
    
    graph_config = {
        "llm": llm_config,
        "verbose": True,
        "headless": True,
    }

    # Initialize SmartScraperGraph with error handling
    try:
        if not cleaned_text:
            raise ValueError("Cleaned text is empty")

        # More explicit prompt to force JSON structure
        prompt = """
        You are a data extraction agent.
        Extract a list of faculty members from the text.
        
        Strictly return a JSON LIST of objects. Do not include any markdown formatting (like ```json).
        Each object must have these keys:
        - "name": Full name of the faculty member.
        - "title": Job title (e.g., Professor, Assistant Professor).
        - "profile_link": The URL to their profile page. If it is a relative path, keep it as is. If not found, use null.
        - "email": Email address if available, else null.
        
        Example Output:
        [
            {"name": "John Doe", "title": "Professor", "profile_link": "/people/john-doe", "email": "john@example.com"},
            {"name": "Jane Smith", "title": "Assistant Professor", "profile_link": "https://example.com/jane", "email": null}
        ]
        """

        scraper = SmartScraperGraph(
            prompt=prompt,
            source=cleaned_text,
            config=graph_config
        )
        
        result = scraper.run()
    except Exception as e:
        print(f"❌ Error inside scraper: {e}")
        traceback.print_exc()
        return []

    try:
        # Validate result structure
        if not isinstance(result, list):
            # Sometimes LLM returns a dict with a key like "faculty" or "result"
            if isinstance(result, dict):
                # Try to find a list value
                for key, value in result.items():
                    if isinstance(value, list):
                        result = value
                        break
                else:
                    # If still dict, maybe it's a single object? Wrap it.
                    result = [result]
            else:
                print(f"⚠️ Unexpected result type: {type(result)}. Content: {result}")
                return []

        # Double check if list elements are dicts
        valid_result = []
        for item in result:
            if isinstance(item, dict):
                valid_result.append(item)
            elif isinstance(item, str):
                # Try to parse if it's a JSON string
                try:
                    parsed = json.loads(item)
                    if isinstance(parsed, dict):
                        valid_result.append(parsed)
                except:
                    print(f"⚠️ Skipping invalid list item (string): {item[:50]}...")
            else:
                print(f"⚠️ Skipping invalid list item type: {type(item)}")

        result = valid_result

        # Post-processing: Fix relative URLs
        for person in result:
            link = person.get('profile_link')
            if link and isinstance(link, str):
                if not link.startswith('http'):
                     # 自动将相对路径拼接为绝对路径 (Should be handled by pre-processing but double check)
                    person['profile_link'] = urljoin(url, link)
        
        # Validation Level 1.5
        if url_pattern_hint:
             print(f"🔍 Validating links with hint: '{url_pattern_hint}'...")
             valid_count = 0
             for person in result:
                 link = person.get('profile_link')
                 if link and url_pattern_hint in link:
                     valid_count += 1
                 else:
                     # Mark as suspicious or clear it? 
                     # The user said: "System should automatically mark as Status = [Review Needed]"
                     # But this function returns a simple list. We can't set status here easily without changing schema.
                     # We will print a warning and let the main loop handle confidence.
                     # However, if the link is clearly wrong, we might want to nullify it so we don't scrape garbage.
                     print(f"    ⚠️ Link mismatch hint: {link}")
                     # person['profile_link'] = None # Optional: be strict?
             
             print(f"    ✅ {valid_count}/{len(result)} links matched hint.")

        # Check reachability on a sample
        valid_links = [p['profile_link'] for p in result if p.get('profile_link')]
        check_link_reachability(valid_links)
                    
        return result
    except Exception as e:
        print(f"❌ Error during graph execution: {e}")
        traceback.print_exc()
        return []

def scrape_profile_details(url: str):
    """
    Scrapes an individual profile page to extract search keywords and bio summary.
    
    Args:
        url (str): The profile URL.
        
    Returns:
        dict: { "search_keyword": str, "bio_summary": str }
    """
    print(f"    🔍 Scraping profile details: {url}")
    
    # 1. Fetch
    proxy = os.getenv("HTTP_PROXY")
    proxies = {}
    if proxy:
        proxies = {
            "http": proxy,
            "https": proxy
        }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, proxies=proxies, timeout=15)
        response.raise_for_status()
        html_content = response.text
    except requests.RequestException as e:
        print(f"    ❌ Error fetching profile: {e}")
        return {"search_keyword": None, "bio_summary": None}

def get_profile_data(url: str):
    print(f"    🔍 Scraping profile content: {url}")
    proxy = os.getenv("HTTP_PROXY")
    proxies = {}
    if proxy:
        proxies = {"http": proxy, "https": proxy}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, proxies=proxies, timeout=15)
        response.raise_for_status()
        html_content = response.text
    except requests.RequestException:
        return {"name": None, "bio_text": None, "email": None, "research_interests": [], "recent_paper_titles": []}
    cleaned_text = clean_html(html_content)
    cleaned_text = cleaned_text[:15000]
    deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
    if not deepseek_api_key:
        name = None
        bio_text = cleaned_text
        return {"name": name, "bio_text": bio_text, "email": None, "research_interests": [], "recent_paper_titles": []}
    graph_config = {
        "llm": {
            "api_key": deepseek_api_key,
            "model": "openai/deepseek-chat",
            "model_name": "deepseek-chat",
            "base_url": "https://api.deepseek.com",
            "openai_api_base": "https://api.deepseek.com",
        },
        "verbose": False,
        "headless": True,
    }
    prompt = """
    Extract a JSON object with keys:
    - "name": inferred person name if present, else null
    - "bio_text": main biography or profile description text (required; if no explicit bio section, return main content)
    - "email": email address if found, else null
    - "research_interests": list of specific research interests or keywords found, else empty list
    - "recent_paper_titles": up to 2 publication titles if a Publications or Selected Works section exists, else empty list
    Return only JSON.
    """
    scraper = SmartScraperGraph(prompt=prompt, source=cleaned_text, config=graph_config)
    try:
        result = scraper.run()
        if isinstance(result, dict):
            name = result.get("name")
            bio_text = result.get("bio_text")
            email = result.get("email")
            interests = result.get("research_interests") or []
            recent = result.get("recent_paper_titles") or []
            if not bio_text:
                bio_text = cleaned_text
            if not isinstance(recent, list):
                recent = []
            if not isinstance(interests, list):
                interests = []
            return {
                "name": name, 
                "bio_text": bio_text, 
                "email": email,
                "research_interests": interests,
                "recent_paper_titles": recent[:2]
            }
        if isinstance(result, list) and len(result) > 0 and isinstance(result[0], dict):
            obj = result[0]
            name = obj.get("name")
            bio_text = obj.get("bio_text") or cleaned_text
            email = obj.get("email")
            interests = obj.get("research_interests") or []
            recent = obj.get("recent_paper_titles") or []
            if not isinstance(recent, list):
                recent = []
            if not isinstance(interests, list):
                interests = []
            return {
                "name": name, 
                "bio_text": bio_text, 
                "email": email,
                "research_interests": interests,
                "recent_paper_titles": recent[:2]
            }
        return {"name": None, "bio_text": cleaned_text, "email": None, "research_interests": [], "recent_paper_titles": []}
    except Exception:
        return {"name": None, "bio_text": cleaned_text, "email": None, "research_interests": [], "recent_paper_titles": []}

    # 2. Clean
    cleaned_text = clean_html(html_content)
    # Truncate if too long to save tokens, but keep enough for bio
    cleaned_text = cleaned_text[:15000] 

    # 3. Parse with DeepSeek
    deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
    if not deepseek_api_key:
        return {"search_keyword": None, "bio_summary": None}

    graph_config = {
        "llm": {
            "api_key": deepseek_api_key,
            "model": "openai/deepseek-chat",
            "model_name": "deepseek-chat",
            "base_url": "https://api.deepseek.com",
            "openai_api_base": "https://api.deepseek.com",
        },
        "verbose": False, # Reduce noise
        "headless": True,
    }

    # Precise prompt for keyword and bio
    prompt = """
    Analyze the profile text. 
    1. Extract ONE specific academic discipline keyword in English (e.g., 'Anthropology', 'Computer Science', 'Bioinformatics'). 
    2. Extract a very brief bio summary (max 50 words).
    Return JSON: {"search_keyword": "...", "bio_summary": "..."}
    """

    scraper = SmartScraperGraph(
        prompt=prompt,
        source=cleaned_text,
        config=graph_config
    )

    try:
        result = scraper.run()
        # Ensure result is dict
        if isinstance(result, dict):
            return result
        # Sometimes list is returned if prompt implies list
        if isinstance(result, list) and len(result) > 0:
            return result[0]
        return {"search_keyword": None, "bio_summary": None}
    except Exception as e:
        print(f"    ❌ Error analyzing profile: {e}")
        return {"search_keyword": None, "bio_summary": None}

if __name__ == "__main__":
    # Test URL
    test_url = "https://ischool.utexas.edu/people/faculty-staff-students/full-time-faculty"
    
    print("-" * 50)
    print("Testing scrape_faculty_list")
    print("-" * 50)
    
    faculty_data = scrape_faculty_list(test_url)
    
    print("\n✅ Extraction Result:")
    print(json.dumps(faculty_data, indent=2, ensure_ascii=False))
