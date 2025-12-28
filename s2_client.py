import os
import time
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def search_author_by_name_and_uni(name: str, university: str, keyword: str = None):
    """
    Search for an author using Semantic Scholar Graph API.
    
    Args:
        name (str): Name of the author.
        university (str): University or affiliation.
        keyword (str, optional): Academic keyword (e.g., 'Anthropology').
        
    Returns:
        dict: Top 1 author details or None if not found.
    """
    base_url = "https://api.semanticscholar.org/graph/v1/author/search"
    
    # Configure Proxy
    proxy = os.getenv("HTTP_PROXY")
    proxies = {}
    if proxy:
        proxies = {
            "http": proxy,
            "https": proxy
        }
    
    # Configure Headers (API Key)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    s2_api_key = os.getenv("S2_API_KEY")
    if s2_api_key:
        headers["x-api-key"] = s2_api_key
        
    # Search Fields (Basic Info) - STRICTLY FLAT to avoid API 400
    search_fields = "authorId,name,affiliations,paperCount,citationCount"

    def _get_author_details(author_id):
        """Fetch papers for the specific author (Detailed Fields)."""
        url = f"https://api.semanticscholar.org/graph/v1/author/{author_id}"
        # Use top-level limit for papers and flattened fields to be safe
        params = {
            "fields": "authorId,name,affiliations,papers.title,papers.year,papers.citationCount",
            "limit": 5
        }
        return _make_api_call(url, params)

    def _make_api_call(url, params):
        # Retry logic for 429
        max_retries = 3  # Increased retries
        for attempt in range(max_retries + 1):
            try:
                response = requests.get(url, params=params, headers=headers, proxies=proxies, timeout=10)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    # Check if API Key is present
                    has_api_key = "x-api-key" in headers
                    wait_time = 1 if has_api_key else 5
                    print(f"⚠️ 429 Too Many Requests. Retrying in {wait_time} seconds... (Attempt {attempt+1}/{max_retries+1})")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"❌ API Error {response.status_code}: {response.text}")
                    return None
            except requests.RequestException as e:
                print(f"❌ Request failed: {e}")
                return None
        return None

    selected_author = None
    verification_status = "needs_manual_check"
    
    # Helper for checking match
    def _check_affiliation_match(author, target_str):
        if not author or not target_str:
            return False
        affs = author.get("affiliations", [])
        if not affs:
            return False
        target_key = target_str.lower()
        return any(target_key in aff.lower() for aff in affs)

    # Attempt 1: Name + University
    print(f"🔍 Attempt 1: Searching '{name} {university}'")
    params_1 = {"query": f"{name} {university}", "fields": search_fields, "limit": 1}
    result_1 = _make_api_call(base_url, params_1)
    
    if result_1 and result_1.get("data"):
        cand = result_1["data"][0]
        if _check_affiliation_match(cand, university):
            selected_author = cand
            verification_status = "verified_by_query_uni"
            print(f"✅ Attempt 1 Success: {cand.get('name')} (Affiliation Match)")
            
    # Attempt 2: Name + Keyword (if provided and Attempt 1 failed)
    if not selected_author and keyword:
        print(f"🔍 Attempt 2: Searching '{name} {keyword}'")
        params_2 = {"query": f"{name} {keyword}", "fields": search_fields, "limit": 1}
        result_2 = _make_api_call(base_url, params_2)
        
        if result_2 and result_2.get("data"):
            cand = result_2["data"][0]
            # If found by keyword search, we trust S2 matched the keyword (in papers or aff).
            # We also check affiliation for university as a bonus.
            if _check_affiliation_match(cand, university):
                 verification_status = "verified_by_query_keyword_uni_match"
                 print(f"✅ Attempt 2 Success: {cand.get('name')} (Affiliation matches Uni)")
            else:
                 verification_status = "verified_by_query_keyword"
                 print(f"✅ Attempt 2 Success: {cand.get('name')} (Found by Keyword Search)")
            selected_author = cand

    # Attempt 3: Fallback Name Only + Re-ranking
    if not selected_author:
        print(f"⚠️ Attempts 1 & 2 failed. Attempt 3: Fallback to name only '{name}' with Re-ranking")
        params_3 = {"query": name, "fields": search_fields, "limit": 10}
        result_3 = _make_api_call(base_url, params_3)
        
        if result_3 and result_3.get("data"):
            candidates = result_3["data"]
            found_match = False
            
            # Manual Re-ranking
            for cand in candidates:
                # 1. Check University in Affiliations
                if _check_affiliation_match(cand, university):
                    selected_author = cand
                    verification_status = "verified_by_rerank_uni"
                    found_match = True
                    print(f"✅ Re-ranking found match (Uni): {cand.get('name')}")
                    break
                
                # 2. Check Keyword in Affiliations
                if keyword and _check_affiliation_match(cand, keyword):
                    selected_author = cand
                    verification_status = "verified_by_rerank_keyword"
                    found_match = True
                    print(f"✅ Re-ranking found match (Keyword in Aff): {cand.get('name')}")
                    break
            
            # If no match found in re-ranking, pick Top 1
            if not found_match:
                selected_author = candidates[0]
                verification_status = "needs_manual_check"
                print(f"⚠️ No enhanced match in Top 10. Using Top 1: {selected_author.get('name')}")

    # Final Step: Fetch Detailed Info (Papers) for the Locked Author
    if selected_author:
        author_id = selected_author['authorId']
        print(f"📄 Fetching detailed papers for Author ID: {author_id}...")
        details = _get_author_details(author_id)
        if details:
            # Update selected_author with detailed info (especially papers)
            selected_author.update(details)
        
        selected_author["verification_status"] = verification_status
        return selected_author
        
    return None

def search_and_fetch_papers(name: str, uni: str, anchor_papers: list[str] | None = None):
    base_url = "https://api.semanticscholar.org/graph/v1/author/search"
    proxy = os.getenv("HTTP_PROXY")
    proxies = {}
    if proxy:
        proxies = {"http": proxy, "https": proxy}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    s2_api_key = os.getenv("S2_API_KEY")
    if s2_api_key:
        headers["x-api-key"] = s2_api_key
    search_fields = "authorId,name,affiliations,paperCount,citationCount"
    def _make_api_call(url, params):
        max_retries = 3
        for attempt in range(max_retries + 1):
            try:
                response = requests.get(url, params=params, headers=headers, proxies=proxies, timeout=10)
                if response.status_code == 200:
                    return response.json()
                if response.status_code == 429:
                    has_api_key = "x-api-key" in headers
                    wait_time = 1 if has_api_key else 5
                    time.sleep(wait_time)
                    continue
                return None
            except requests.RequestException:
                return None
        return None
    def _get_author_details(author_id):
        url = f"https://api.semanticscholar.org/graph/v1/author/{author_id}"
        params = {
            "fields": "authorId,name,affiliations,papers.title,papers.year,papers.tldr",
            "limit": 25
        }
        data = _make_api_call(url, params)
        if not data:
            params_fallback = {
                "fields": "authorId,name,affiliations,papers.title,papers.year",
                "limit": 25
            }
            data = _make_api_call(url, params_fallback)
        return data
    def _norm(s):
        if not s:
            return ""
        return "".join(ch.lower() for ch in s if ch.isalnum() or ch.isspace())
    def _affil_fuzzy_match(affs, target):
        if not affs or not target:
            return False
        t = _norm(target)
        for a in affs:
            if _norm(a).find(t) != -1:
                return True
        return False
    def _has_anchor_paper(papers, anchors):
        if not anchors:
            return False
        anchors_norm = {a.strip().lower() for a in anchors if isinstance(a, str)}
        for p in papers or []:
            title = (p.get("title") or "").strip().lower()
            if title in anchors_norm:
                return True
        return False
    try:
        params = {"query": f"{name} {uni}", "fields": search_fields, "limit": 5}
        search = _make_api_call(base_url, params)
        candidates = search.get("data") if search else []
        locked = None
        if candidates:
            for cand in candidates:
                details = _get_author_details(cand["authorId"])
                papers = details.get("papers") if details else []
                if anchor_papers and _has_anchor_paper(papers, anchor_papers):
                    locked = details
                    break
                if not anchor_papers and _affil_fuzzy_match(cand.get("affiliations", []), uni):
                    locked = details
                    break
        if not locked:
            return None
        year_now = int(time.strftime("%Y"))
        recent = []
        for p in locked.get("papers", []):
            y = p.get("year")
            if isinstance(y, int) and y >= year_now - 2:
                recent.append({
                    "title": p.get("title"),
                    "year": y,
                    "tldr": p.get("tldr")
                })
        result = {
            "is_confident_match": True,
            "authorId": locked.get("authorId"),
            "name": locked.get("name"),
            "affiliations": locked.get("affiliations"),
            "papers": recent
        }
        return result
    except Exception:
        return None
if __name__ == "__main__":
    # Test case
    test_name = "Ying Ding"
    test_uni = "University of Texas Austin"
    test_keyword = "Information" # Example keyword
    
    print("-" * 50)
    print("Testing s2_client.py with Keyword Support")
    print("-" * 50)
    
    # Test 1: Standard Search
    print("\n--- Test 1: Standard Search (Name + Uni) ---")
    author_data = search_author_by_name_and_uni(test_name, test_uni)
    if author_data:
        print(f"Found: {author_data.get('name')} | Status: {author_data.get('verification_status')}")
    else:
        print("Not found.")

    # Test 2: Keyword Search (Simulating a case where Uni might be ambiguous or missing in Affiliation but Keyword helps)
    # We use a name that might need keyword disambiguation
    test_name_2 = "Wei Wang"
    test_uni_2 = "University of California Los Angeles"
    test_keyword_2 = "Computer Science"
    
    print(f"\n--- Test 2: Keyword Search ({test_name_2} + {test_keyword_2}) ---")
    author_data_2 = search_author_by_name_and_uni(test_name_2, test_uni_2, keyword=test_keyword_2)
    
    if author_data_2:
        print("\n✅ Author Found:")
        print(f"Name: {author_data_2.get('name')}")
        print(f"Author ID: {author_data_2.get('authorId')}")
        print(f"Affiliations: {author_data_2.get('affiliations')}")
        print(f"Status: {author_data_2.get('verification_status')}")
        print("\n📚 Top 5 Papers:")
        for paper in author_data_2.get("papers", []):
            print(f"- [{paper.get('year')}] {paper.get('title')} (Citations: {paper.get('citationCount')})")
    else:
        print("\n❌ Author not found.")
