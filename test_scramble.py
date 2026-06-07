import requests
import json

def main():
    url = "https://wowpic.cc/images/40/66432f7a55269.jpg" # Let's find a real URL from the chapter
    # I need to get an actual URL from a chapter, because I don't know the exact URL.
    # Let me parse the COMIC api to get the images.
    from playwright.sync_api import sync_playwright
    import time
    
    chapter_url = "https://comix.to/title/2qow8/310343-chapter-250"
    images = []
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
        try:
            page.goto(chapter_url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(5000)
            images = page.evaluate("window.interceptedImages")
        except Exception as e:
            print("Playwright error:", e)
        browser.close()
        
    if not images:
        print("Failed to intercept images.")
        return
        
    print(f"Intercepted {len(images)} images.")
    # Find a scrambled one
    scrambled = [img for img in images if img.get("s") == 1]
    normal = [img for img in images if img.get("s") != 1]
    
    print(f"Scrambled: {len(scrambled)}, Normal: {len(normal)}")
    
    test_urls = []
    if scrambled: test_urls.append(scrambled[0]["url"])
    if normal: test_urls.append(normal[0]["url"])
    
    for url in test_urls:
        if not url.startswith("http"):
            url = "https://comix.to" + url
        print(f"\\nFetching {url}")
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Referer": "https://comix.to/",
            "Origin": "https://comix.to",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br"
        }
        res = requests.get(url, headers=headers, stream=True)
        print("Status:", res.status_code)
        print("Headers:", dict(res.headers))
        data = res.raw.read(20)
        print("First 20 bytes hex:", data.hex())
        
if __name__ == "__main__":
    main()
