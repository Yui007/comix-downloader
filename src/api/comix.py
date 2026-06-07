"""
Comix.to API wrapper for manga information and chapter data using Playwright.
"""

import json
import time
from typing import Optional
from playwright.sync_api import sync_playwright

from ..core.models import MangaInfo, Chapter
from ..utils.retry import retry_with_backoff
from ..utils.logger import get_logger

logger = get_logger(__name__)

class ComixAPI:
    """API wrapper for comix.to using Playwright to intercept decrypted JSON"""
    
    BASE_URL = "https://comix.to"
    
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
    @retry_with_backoff()
    def get_manga_info(cls, manga_code: str) -> Optional[MangaInfo]:
        """Fetch manga information from #initial-data on the page."""
        url = f"{cls.BASE_URL}/title/{manga_code}"
        logger.debug(f"Fetching manga info from: {url}")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
            
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                
                # Extract initial data
                initial_data_str = page.evaluate('document.getElementById("initial-data")?.textContent')
                if not initial_data_str:
                    logger.error("Could not find initial-data in the page.")
                    return None
                    
                json_data = json.loads(initial_data_str)
                queries = json_data.get("queries", {})
                
                manga_data = None
                for k, v in queries.items():
                    if "manga" in k and "detail" in k and manga_code in k:
                        manga_data = v
                        break
                        
                if not manga_data:
                    logger.error("Could not find manga details in queries.")
                    return None
                    
                url_path = manga_data.get("url", "")
                slug = manga_data.get("slug") or url_path.split("/")[-1] if "/" in url_path else None
                
                return MangaInfo(
                    manga_id=manga_data.get("id"),
                    hash_id=manga_data.get("hid"),
                    title=manga_data.get("title", ""),
                    alt_titles=manga_data.get("altTitles", []),
                    description=manga_data.get("synopsis", ""),
                    slug=slug,
                    manga_type=manga_data.get("type"),
                    poster_url=manga_data.get("poster"),
                    original_language=manga_data.get("originalLanguage"),
                    status=manga_data.get("status"),
                    final_chapter=manga_data.get("finalChapter"),
                    latest_chapter=manga_data.get("latestChapter"),
                    start_date=manga_data.get("startDate"),
                    end_date=manga_data.get("endDate"),
                    rated_avg=manga_data.get("ratedAvg"),
                    rated_count=manga_data.get("ratedCount"),
                    follows_total=manga_data.get("followsTotal"),
                    is_nsfw=manga_data.get("contentRating") == "pornographic",
                    year=manga_data.get("year"),
                    genres=[g.get("name") for g in manga_data.get("genres", [])] if manga_data.get("genres") else [],
                    rank=manga_data.get("rank")
                )
            except Exception as e:
                logger.error(f"Failed to fetch manga info: {e}")
                return None
            finally:
                browser.close()

    @classmethod
    def get_all_chapters(cls, manga_code: str) -> list[Chapter]:
        """Fetch all chapters using Playwright JSON.parse interception on the reader page."""
        url = f"{cls.BASE_URL}/title/{manga_code}"
        logger.debug(f"Fetching chapters for: {manga_code}")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
            
            page.add_init_script("""
                window.interceptedChapters = [];
                const origParse = JSON.parse;
                JSON.parse = (t, r) => {
                    const parsed = origParse(t, r);
                    if (parsed && parsed.result && parsed.result.items && parsed.result.items.length > 0) {
                        if (parsed.result.items[0].number !== undefined) {
                            window.interceptedChapters = window.interceptedChapters.concat(parsed.result.items);
                        }
                    }
                    return parsed;
                };
            """)
            
            try:
                # 1. Go to manga page to get at least one chapter ID
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                
                chapters_data = None
                chapter_url = None
                for _ in range(40):
                    chapters_data = page.evaluate("window.interceptedChapters")
                    if chapters_data:
                        # Extract firstChapterUrl from initial-data
                        initial_data_str = page.evaluate('document.getElementById("initial-data")?.textContent')
                        if initial_data_str:
                            import json
                            try:
                                json_data = json.loads(initial_data_str)
                                queries = json_data.get("queries", {})
                                for k, v in queries.items():
                                    if "manga" in k and "detail" in k and manga_code in k:
                                        first_chapter_url = v.get("firstChapterUrl")
                                        if first_chapter_url:
                                            chapter_url = f"{cls.BASE_URL}{first_chapter_url}"
                                        break
                            except:
                                pass
                        break
                    time.sleep(0.5)
                
                if not chapters_data:
                    logger.error("Could not fetch initial chapter list.")
                    return []
                
                # Fallback to constructing URL if firstChapterUrl is not found
                if not chapter_url:
                    first_chap = chapters_data[-1] if chapters_data else {}
                    chap_id = first_chap.get("id", 0)
                    chap_num = first_chap.get("number", 1)
                    num_str = str(int(chap_num)) if chap_num == int(chap_num) else str(chap_num)
                    chapter_url = f"{cls.BASE_URL}/title/{manga_code}/{chap_id}-chapter-{num_str}"
                
                logger.debug(f"Navigating to chapter page to fetch full list: {chapter_url}")
                
                # 3. Navigate to chapter reader page to trigger full list fetch
                page.goto(chapter_url, wait_until="domcontentloaded", timeout=30000)
                
                full_chapters_data = None
                for _ in range(40):
                    full_chapters_data = page.evaluate("window.interceptedChapters")
                    if full_chapters_data and len(full_chapters_data) > len(chapters_data):
                        break
                    time.sleep(0.5)
                    
                if not full_chapters_data:
                    full_chapters_data = page.evaluate("window.interceptedChapters")
                    
                if not full_chapters_data:
                    full_chapters_data = chapters_data
                    
                # Deduplicate chapters
                seen_numbers = set()
                chapters = []
                for chap in full_chapters_data:
                    chap_num_val = chap.get("number")
                    if chap_num_val in seen_numbers:
                        continue
                    seen_numbers.add(chap_num_val)
                    
                    groups = chap.get("groups", [])
                    group_name = groups[0].get("name") if groups else None
                    
                    chapters.append(Chapter(
                        chapter_id=chap.get("id", 0),
                        number=chap.get("number"),
                        title=chap.get("name") or chap.get("title"),
                        volume=chap.get("volume"),
                        votes=chap.get("votes"),
                        group_name=group_name,
                        pages_count=chap.get("pages_count", 0)
                    ))
                    
                # Reverse to sort by oldest first
                chapters.reverse()
                logger.info(f"Found {len(chapters)} chapters")
                return chapters
            except Exception as e:
                logger.error(f"Failed to fetch chapters: {e}")
                return []
            finally:
                browser.close()

    @classmethod
    @retry_with_backoff()
    def get_chapter_images(cls, manga_hid: str, chapter_id: int, chapter_number: float) -> list[str]:
        """Fetch all image URLs for a chapter using Playwright JSON.parse interception."""
        # Ensure chapter number is formatted correctly (e.g., "0" or "73" or "72.5")
        num_str = str(int(chapter_number)) if chapter_number == int(chapter_number) else str(chapter_number)
        url = f"{cls.BASE_URL}/title/{manga_hid}/{chapter_id}-chapter-{num_str}"
        logger.debug(f"Fetching images from chapter URL: {url}")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
            
            page.add_init_script("""
                window.interceptedImages = null;
                const origParse = JSON.parse;
                JSON.parse = (t, r) => {
                    const parsed = origParse(t, r);
                    if (parsed && parsed.result && parsed.result.pages && parsed.result.pages.items) {
                        window.interceptedImages = parsed.result.pages.items.map(item => item.url);
                    }
                    return parsed;
                };
            """)
            
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                
                # Wait for images to be intercepted
                for _ in range(40): # wait up to 20 seconds
                    images = page.evaluate("window.interceptedImages")
                    if images:
                        break
                    time.sleep(0.5)
                    
                images = page.evaluate("window.interceptedImages") or []
                logger.debug(f"Found {len(images)} images")
                return images
            except Exception as e:
                logger.error(f"Failed to fetch chapter images: {e}")
                return []
            finally:
                browser.close()
