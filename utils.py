from bs4 import BeautifulSoup

def clean_html(raw_html: str) -> str:
    """
    Cleans raw HTML by removing unwanted tags and extracting text.
    
    Args:
        raw_html (str): The raw HTML string to clean.
        
    Returns:
        str: The cleaned text content.
    """
    if not raw_html:
        return ""
        
    soup = BeautifulSoup(raw_html, 'html.parser')
    
    # If there is no body, we might be dealing with a fragment or just head
    # But usually we expect a full page. If no body, use the whole soup.
    target = soup.body if soup.body else soup
    
    # Tags to remove
    unwanted_tags = [
        'script', 'style', 'nav', 'footer', 'header', 
        'svg', 'button', 'input', 'form', 'iframe'
    ]
    
    for tag in target.find_all(unwanted_tags):
        tag.decompose()
        
    # Preserve links in content before extracting text
    # Convert <a href="url">text</a> to text (url)
    for a_tag in target.find_all('a', href=True):
        url = a_tag['href']
        text = a_tag.get_text(strip=True)
        if url and text:
             a_tag.replace_with(f"{text} ({url})")
    
    return target.get_text(separator='\n', strip=True)
