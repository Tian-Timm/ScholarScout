import pandas as pd
from datetime import datetime
from scraper import scrape_faculty_list, get_profile_data
from s2_client import search_and_fetch_papers
from llm_engine import summarize_from_papers, summarize_from_bio

URL = "https://anthropology.stanford.edu/people/faculty-and-affiliates/faculty"
UNI = "Stanford" # Use shorter name for better fuzzy matching coverage

def run():
    print(f"Starting scrape for {URL}")
    # No url_pattern_hint provided, relying on LLM to extract correct links
    faculty_list = scrape_faculty_list(URL)
    print(f"Found {len(faculty_list)} faculty members.")
    
    rows = []
    # Process all faculty members
    for i, person in enumerate(faculty_list):
        print(f"Processing {i+1}/{len(faculty_list)}: {person.get('name', 'Unknown')}")
        name = person.get("name", "Unknown")
        link = person.get("profile_link")
        
        # Fallback if name is missing or generic
        if not name or name == "Unknown":
            continue

        profile = {}
        if link:
            try:
                # Ensure link is absolute (should be handled by scraper but double check)
                if link and not link.startswith("http"):
                    # This logic assumes the scraper returned absolute links, 
                    # but if not, we might need to fix it. 
                    # scraper.py's scrape_faculty_list tries to fix it.
                    pass 
                profile = get_profile_data(link)
            except Exception as e:
                print(f"  Error fetching profile for {name}: {e}")
                profile = {}
        
        # Update name if profile has a better one
        if profile.get("name"):
            name = profile.get("name")
            
        bio = profile.get("bio_text") or ""
        anchors = profile.get("recent_paper_titles") or []
        
        s2 = None
        try:
            # Step 2: S2 Search
            # We use UNI and anchors to verify
            s2 = search_and_fetch_papers(name=name, uni=UNI, anchor_papers=anchors)
        except Exception as e:
            print(f"  Error in S2 search for {name}: {e}")
            s2 = None
            
        row = {"Name": name, "Profile_Link": link, "Research_Summary": "", "Data_Source": ""}
        
        try:
            # Step 3: Decision Logic
            if s2 and s2.get("is_confident_match"):
                print("  -> S2 Match Confirmed")
                summary = summarize_from_papers(s2.get("papers", []), name=name)
                if summary:
                    row["Research_Summary"] = summary
                    row["Data_Source"] = "S2_Verified"
                else:
                    # Fallback to Bio if S2 summary fails (unlikely if papers exist)
                    print("  -> S2 papers found but summary failed, using Bio")
                    summary = summarize_from_bio(bio, name=name)
                    row["Research_Summary"] = summary or "No data available."
                    row["Data_Source"] = "Web_Bio" if summary else "Empty"
            elif bio:
                print("  -> S2 Match Failed/Not Found, using Bio")
                summary = summarize_from_bio(bio, name=name)
                row["Research_Summary"] = summary or "No data available."
                row["Data_Source"] = "Web_Bio" if summary else "Empty"
            else:
                print("  -> No S2 and No Bio")
                row["Research_Summary"] = "No data available."
                row["Data_Source"] = "Empty"
        except Exception as e:
            print(f"  Error generating summary for {name}: {e}")
            # Emergency fallback
            if bio:
                 summary = summarize_from_bio(bio, name=name)
                 row["Research_Summary"] = summary
                 row["Data_Source"] = "Web_Bio"
            else:
                 row["Research_Summary"] = "Error"
                 row["Data_Source"] = "Error"
                 
        rows.append(row)

    # Save to Excel
    if rows:
        df = pd.DataFrame(rows)
        fname = f"Stanford_Anthropology_Test_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        df.to_excel(fname, index=False)
        print(f"Done! Saved to {fname}")
    else:
        print("No data rows generated.")

if __name__ == "__main__":
    run()
