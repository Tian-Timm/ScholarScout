import pandas as pd
import time
import re
import sys
import traceback
from datetime import datetime
from scraper import scrape_faculty_list, get_profile_data
from s2_client import search_and_fetch_papers
from llm_engine import summarize_from_papers, summarize_from_bio

def process_faculty_url(url, university_name, url_pattern_hint=None):
    """
    Main orchestration function.
    """
    print(f"🚀 Starting process for {university_name}...")
    
    # Step 1: Scrape List
    print("📡 Step 1: Scraping faculty list...")
    try:
        faculty_list = scrape_faculty_list(url, url_pattern_hint=url_pattern_hint)
    except Exception as e:
        print(f"❌ Critical Error in Step 1: {e}")
        # Print full traceback for debugging
        traceback.print_exc()
        return []
        
    if not faculty_list:
        print("⚠️ No faculty members found. Exiting.")
        return []
        
    print(f"✅ Found {len(faculty_list)} faculty members.")
    
    final_data = []
    
    print("🕵️ Step 2: Dual-Source verification and summarization...")
    
    total = len(faculty_list)
    for i, person in enumerate(faculty_list):
        name = person.get('name', 'Unknown')
        print(f"[{i+1}/{total}] Processing {name}...")
        
        profile_link = person.get('profile_link')
        email = person.get('email')
        bio_text = ""
        recent_titles = []
        research_interests = []
        try:
            profile_data = get_profile_data(profile_link) if profile_link else {}
            if profile_data.get("name"):
                name = profile_data.get("name") or name
            if profile_data.get("email"):
                email = profile_data.get("email")
            bio_text = profile_data.get("bio_text") or ""
            recent_titles = profile_data.get("recent_paper_titles") or []
            research_interests = profile_data.get("research_interests") or []
        except Exception as e:
            print(f"    ⚠️ Failed to get profile data: {e}")
        row = {
            "Name": name,
            "Title": person.get('title', ''),
            "Email": email or "",
            "Research_Keywords": ", ".join(research_interests),
            "Profile_Link": profile_link,
            "Research_Summary": "",
            "Data_Source": ""
        }
        
        try:
            s2_data = search_and_fetch_papers(name=name, uni=university_name, anchor_papers=recent_titles)
            if s2_data and s2_data.get("is_confident_match"):
                summary = summarize_from_papers(s2_data.get("papers", []), name=name, language=language)
                if summary:
                    row["Research_Summary"] = summary
                    row["Data_Source"] = "S2_Verified"
                else:
                    fallback = summarize_from_bio(bio_text, name=name, language=language)
                    row["Research_Summary"] = fallback or "No data available."
                    row["Data_Source"] = "Web_Bio" if fallback else "Empty"
            elif bio_text:
                summary = summarize_from_bio(bio_text, name=name, language=language)
                row["Research_Summary"] = summary or "No data available."
                row["Data_Source"] = "Web_Bio" if summary else "Empty"
            else:
                row["Research_Summary"] = "No data available."
                row["Data_Source"] = "Empty"
                    
        except Exception as e:
            print(f"   ❌ Error processing {name}: {e}")
            fallback = summarize_from_bio(bio_text, name=name, language=language) if bio_text else ""
            row["Research_Summary"] = fallback or "No data available."
            row["Data_Source"] = "Web_Bio" if fallback else "Empty"
            
        final_data.append(row)
        
    return final_data

def save_to_excel(data_list, filename):
    """
    Saves data to Excel with styling.
    """
    if not data_list:
        print("⚠️ No data to save.")
        return

    df = pd.DataFrame(data_list)
    
    columns_order = [
        "Name", "Title", "Email", "Research_Keywords", "Profile_Link", "Research_Summary", "Data_Source"
    ]
    for col in columns_order:
        if col not in df.columns:
            df[col] = ""
            
    df = df[columns_order]
    
    print(f"💾 Saving to {filename}...")
    
    # Use xlsxwriter for styling
    writer = pd.ExcelWriter(filename, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Faculty Data')
    
    workbook = writer.book
    worksheet = writer.sheets['Faculty Data']
    
    header_format = workbook.add_format({'bold': True, 'bottom': 1})
    
    for col_num, value in enumerate(df.columns.values):
        worksheet.write(0, col_num, value, header_format)
        
    for i, col in enumerate(df.columns):
        column_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
        if column_len > 50:
            column_len = 50
        worksheet.set_column(i, i, column_len)

    writer.close()
    print("✅ Excel saved successfully.")

if __name__ == "__main__":
    # Test Entry Point
    print("🎓 University Faculty Scraper & Verifier System")
    print("="*50)
    
    # Default for testing
    default_url = "https://ischool.utexas.edu/people/faculty-staff-students/full-time-faculty"
    default_uni = "University of Texas at Austin"
    
    target_url = input(f"Enter Faculty List URL [Default: {default_url}]: ").strip() or default_url
    target_uni = input(f"Enter University Name [Default: {default_uni}]: ").strip() or default_uni
    
    start_time = time.time()
    
    # Configuration Logic for URL Hints
    url_pattern_hint = None
    if "byu" in target_uni.lower() or "brigham young" in target_uni.lower():
        print("💡 Detected BYU: Applying 'faculty-directory' URL hint.")
        url_pattern_hint = "faculty-directory"
    
    data = process_faculty_url(target_url, target_uni, url_pattern_hint=url_pattern_hint)
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    # Generate Filename
    # Clean university name: remove spaces, special chars
    clean_uni_name = re.sub(r'[^a-zA-Z0-9]', '_', target_uni)
    # Remove consecutive underscores
    clean_uni_name = re.sub(r'_+', '_', clean_uni_name).strip('_')
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"{clean_uni_name}_{timestamp}.xlsx"
    
    save_to_excel(data, filename)
    
    if data:
        total_scraped = len(data)
        print("\n📊 Summary Report")
        print("="*30)
        print(f"Total Scraped: {total_scraped}")
        by_source = {}
        for row in data:
            src = row.get("Data_Source") or "Empty"
            by_source[src] = by_source.get(src, 0) + 1
        for k, v in by_source.items():
            print(f"{k}: {v}")
        print(f"Total Time: {elapsed_time:.2f} seconds")
        print("="*30)
    else:
        print("\n📊 Summary Report")
        print("="*30)
        print("Total Scraped: 0")
        print(f"Total Time: {elapsed_time:.2f} seconds")
        print("="*30)
    
    print("\n🎉 Process Complete!")
