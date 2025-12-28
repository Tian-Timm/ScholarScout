from utils import clean_html

def test_clean_html():
    raw_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>University Page</title>
        <style>
            body { font-family: sans-serif; }
            .hidden { display: none; }
        </style>
        <script>
            console.log("Tracking user...");
            function badStuff() { return true; }
        </script>
    </head>
    <body>
        <header>
            <nav>
                <ul>
                    <li><a href="/">Home</a></li>
                    <li><a href="/about">About</a></li>
                </ul>
                <button>Login</button>
            </nav>
            <h1>University of Science</h1>
        </header>
        
        <div class="content">
            <p>Welcome to the faculty page.</p>
            <div class="profile">
                <h2>Professor Wei Wang</h2>
                <p>Department of Computer Science</p>
                <p>Research Interests: AI, Data Mining</p>
                <span>link: https://scholar.google.com/citations?user=12345</span>
            </div>
            
            <form action="/search">
                <input type="text" name="q" placeholder="Search...">
                <button type="submit">Search</button>
            </form>
            
            <iframe src="ads.html"></iframe>
            <svg width="100" height="100"><circle cx="50" cy="50" r="40" /></svg>
        </div>

        <footer>
            <p>&copy; 2024 University. All rights reserved.</p>
            <div class="links">
                <a href="/privacy">Privacy Policy</a>
            </div>
        </footer>
        
        <script>
            // More analytics code
            var x = 100;
        </script>
    </body>
    </html>
    """

    print("--- Starting Test for clean_html ---")
    
    original_len = len(raw_html)
    cleaned_text = clean_html(raw_html)
    cleaned_len = len(cleaned_text)
    
    print(f"Original: {original_len} chars -> Cleaned: {cleaned_len} chars")
    print("-" * 30)
    print("Cleaned Content:")
    print("-" * 30)
    print(cleaned_text)
    print("-" * 30)
    
    # Assertions to verify requirements
    assert "Professor Wei Wang" in cleaned_text
    assert "link: https://scholar.google.com/citations?user=12345" in cleaned_text
    assert "console.log" not in cleaned_text
    assert "Home" not in cleaned_text # nav should be removed
    assert "Login" not in cleaned_text # button inside nav should be removed
    assert "Search..." not in cleaned_text # input should be removed
    assert "Privacy Policy" not in cleaned_text # footer should be removed
    
    print("✅ Test Passed: Content preserved and noise removed.")

if __name__ == "__main__":
    test_clean_html()
