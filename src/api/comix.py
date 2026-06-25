"""
Comix.to API wrapper for manga information and chapter data.
"""

import json
import re
import asyncio
import threading
from typing import Optional
from ..utils.retry import retry_with_backoff
from ..utils.logger import get_logger
from ..utils.session import get_session
from ..utils.hash import generate_comix_hash
from ..utils.nodriver_compat import load_cdp_page, load_nodriver

logger = get_logger(__name__)

# Global lock to synchronize browser creation and cookie loading/saving across threads
_browser_lock = threading.Lock()


def run_async(coro):
    """Run an async coroutine synchronously."""
    return asyncio.run(coro)


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
    async def _get_manga_info_async(cls, manga_code: str, headless: bool) -> Optional[str]:
        uc = load_nodriver()
        from pathlib import Path
        
        url = f"https://comix.to/title/{manga_code}"
        cookie_file = Path("cf_cookies.dat")
        
        _browser_lock.acquire()
        try:
            browser = await uc.start(
                headless=headless,
                browser_args=[
                    "--start-maximized",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-background-timer-throttling",
                    "--disable-backgrounding-occluded-windows",
                    "--disable-renderer-backgrounding",
                    "--disable-ipc-flooding-protection",
                ]
            )
            
            if cookie_file.exists():
                try:
                    await browser.cookies.load(str(cookie_file))
                    logger.info(f"Loaded cookies from {cookie_file}")
                except Exception as e:
                    logger.warning(f"Failed loading cookies: {e}")
        finally:
            _browser_lock.release()
        
        try:
            page = await browser.get(url)
            await page.sleep(5)
            
            title = await page.evaluate("document.title")
            if "moment" in title.lower():
                logger.warning("Cloudflare challenge detected.")
                if headless:
                    logger.error("Cannot solve Cloudflare challenge in headless mode. Run with headless=False first.")
                else:
                    print("\n[!] Still on the Cloudflare challenge page.")
                    print("[!] Solve the checkbox manually in the browser window now.")
                    input("    Press ENTER *after* the page has fully loaded (title changes)...\n")
                    await page
                    title = await page.evaluate("document.title")
            
            script_content = None
            for _ in range(20):
                script_content = await page.evaluate(
                    "document.getElementById('initial-data') ? document.getElementById('initial-data').innerHTML : null"
                )
                if script_content:
                    break
                await page.sleep(0.5)
                
            if "moment" not in title.lower():
                _browser_lock.acquire()
                try:
                    await browser.cookies.save(str(cookie_file), pattern=".*")
                    logger.info(f"Saved cookies to {cookie_file}")
                except Exception as e:
                    logger.warning(f"Failed saving cookies: {e}")
                finally:
                    _browser_lock.release()
                
            return script_content
            
        finally:
            browser.stop()
            
    @classmethod
    def get_manga_info(cls, manga_code: str, headless: Optional[bool] = None) -> Optional[any]:
        """Fetch manga information from DOM using nodriver."""
        from ..core.models import MangaInfo
        if headless is None:
            from ..utils.config import ConfigManager
            headless = ConfigManager().get("headless", True)
            
        logger.info(f"Fetching manga info using nodriver (headless={headless}) for {manga_code}...")
        
        try:
            initial_data_str = run_async(cls._get_manga_info_async(manga_code, headless))
            if not initial_data_str:
                return None
            json_data = json.loads(initial_data_str)
        except Exception as e:
            logger.error(f"nodriver failed to fetch manga info for {manga_code}: {e}")
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
    async def _get_all_chapters_async(cls, manga_code: str, headless: bool) -> list[dict]:
        uc = load_nodriver()
        from pathlib import Path
        
        url = f"https://comix.to/title/{manga_code}"
        cookie_file = Path("cf_cookies.dat")
        
        _browser_lock.acquire()
        try:
            browser = await uc.start(
                headless=headless,
                browser_args=[
                    "--start-maximized",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-background-timer-throttling",
                    "--disable-backgrounding-occluded-windows",
                    "--disable-renderer-backgrounding",
                    "--disable-ipc-flooding-protection",
                ]
            )
            
            if cookie_file.exists():
                try:
                    await browser.cookies.load(str(cookie_file))
                    logger.info(f"Loaded cookies from {cookie_file}")
                except Exception as e:
                    logger.warning(f"Failed loading cookies: {e}")
        finally:
            _browser_lock.release()
                
        scrape_js = """(() => {
            const rows = Array.from(document.querySelectorAll('.mchap-item')).map(li => {
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
            return JSON.stringify(rows);
        })()"""
        
        all_rows = []
        seen_ids = set()
        
        try:
            page = await browser.get(url)
            await page.sleep(5)
            
            title = await page.evaluate("document.title")
            if "moment" in title.lower():
                logger.warning("Cloudflare challenge detected.")
                if headless:
                    logger.error("Cannot solve Cloudflare challenge in headless mode. Run with headless=False first.")
                else:
                    print("\n[!] Still on the Cloudflare challenge page.")
                    print("[!] Solve the checkbox manually in the browser window now.")
                    input("    Press ENTER *after* the page has fully loaded (title changes)...\n")
                    await page
                    title = await page.evaluate("document.title")
            
            prev_first_href = None
            consecutive_dup_pages = 0
            max_pages = 200
            
            for page_n in range(1, max_pages + 1):
                page_url = f"{url}?page={page_n}"
                if page_n > 1 or page_url != page.url:
                    await page.get(page_url)
                    
                rows = []
                for _ in range(20):
                    rows_str = await page.evaluate(scrape_js)
                    rows = json.loads(rows_str) if rows_str else []
                    if rows:
                        if prev_first_href is None or rows[0].get("href") != prev_first_href:
                            break
                    await page.sleep(0.2)
                
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
                        
                    all_rows.append({
                        "chapter_id": int(chap_id_str),
                        "number": chap_num_str,
                        "title": row.get("title") or f"Chapter {chap_num_str}",
                        "group_name": group,
                    })
                    page_added += 1
                    
                if page_added == 0:
                    consecutive_dup_pages += 1
                    if consecutive_dup_pages >= 2:
                        break
                else:
                    consecutive_dup_pages = 0
            
            if "moment" not in title.lower():
                _browser_lock.acquire()
                try:
                    await browser.cookies.save(str(cookie_file), pattern=".*")
                    logger.info(f"Saved cookies to {cookie_file}")
                except Exception as e:
                    logger.warning(f"Failed saving cookies: {e}")
                finally:
                    _browser_lock.release()
                
            return all_rows
        finally:
            browser.stop()

    @classmethod
    def get_all_chapters(cls, manga_code: str, headless: Optional[bool] = None) -> list[any]:
        """Fetch all chapters for a manga using nodriver DOM scraping."""
        from ..core.models import Chapter
        if headless is None:
            from ..utils.config import ConfigManager
            headless = ConfigManager().get("headless", True)
            
        logger.info(f"Scraping chapters using nodriver (headless={headless}) for {manga_code}...")
        
        chapters: list[Chapter] = []
        try:
            rows = run_async(cls._get_all_chapters_async(manga_code, headless))
            for row in rows:
                chapters.append(Chapter(
                    chapter_id=row["chapter_id"],
                    number=row["number"],
                    title=row["title"],
                    volume=None,
                    votes=0,
                    group_name=row["group_name"],
                    pages_count=0
                ))
        except Exception as e:
            logger.error(f"nodriver failed to fetch chapters for {manga_code}: {e}")
            
        # Reverse the list so old chapters (low numbers) are at the beginning
        chapters.reverse()
        logger.info(f"Found {len(chapters)} chapters using nodriver DOM scraping")
        return chapters
    
    @classmethod
    async def _get_chapter_images_async(
        cls, chapter_id: int, manga_slug: str, chapter_number: str, headless: bool
    ) -> tuple[list[str], int]:
        uc = load_nodriver()
        from pathlib import Path
        
        chapter_url = f"https://comix.to/title/{manga_slug}/{chapter_id}-chapter-{chapter_number}"
        cookie_file = Path("cf_cookies.dat")
        
        _browser_lock.acquire()
        try:
            browser = await uc.start(
                headless=headless,
                browser_args=[
                    "--start-maximized",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-background-timer-throttling",
                    "--disable-backgrounding-occluded-windows",
                    "--disable-renderer-backgrounding",
                    "--disable-ipc-flooding-protection",
                ]
            )
            
            if cookie_file.exists():
                try:
                    await browser.cookies.load(str(cookie_file))
                    logger.info(f"Loaded cookies from {cookie_file}")
                except Exception as e:
                    logger.warning(f"Failed loading cookies: {e}")
        finally:
            _browser_lock.release()
                
        image_urls = []
        page_count = 0
        
        try:
            # Setup init script to backup original toDataURL and set localStorage reader.default preload config
            page = browser.main_tab
            try:
                cdp_page = load_cdp_page()
                await page.send(cdp_page.enable())
                init_js = """
                try {
                    window.__origToDataURL = HTMLCanvasElement.prototype.toDataURL;
                    const k = 'reader.default';
                    const cur = JSON.parse(localStorage.getItem(k) || '{}');
                    cur.preload = 'all';
                    localStorage.setItem(k, JSON.stringify(cur));
                } catch (e) {}
                """
                await page.send(cdp_page.add_script_to_evaluate_on_new_document(source=init_js))
            except Exception as e:
                logger.warning(f"Failed to setup page init script: {e}")
                
            # Now navigate directly to chapter page
            page = await browser.get(chapter_url)
            
            # Wait for reader page elements to load OR Cloudflare challenge
            cloudflare_detected = False
            for _ in range(150):
                try:
                    title = await page.evaluate("document.title") or ""
                    if "moment" in title.lower():
                        cloudflare_detected = True
                        break
                    page_count = await page.evaluate("document.querySelectorAll('.rpage-page').length") or 0
                    if page_count > 0:
                        break
                except Exception:
                    pass
                await page.sleep(0.2)
            
            if cloudflare_detected:
                logger.warning("Cloudflare challenge detected.")
                if headless:
                    logger.error("Cannot solve Cloudflare challenge in headless mode. Run with headless=False first.")
                    return [], 0
                else:
                    print("\n[!] Still on the Cloudflare challenge page.")
                    print("[!] Solve the checkbox manually in the browser window now.")
                    input("    Press ENTER *after* the page has fully loaded (title changes)...\n")
                    await page
                    # Re-verify page count after manual solving
                    for _ in range(150):
                        try:
                            page_count = await page.evaluate("document.querySelectorAll('.rpage-page').length") or 0
                            if page_count > 0:
                                break
                        except Exception:
                            pass
                        await page.sleep(0.2)
                
            if page_count == 0:
                logger.error(f"Chapter page had no pages in DOM: {chapter_url}")
                return [], 0
                
            # Wait for first page to begin rendering
            for _ in range(150):
                try:
                    first_ready = await page.evaluate(
                        "document.querySelector('.rpage-page[data-page=\"1\"] canvas, .rpage-page[data-page=\"1\"] img') ? true : false"
                    )
                    if first_ready:
                        break
                except Exception:
                    pass
                await page.sleep(0.2)
                
            logger.info(f"Chapter has {page_count} pages. Extracting content...")
            
            for page_num in range(1, page_count + 1):
                # Scroll page element into view to trigger render/decryption
                try:
                    await page.evaluate(
                        f"(() => {{ const el = document.querySelector('.rpage-page[data-page=\"{page_num}\"]'); if (el) el.scrollIntoView({{behavior: 'instant', block: 'center'}}); }})()"
                    )
                except Exception:
                    pass
                    
                # Wait for image element or canvas element to be ready
                ready = None
                for _attempt in range(150):
                    try:
                        ready_res = await page.evaluate(
                            f"""(() => {{
                                const el = document.querySelector('.rpage-page[data-page="{page_num}"]');
                                if (!el) return null;
                                const isLoading = el.classList.contains('is-loading');
                                
                                // Check canvas
                                const c = el.querySelector('canvas');
                                if (c && c.width > 10 && c.height > 10) {{
                                    if (isLoading) return null; // Wait if still loading
                                    const toDataURL = window.__origToDataURL || c.toDataURL;
                                    const data = toDataURL.call(c, 'image/webp', 0.95);
                                    if (data.length < 20000) {{
                                        return JSON.stringify({{type: 'skip'}}); // Blank/Ad canvas
                                    }}
                                    return JSON.stringify({{type: 'canvas_data', data: data}});
                                }}
                                
                                // Check image
                                const i = el.querySelector('img');
                                if (i && i.src) {{
                                    if (i.complete) {{
                                        if (i.naturalWidth > 10 && i.naturalHeight > 10) {{
                                            return JSON.stringify({{type: 'img', src: i.src}});
                                        }}
                                        if (i.naturalWidth > 0 && i.naturalWidth <= 10) {{
                                            return JSON.stringify({{type: 'skip'}}); // 1x1 placeholder
                                        }}
                                    }}
                                }}
                                return null;
                            }})()"""
                        )
                        ready = json.loads(ready_res) if ready_res else None
                    except Exception:
                        ready = None
                    if ready:
                        break
                    await page.sleep(0.2)
                    
                if not ready:
                    logger.error(f"Page {page_num} timed out waiting for render.")
                    continue
                    
                if ready.get('type') == 'skip':
                    logger.debug(f"Page {page_num} is an ad/placeholder page. Skipping.")
                    continue
                    
                if ready.get('type') == 'canvas_data':
                    image_urls.append(ready.get('data'))
                    continue
                    
                # Extract image data or URL from image
                try:
                    extracted_url = await page.evaluate(
                        f"""(() => {{
                            try {{
                                const el = document.querySelector('.rpage-page[data-page="{page_num}"]');
                                if (!el) return null;
                                
                                const c = el.querySelector('canvas');
                                if (c && c.width > 0 && c.height > 0) {{
                                    const toDataURL = window.__origToDataURL || c.toDataURL;
                                    return toDataURL.call(c, 'image/webp', 0.95);
                                }}
                                
                                const i = el.querySelector('img');
                                if (i && i.src) {{
                                    if (i.src.startsWith('blob:')) {{
                                        try {{
                                            const canvas = document.createElement('canvas');
                                            canvas.width = i.naturalWidth || i.width;
                                            canvas.height = i.naturalHeight || i.height;
                                            const ctx = canvas.getContext('2d');
                                            ctx.drawImage(i, 0, 0);
                                            const toDataURL = window.__origToDataURL || canvas.toDataURL;
                                            return toDataURL.call(canvas, 'image/webp', 0.95);
                                        }} catch (e) {{
                                            return null;
                                        }}
                                    }}
                                    return i.src;
                                }}
                                return null;
                            }} catch (e) {{
                                return null;
                            }}
                        }})()"""
                    )
                except Exception as e:
                    logger.error(f"Page {page_num} extraction failed: {e}")
                    continue
                    
                if extracted_url:
                    image_urls.append(extracted_url)
                else:
                    logger.error(f"Page {page_num} failed to extract valid URL or data.")
            
            if "moment" not in title.lower():
                _browser_lock.acquire()
                try:
                    await browser.cookies.save(str(cookie_file), pattern=".*")
                    logger.info(f"Saved cookies to {cookie_file}")
                except Exception as e:
                    logger.warning(f"Failed saving cookies: {e}")
                finally:
                    _browser_lock.release()
                
            return image_urls, page_count
        finally:
            browser.stop()

    @classmethod
    def get_chapter_images(cls, chapter_id: int, manga_slug: str = None, chapter_number: str = None, headless: Optional[bool] = None) -> list[str]:
        """Fetch all image URLs / data URLs for a chapter using nodriver."""
        if headless is None:
            from ..utils.config import ConfigManager
            headless = ConfigManager().get("headless", True)
            
        if not manga_slug or not chapter_number:
            manga_slug = "manga"
            chapter_number = "1"
            
        chapter_url = f"https://comix.to/title/{manga_slug}/{chapter_id}-chapter-{chapter_number}"
        logger.info(f"Fetching chapter images via nodriver DOM (headless={headless}) for {chapter_url}...")
        
        image_urls = []
        page_count = 0
        try:
            image_urls, page_count = run_async(cls._get_chapter_images_async(chapter_id, manga_slug, chapter_number, headless))
        except Exception as e:
            logger.error(f"nodriver failed to fetch images for chapter {chapter_id}: {e}")
            
        logger.info(f"Retrieved {len(image_urls)} / {page_count} page images.")
        return image_urls
