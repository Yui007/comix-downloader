import time
from playwright.sync_api import sync_playwright
import json

def main():
    chapter_url = "https://comix.to/title/93qx2/313361-chapter-1"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
        
        page.add_init_script("""
            window.interceptedImages = null;
            const origParse = JSON.parse;
            JSON.parse = (t, r) => {
                const parsed = origParse(t, r);
                if (parsed && parsed.result && parsed.result.pages && parsed.result.pages.items) {
                    window.interceptedImages = parsed.result.pages.items;
                }
                return parsed;
            };
        """)
        
        print(f"Navigating to {chapter_url}")
        try:
            page.goto(chapter_url, wait_until="domcontentloaded", timeout=60000)
            
            # Wait for images to be intercepted
            images_data = None
            for _ in range(40):
                images_data = page.evaluate("window.interceptedImages")
                if images_data:
                    break
                time.sleep(0.5)
                
            if images_data:
                print(f"Intercepted {len(images_data)} images")
                print(json.dumps(images_data[:10], indent=2))
                
                # Check for any extra keys in the response body!
                # Maybe the whole JSON response has more than just result.pages.items?
            else:
                print("Failed to intercept images. Cloudflare maybe?")
        except Exception as e:
            print("Playwright error:", e)
        finally:
            browser.close()

if __name__ == "__main__":
    main()
