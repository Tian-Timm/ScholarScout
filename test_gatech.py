import pandas as pd
from datetime import datetime
from scraper import scrape_faculty_list, get_profile_data
from s2_client import search_and_fetch_papers
from llm_engine import summarize_from_papers, summarize_from_bio

URL = "https://dm.lmc.gatech.edu/people/faculty-and-staff/"
UNI = "Georgia Institute of Technology"

def run():
    faculty_list = scrape_faculty_list(URL)
    faculty_list = faculty_list[:3]
    rows = []
    for person in faculty_list:
        name = person.get("name", "Unknown")
        link = person.get("profile_link")
        profile = get_profile_data(link) if link else {}
        if profile.get("name"):
            name = profile.get("name") or name
        bio = profile.get("bio_text") or ""
        anchors = profile.get("recent_paper_titles") or []
        try:
            s2 = search_and_fetch_papers(name=name, uni=UNI, anchor_papers=anchors)
        except Exception:
            s2 = None
        row = {"Name": name, "Profile_Link": link, "Research_Summary": "", "Data_Source": ""}
        try:
            if s2 and s2.get("is_confident_match"):
                summary = summarize_from_papers(s2.get("papers", []), name=name)
                if summary:
                    row["Research_Summary"] = summary
                    row["Data_Source"] = "S2_Verified"
                else:
                    summary = summarize_from_bio(bio, name=name)
                    row["Research_Summary"] = summary or "No data available."
                    row["Data_Source"] = "Web_Bio" if summary else "Empty"
            elif bio:
                summary = summarize_from_bio(bio, name=name)
                row["Research_Summary"] = summary or "No data available."
                row["Data_Source"] = "Web_Bio" if summary else "Empty"
            else:
                row["Research_Summary"] = "No data available."
                row["Data_Source"] = "Empty"
        except Exception:
            summary = summarize_from_bio(bio, name=name) if bio else ""
            row["Research_Summary"] = summary or "No data available."
            row["Data_Source"] = "Web_Bio" if summary else "Empty"
        rows.append(row)
    df = pd.DataFrame(rows)
    fname = f"Gatech_DigitalMedia_Test_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    df.to_excel(fname, index=False)
    print(fname)
    print(df.to_string(index=False))

if __name__ == "__main__":
    run()
