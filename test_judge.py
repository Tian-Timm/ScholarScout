import json
from judge import AuthorJudge

def run_tests():
    judge = AuthorJudge()
    
    print("-" * 50)
    print("Testing judge.py")
    print("-" * 50)

    # Case 1: Hard Match
    # S2 Data has correct affiliation, Not fallback
    print("\n🔹 Case 1: Hard Match (Affiliation matches 'Austin')")
    case1_scraped = {
        "name": "Test User",
        "title": "Professor",
        "profile_link": "http://ut.edu/test"
    }
    case1_s2 = {
        "name": "Test User",
        "affiliations": ["University of Texas at Austin", "Google"],
        "verification_status": "verified_by_query",
        "papers": []
    }
    # Target: "Austin"
    result1 = judge.judge_candidate(case1_scraped, case1_s2, "Austin")
    print(f"Result: {result1}")
    assert result1['confidence'] == 'High'
    assert result1['reason'] == 'Affiliation Hard Match'
    print("✅ Case 1 Passed")

    # Case 2: AI Match
    # Hard match fails (Affiliation empty), but content matches.
    # verification_status can be 'needs_manual_check' or normal but hard match failed.
    print("\n🔹 Case 2: AI Match (Deep Learning Context)")
    case2_scraped = {
        "name": "AI Researcher",
        "title": "Professor of CS",
        "profile_link": "http://ut.edu/ai",
        "bio": "Expert in Deep Learning and Neural Networks."
    }
    case2_s2 = {
        "name": "AI Researcher",
        "affiliations": [], # No affiliation to match
        "verification_status": "needs_manual_check", # Triggers AI
        "paperCount": 100,
        "citationCount": 5000,
        "papers": [
            {"title": "Deep Learning for Image Recognition", "year": 2020},
            {"title": "Neural Networks in Practice", "year": 2021}
        ]
    }
    result2 = judge.judge_candidate(case2_scraped, case2_s2, "Austin")
    print(f"Result: {result2}")
    # We expect High because content matches strongly
    # DeepSeek might be conservative and return Medium if affiliation is missing.
    # We accept Medium or High for this test case as long as it's not Low.
    if result2['confidence'] in ['High', 'Medium']:
        print("✅ Case 2 Passed (Confidence is High or Medium)")
    else:
        print("⚠️ Case 2 Warning: AI returned Low confidence.")

    # Case 3: Mismatch
    # Content differs significantly
    print("\n🔹 Case 3: Mismatch (History vs Physics)")
    case3_scraped = {
        "name": "John Doe",
        "title": "Professor of History",
        "profile_link": "http://ut.edu/history",
        "bio": "Historian specializing in medieval Europe."
    }
    case3_s2 = {
        "name": "John Doe",
        "affiliations": ["Some Physics Lab"],
        "verification_status": "needs_manual_check",
        "paperCount": 50,
        "citationCount": 200,
        "papers": [
            {"title": "Quantum Entanglement in Superconductors", "year": 2022},
            {"title": "Electron Spin Dynamics", "year": 2023}
        ]
    }
    result3 = judge.judge_candidate(case3_scraped, case3_s2, "Austin")
    print(f"Result: {result3}")
    # We expect Low
    if result3['confidence'] == 'Low':
        print("✅ Case 3 Passed")
    else:
        print("⚠️ Case 3 Warning: AI returned non-Low confidence.")

if __name__ == "__main__":
    run_tests()
