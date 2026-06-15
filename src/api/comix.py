"""
Comix.to API wrapper for manga information and chapter data.
"""

import json
import re
from typing import Optional
from playwright.sync_api import sync_playwright
from ..utils.retry import retry_with_backoff
from ..utils.logger import get_logger
from ..utils.session import get_session
from ..utils.hash import generate_comix_hash

logger = get_logger(__name__)


class ComixAPI:
    """API wrapper for comix.to"""
    
    BASE_URL = "https://comix.to/api/v2"
    
    @staticmethod
    def extract_manga_code(url: str) -> str:
        """
        Extract manga code from the title URL.
        Example: https://comix.to/title/93q1r-the-summoner -> 93q1r
        """
        parts = url.rstrip("/").split("/")
        last = parts[-1] if parts[-1] else parts[-2]
        code = last.split("-")[0]
        logger.debug(f"Extracted manga code: {code} from URL: {url}")
        return code
    
    @classmethod
    def get_manga_info(cls, manga_code: str) -> Optional[any]:
        """Fetch manga information from DOM using Playwright."""
        from ..core.models import MangaInfo
        url = f"https://comix.to/title/{manga_code}"
        logger.info(f"Fetching manga info using Playwright for {manga_code}...")
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
                )
                page = context.new_page()
                
                # Navigate to the page
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                
                # Wait for the initial-data script tag to be present in the DOM
                page.wait_for_selector('script#initial-data', state="attached", timeout=10000)
                
                # Get initial data contents
                initial_data_str = page.locator('script#initial-data').inner_html()
                json_data = json.loads(initial_data_str)
                
                browser.close()
        except Exception as e:
            logger.error(f"Playwright failed to fetch manga info for {manga_code}: {e}")
            return None

        # Find the manga detail query in the json_data
        manga_detail = None
        queries = json_data.get("queries", {})
        for key, val in queries.items():
            if "manga" in key and "detail" in key and manga_code in key:
                manga_detail = val
                break
                
        if not manga_detail:
            logger.error(f"Could not find manga detail in initial-data for {manga_code}. Keys: {list(queries.keys())}")
            return None
            
        # Get alt titles safely
        alt_titles = manga_detail.get("altTitles", [])
        if not isinstance(alt_titles, list):
            alt_titles = [alt_titles] if alt_titles else []
            
        # Poster URL
        poster = manga_detail.get("poster") or {}
        poster_url = None
        if isinstance(poster, dict):
            poster_url = poster.get("large") or poster.get("medium")
            
        genres = []
        for g in manga_detail.get("genres", []):
            if isinstance(g, dict) and "title" in g:
                genres.append(g["title"])
            elif isinstance(g, str):
                genres.append(g)

        return MangaInfo(
            manga_id=manga_detail.get("id"),
            hash_id=manga_detail.get("hid"),
            title=manga_detail.get("title", "Unknown"),
            alt_titles=alt_titles,
            slug=manga_detail.get("url", "").split("/")[-1] if manga_detail.get("url") else None,
            rank=manga_detail.get("rank"),
            manga_type=manga_detail.get("type"),
            poster_url=poster_url,
            original_language=manga_detail.get("originalLanguage"),
            status=manga_detail.get("status"),
            final_chapter=str(manga_detail.get("finalChapter") or 0),
            latest_chapter=str(manga_detail.get("latestChapter") or 0),
            start_date=manga_detail.get("startDate"),
            end_date=manga_detail.get("endDate"),
            rated_avg=manga_detail.get("ratedAvg"),
            rated_count=manga_detail.get("ratedCount"),
            follows_total=manga_detail.get("followsTotal"),
            is_nsfw=manga_detail.get("contentRating") == "nsfw",
            year=manga_detail.get("year"),
            genres=genres,
            description=manga_detail.get("synopsis", "")
        )
    
    @classmethod
    def get_all_chapters(cls, manga_code: str) -> list[any]:
        """Fetch all chapters for a manga using Playwright DOM scraping."""
        from ..core.models import Chapter
        url = f"https://comix.to/title/{manga_code}"
        logger.info(f"Scraping chapters using Playwright for {manga_code}...")
        
        scrape_js = """() => {
            return Array.from(document.querySelectorAll('.mchap-item')).map(li => {
                const a = li.querySelector('.mchap-row__primary');
                const ch = li.querySelector('.mchap-row__ch');
                const ti = li.querySelector('.mchap-row__title');
                const gp = li.querySelector('.mchap-row__group');
                return {
                    href: a ? a.getAttribute('href') : null,
                    chap_label: ch ? ch.textContent.trim() : null,
                    title: ti ? ti.textContent.trim() : null,
                    group: gp ? (gp.querySelector('span') ? gp.querySelector('span').textContent.trim() : gp.textContent.trim()) : null,
                    group_official: gp ? gp.classList.contains('is-official') : false,
                };
            });
        }"""
        
        chapters: list[Chapter] = []
        seen_ids = set()
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
                )
                page = context.new_page()
                
                prev_first_href = None
                consecutive_dup_pages = 0
                max_pages = 200
                
                for page_n in range(1, max_pages + 1):
                    page_url = f"{url}?page={page_n}"
                    page.goto(page_url, wait_until="domcontentloaded", timeout=30000)
                    
                    if prev_first_href is None:
                        try:
                            page.wait_for_selector(".mchap-row__primary", timeout=10000)
                        except Exception:
                            # If page 1 doesn't render any chapter links, there are none
                            logger.warning(f"No chapters found on page 1 for {manga_code}")
                            break
                    else:
                        # Wait for React to swap the page content
                        import json as std_json
                        js_predicate = (
                            "(() => { const a = document.querySelector('.mchap-row__primary'); "
                            f"return a && a.getAttribute('href') !== {std_json.dumps(prev_first_href)}; }})"
                        )
                        try:
                            page.wait_for_function(js_predicate, timeout=5000)
                        except Exception:
                            # If it didn't change, we likely hit the end or it failed to render new content
                            pass
                            
                    rows = page.evaluate(scrape_js) or []
                    if not rows:
                        break
                        
                    prev_first_href = rows[0].get("href")
                    page_added = 0
                    
                    for row in rows:
                        href = row.get("href")
                        if not href:
                            continue
                        
                        # Parse `/title/{slug}/{chap_id}-chapter-{chap_num}`
                        m = re.match(r".*/title/[^/]+/(\d+)-chapter-(.+)$", href)
                        if not m:
                            continue
                        
                        chap_id_str, chap_num_str = m.group(1), m.group(2)
                        if chap_id_str in seen_ids:
                            continue
                            
                        seen_ids.add(chap_id_str)
                        
                        group = row.get("group")
                        if not group and row.get("group_official"):
                            group = "Official"
                            
                        chapters.append(Chapter(
                            chapter_id=int(chap_id_str),
                            number=chap_num_str,
                            title=row.get("title") or f"Chapter {chap_num_str}",
                            volume=None,
                            votes=0,
                            group_name=group,
                            pages_count=0
                        ))
                        page_added += 1
                        
                    if page_added == 0:
                        consecutive_dup_pages += 1
                        if consecutive_dup_pages >= 2:
                            break
                    else:
                        consecutive_dup_pages = 0
                        
                browser.close()
        except Exception as e:
            logger.error(f"Playwright failed to fetch chapters for {manga_code}: {e}")
            
        # Reverse the list so old chapters (low numbers) are at the beginning
        chapters.reverse()
        logger.info(f"Found {len(chapters)} chapters using Playwright DOM scraping")
        return chapters
    
    @classmethod
    def get_chapter_images(cls, chapter_id: int, manga_slug: str = None, chapter_number: str = None) -> list[str]:
        """Fetch all image URLs / data URLs for a chapter using Playwright."""
        if not manga_slug or not chapter_number:
            manga_slug = "manga"
            chapter_number = "1"
            
        chapter_url = f"https://comix.to/title/{manga_slug}/{chapter_id}-chapter-{chapter_number}"
        logger.info(f"Fetching chapter images via Playwright DOM for {chapter_url}...")
        
        image_urls = []
        page_count = 0
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
                )
                page = context.new_page()
                
                # Preload all the images
                try:
                    page.goto("https://comix.to/", wait_until="domcontentloaded", timeout=15000)
                    page.evaluate("""() => {
                        try {
                            const k = 'reader.default';
                            const cur = JSON.parse(localStorage.getItem(k) || '{}');
                            cur.preload = 'all';
                            localStorage.setItem(k, JSON.stringify(cur));
                        } catch (e) {}
                    }""")
                except Exception as e:
                    logger.warning(f"Failed to set preload settings: {e}")
                
                # Navigate to the chapter page
                page.goto(chapter_url, wait_until="domcontentloaded", timeout=30000)
                
                # Wait for reader page elements to load
                page_count = 0
                for _ in range(60):
                    try:
                        page_count = page.evaluate("() => document.querySelectorAll('.rpage-page').length") or 0
                    except Exception:
                        page_count = 0
                    if page_count > 0:
                        break
                    page.wait_for_timeout(500)
                    
                if page_count == 0:
                    logger.error(f"Chapter page had no pages in DOM: {chapter_url}")
                    browser.close()
                    return []
                    
                # Wait for the first page to begin rendering to avoid cold-start timeouts
                try:
                    page.wait_for_selector('.rpage-page[data-page="1"] canvas, .rpage-page[data-page="1"] img', timeout=15000)
                except Exception:
                    pass
                    
                logger.info(f"Chapter has {page_count} pages. Extracting content...")
                
                # Iterate and capture each page
                for page_num in range(1, page_count + 1):
                    # Scroll page element into view to trigger render/decryption
                    try:
                        page.evaluate(
                            "(n) => { const el = document.querySelector('.rpage-page[data-page=\"' + n + '\"]'); if (el) el.scrollIntoView({behavior: 'instant', block: 'center'}); }",
                            page_num
                        )
                    except Exception:
                        pass
                        
                    # Wait for image element or canvas element to be ready
                    ready = None
                    for _attempt in range(40):
                        try:
                            ready = page.evaluate(
                                """(n) => {
                                    const el = document.querySelector('.rpage-page[data-page="' + n + '"]');
                                    if (!el) return null;
                                    const isLoading = el.classList.contains('is-loading');
                                    const c = el.querySelector('canvas');
                                    if (c && c.width > 0 && c.height > 0 && !isLoading) {
                                        return {type: 'canvas'};
                                    }
                                    const i = el.querySelector('img');
                                    if (i && i.src && i.complete && i.naturalWidth > 0) {
                                        return {type: 'img', src: i.src};
                                    }
                                    return null;
                                }""",
                                page_num
                            )
                        except Exception:
                            ready = None
                        if ready:
                            break
                        page.wait_for_timeout(250)
                        
                    if not ready:
                        logger.error(f"Page {page_num} timed out waiting for render.")
                        continue
                        
                    # Extract the image data or URL from canvas/image (handling blobs via canvas)
                    try:
                        extracted_url = page.evaluate(
                            """(n) => {
                                try {
                                    const el = document.querySelector('.rpage-page[data-page="' + n + '"]');
                                    if (!el) return null;
                                    
                                    const c = el.querySelector('canvas');
                                    if (c && c.width > 0 && c.height > 0) {
                                        return c.toDataURL('image/webp', 0.95);
                                    }
                                    
                                    const i = el.querySelector('img');
                                    if (i && i.src) {
                                        if (i.src.startsWith('blob:')) {
                                            try {
                                                const canvas = document.createElement('canvas');
                                                canvas.width = i.naturalWidth || i.width;
                                                canvas.height = i.naturalHeight || i.height;
                                                const ctx = canvas.getContext('2d');
                                                ctx.drawImage(i, 0, 0);
                                                return canvas.toDataURL('image/webp', 0.95);
                                            } catch (e) {
                                                return null;
                                            }
                                        }
                                        return i.src;
                                    }
                                    return null;
                                } catch (e) {
                                    return null;
                                }
                            }""",
                            page_num
                        )
                    except Exception as e:
                        logger.error(f"Page {page_num} extraction failed: {e}")
                        continue
                        
                    if extracted_url:
                        image_urls.append(extracted_url)
                    else:
                        logger.error(f"Page {page_num} failed to extract valid URL or data.")
                        
                browser.close()
        except Exception as e:
            logger.error(f"Playwright failed to fetch images for chapter {chapter_id}: {e}")
            
        logger.info(f"Retrieved {len(image_urls)} / {page_count} page images.")
        return image_urls
