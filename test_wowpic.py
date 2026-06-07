from playwright.sync_api import sync_playwright

def main():
    # We will use playwright to fetch a wowpic url directly!
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        url = "https://wowpic.cc/images/40/66432f7a55269.jpg" # I don't know if this exists
        
        try:
            res = page.goto(url)
            print("Status:", res.status)
            body = res.body()
            print("Size:", len(body))
            print("Hex:", body[:20].hex())
        except Exception as e:
            print("Error:", e)
            
        browser.close()

if __name__ == "__main__":
    main()
