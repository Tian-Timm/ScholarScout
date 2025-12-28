import os
from dotenv import load_dotenv
from s2_client import search_author_by_name_and_uni

# Load env
load_dotenv()

def check_env():
    print("🔍 Checking Environment Variables...")
    s2_key = os.getenv("S2_API_KEY")
    if s2_key:
        print(f"✅ S2_API_KEY found: {s2_key[:4]}...{s2_key[-4:]}")
    else:
        print("❌ S2_API_KEY NOT found!")

    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    if deepseek_key:
        print(f"✅ DEEPSEEK_API_KEY found: {deepseek_key[:4]}...{deepseek_key[-4:]}")
    else:
        print("❌ DEEPSEEK_API_KEY NOT found!")

def run_test():
    check_env()
    
    # Using 'Anthropology' as a likely keyword based on context, 
    # but the search should work even if keyword is not perfectly matched if name+uni works.
    test_cases = [
        {"name": "Angela Garcia", "uni": "Stanford University", "keyword": "Anthropology"}, 
        {"name": "Andrew Bauer", "uni": "Stanford University", "keyword": "Anthropology"}
    ]
    
    print("\n🚀 Starting Test Run for 2 Authors...")
    
    for person in test_cases:
        name = person["name"]
        uni = person["uni"]
        keyword = person["keyword"]
        
        print(f"\nProcessing: {name} ({uni}) [Keyword: {keyword}]")
        
        try:
            result = search_author_by_name_and_uni(name, uni, keyword)
            if result:
                print(f"✅ Match Found: {result.get('name')} (ID: {result.get('authorId')})")
                print(f"   Status: {result.get('verification_status')}")
                papers = result.get('papers', [])
                print(f"   Papers Found: {len(papers)}")
                if not papers:
                    print("   ⚠️ No papers returned! Check if details fetch failed.")
                for p in papers[:3]:
                    print(f"   - [{p.get('year')}] {p.get('title')} (Citations: {p.get('citationCount')})")
            else:
                print(f"❌ No match found for {name}")
        except Exception as e:
            print(f"❌ Exception occurred: {e}")

if __name__ == "__main__":
    run_test()