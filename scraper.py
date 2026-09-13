import asyncio
import re
import html
from urllib.parse import urljoin, urlparse
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import markdownify

PRIORITY_KEYWORDS = ["contact", "support", "about", "team", "leadership", "company"]
EMAIL_REGEX = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,7}\b'

def clean_html_to_markdown(html_content: str) -> str:
    """Strips boilerplate HTML and converts to markdown to optimize LLM tokens."""
    soup = BeautifulSoup(html_content, "html.parser")
    for tag in soup(["script", "style", "svg", "noscript"]):
        tag.decompose()
    markdown_text = markdownify.markdownify(str(soup), heading_style="ATX")
    return "\n".join([line for line in markdown_text.splitlines() if line.strip()])

def find_emails(text: str) -> list[str]:
    # Unescape entities (e.g., &gt;, \u003e) and remove leading artifacts
    unescaped = html.unescape(text)
    raw_emails = re.findall(EMAIL_REGEX, unescaped)
    valid = set()
    for e in raw_emails:
        cleaned = re.sub(r'^(?:u003e|gt;|lt;)+', '', e.lower()).strip('.-_')
        if not cleaned.endswith(('.png', '.jpg', '.jpeg', '.webp', '.svg')):
            if '@' in cleaned and '.' in cleaned.split('@')[-1]:
                valid.add(cleaned)
    return list(valid)

async def extract_relevant_subpage_urls(page, base_url: str) -> list[str]:
    """Finds links to high-priority pages (like about or contact), including subdomains."""
    hrefs = await page.eval_on_selector_all("a[href]", "elements => elements.map(el => el.getAttribute('href'))")
    
    root_domain = urlparse(base_url).netloc.replace("www.", "")
    discovered = []
    
    for keyword in PRIORITY_KEYWORDS:
        for href in hrefs:
            if not href: continue
            
            full_url = urljoin(base_url, href)
            parsed = urlparse(full_url)
            
            # Allow subdomains (e.g., docs.vapi.ai) by checking if root_domain is in the netloc
            if root_domain in parsed.netloc and not parsed.path.endswith(('.png', '.jpg', '.pdf')):
                if keyword in full_url.lower() and full_url not in discovered:
                    discovered.append(full_url)
                    
    return discovered[:2]

async def scrape_domain(domain: str) -> tuple[str, list[str]]:
    """Crawls the domain, bypassing basic bot protection, handling timeouts gracefully."""
    urls_to_try = [f"https://{domain}", f"https://www.{domain}"]
    aggregated_markdown = []
    discovered_emails = set()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        page = await context.new_page()

        success = False
        actual_url = ""

        # 1. Scrape Homepage
        for url in urls_to_try:
            try:
                print(f"      - Trying {url}...")
                await page.goto(url, timeout=45000, wait_until="domcontentloaded")
                await asyncio.sleep(3)
                home_html = await page.content()
                aggregated_markdown.append(f"# Homepage Content for {domain}\n" + clean_html_to_markdown(home_html))
                discovered_emails.update(find_emails(home_html))
                success = True
                actual_url = page.url 
                break 
            except Exception as e:
                print(f"      [!] Timeout or block on {url}: Retrying...")

        if not success:
            await browser.close()
            return "", list(discovered_emails)

        # 2. Discover relevant subpages
        subpage_urls = await extract_relevant_subpage_urls(page, actual_url)

        # 3. Scrape Subpages
        for sub_url in subpage_urls:
            try:
                print(f"      - Scraping subpage: {sub_url}")
                await page.goto(sub_url, timeout=25000, wait_until="domcontentloaded")
                await asyncio.sleep(2)
                sub_html = await page.content()
                aggregated_markdown.append(f"\n# Subpage ({sub_url})\n" + clean_html_to_markdown(sub_html))
                discovered_emails.update(find_emails(sub_html))
            except Exception as sub_err:
                print(f"      [!] Skipping subpage {sub_url}: {sub_err}")

        await browser.close()
        return "\n\n".join(aggregated_markdown), list(discovered_emails)