import asyncio
import io
import os
import re
import sys
import base64
import urllib.parse
from pathlib import Path

from deepx.core.constants import *
from deepx.core.config import *
from deepx.parser.tool_parser import _as_int
from deepx.ui.markup import *
from deepx.ui.terminal import console

class WebToolsMixin:
    """Enterprise-grade web search, scraping, and document retrieval mixin."""

    def _clean_ddg_link(self, href: str) -> str:
        if not href:
            return ""
        if href.startswith("//"):
            href = "https:" + href
        if "duckduckgo.com/l/" in href:
            target = urllib.parse.parse_qs(urllib.parse.urlparse(href).query).get("uddg", [""])[0]
            if target:
                return urllib.parse.unquote(target)
        return href

    def _unwrap_bing_link(self, url: str) -> str:
        if "bing.com/ck/a" in url:
            try:
                parsed = urllib.parse.urlparse(url)
                params = urllib.parse.parse_qs(parsed.query)
                u_val = params.get("u", [""])[0]
                if u_val.startswith("a1"):
                    raw_b64 = u_val[2:]
                    pad = len(raw_b64) % 4
                    if pad:
                        raw_b64 += "=" * (4 - pad)
                    decoded = base64.urlsafe_b64decode(raw_b64).decode("utf-8", errors="ignore")
                    if decoded.startswith("http"):
                        return decoded
            except Exception:
                pass
        return url

    def _is_ad_link(self, url: str) -> bool:
        lowered = url.lower()
        return (
            "duckduckgo.com/y.js" in lowered
            or "ad_provider=" in lowered
            or "bing.com/aclick" in lowered
            or "doubleclick.net" in lowered
            or "googleadservices" in lowered
        )

    def _search_ddg(self, query: str, max_results: int, region: str, headers: dict) -> list:
        try:
            import requests
            from bs4 import BeautifulSoup
        except ImportError:
            return []

        results = []
        for endpoint in ("https://html.duckduckgo.com/html/", "https://lite.duckduckgo.com/lite/"):
            if len(results) >= max_results:
                break
            try:
                response = requests.post(
                    endpoint,
                    data={"q": query, "kl": region},
                    headers=headers,
                    timeout=15,
                )
                if response.status_code != 200:
                    continue
                soup = BeautifulSoup(response.text, "html.parser")
                blocks = soup.select("div.result, div.web-result")
                if blocks:
                    for block in blocks:
                        link = block.select_one("a.result__a")
                        if not link:
                            continue
                        url = self._clean_ddg_link(link.get("href", ""))
                        if not url or self._is_ad_link(url) or any(r["url"] == url for r in results):
                            continue
                        snippet_el = block.select_one(".result__snippet")
                        results.append({
                            "title": link.get_text(" ", strip=True),
                            "url": url,
                            "snippet": snippet_el.get_text(" ", strip=True) if snippet_el else "",
                        })
                        if len(results) >= max_results:
                            break
                else:
                    for link in soup.select("a.result-link"):
                        url = self._clean_ddg_link(link.get("href", ""))
                        if not url or self._is_ad_link(url) or any(r["url"] == url for r in results):
                            continue
                        results.append({
                            "title": link.get_text(" ", strip=True),
                            "url": url,
                            "snippet": "",
                        })
                        if len(results) >= max_results:
                            break
            except Exception:
                pass
        return results

    def _search_bing(self, query: str, max_results: int, headers: dict) -> list:
        try:
            import requests
            from bs4 import BeautifulSoup
        except ImportError:
            return []

        results = []
        try:
            url = f"https://www.bing.com/search?q={urllib.parse.quote(query)}"
            resp = requests.get(url, headers=headers, timeout=12)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                for item in soup.select("li.b_algo"):
                    h2 = item.select_one("h2 a")
                    if not h2:
                        continue
                    raw_href = h2.get("href", "")
                    clean_href = self._unwrap_bing_link(raw_href)
                    if not clean_href or not clean_href.startswith("http") or self._is_ad_link(clean_href):
                        continue
                    if any(r["url"] == clean_href for r in results):
                        continue
                    title = h2.get_text(" ", strip=True)
                    snippet_el = item.select_one(".b_caption p, .b_algoSlug, p")
                    snippet = snippet_el.get_text(" ", strip=True) if snippet_el else ""
                    results.append({
                        "title": title,
                        "url": clean_href,
                        "snippet": snippet,
                    })
                    if len(results) >= max_results:
                        break
        except Exception:
            pass
        return results

    def _search_wikipedia(self, query: str, max_results: int) -> list:
        try:
            import requests
            from bs4 import BeautifulSoup
        except ImportError:
            return []

        wiki_headers = {
            "User-Agent": "DeepX-ResearchBot/1.0 (https://deepx.agent; contact@deepx.local) python-requests/2.34",
            "Accept": "application/json",
        }

        results = []
        for lang in ("ru", "en"):
            try:
                url = f"https://{lang}.wikipedia.org/w/api.php"
                params = {
                    "action": "query",
                    "list": "search",
                    "srsearch": query,
                    "format": "json",
                    "srlimit": max_results,
                }
                resp = requests.get(url, params=params, headers=wiki_headers, timeout=10)
                if resp.status_code == 200:
                    items = resp.json().get("query", {}).get("search", [])
                    for item in items:
                        title = item.get("title", "")
                        page_url = f"https://{lang}.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"
                        snippet = BeautifulSoup(item.get("snippet", ""), "html.parser").get_text(" ", strip=True)
                        results.append({
                            "title": f"[Wikipedia-{lang.upper()}] {title}",
                            "url": page_url,
                            "snippet": snippet,
                        })
                        if len(results) >= max_results:
                            break
                if results:
                    break
            except Exception:
                pass
        return results

    def web_search(self, query: str, max_results: int = 10, site: str = "", region: str = "wt-wt") -> str:
        """Search the web with multi-engine cascading fallback."""
        if not query or not str(query).strip():
            return "[Error: web_search requires a 'query' argument]"

        query = str(query).strip()
        if site:
            query = f"site:{site} {query}"

        max_results = max(1, min(_as_int(max_results, 10), 25))

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept-Language": "ru,en-US;q=0.9,en;q=0.8",
        }

        # 1. Primary: DuckDuckGo
        results = self._search_ddg(query, max_results, region, headers)
        source_engine = "DuckDuckGo"

        # 2. Fallback 1: Bing
        if not results:
            results = self._search_bing(query, max_results, headers)
            if results:
                source_engine = "Bing"

        # 3. Fallback 2: Wikipedia (if not domain-restricted)
        if not results and not site:
            results = self._search_wikipedia(query, max_results)
            if results:
                source_engine = "Wikipedia"

        if not results:
            return f"[web_search '{query}': no results found across search engines]"

        lines = [f"--- Search results for '{query}' ({len(results)} found via {source_engine}) ---"]
        for i, item in enumerate(results, 1):
            lines.append(f"{i}. {item['title']}\n   {item['url']}")
            if item["snippet"]:
                lines.append(f"   {item['snippet'][:400]}")
        return "\n".join(lines)

    def _convert_tables_to_markdown(self, soup):
        """Convert HTML <table> elements into formatted Markdown tables."""
        for table in soup.find_all("table"):
            rows = []
            for tr in table.find_all("tr"):
                cells = []
                for cell in tr.find_all(["th", "td"]):
                    c_text = re.sub(r"\s+", " ", cell.get_text(" ", strip=True)).replace("|", "\\|")
                    cells.append(c_text)
                if any(cells):
                    rows.append(cells)
            if not rows:
                table.decompose()
                continue
            max_cols = max(len(r) for r in rows)
            if max_cols == 0:
                table.decompose()
                continue
            for r in rows:
                while len(r) < max_cols:
                    r.append("")
            md_lines = [
                "| " + " | ".join(rows[0]) + " |",
                "| " + " | ".join(["---"] * max_cols) + " |",
            ]
            for r in rows[1:]:
                md_lines.append("| " + " | ".join(r) + " |")
            md_str = "\n\n" + "\n".join(md_lines) + "\n\n"
            table.replace_with(soup.new_string(md_str))

    def _extract_pdf_text(self, pdf_bytes: bytes, max_chars: int) -> tuple[str, int]:
        """Extract text from PDF byte content page by page."""
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
            num_pages = len(reader.pages)
            pages_text = []
            total_chars = 0
            for page_idx, page in enumerate(reader.pages, 1):
                page_str = page.extract_text() or ""
                if page_str.strip():
                    pages_text.append(f"--- [Page {page_idx}/{num_pages}] ---\n{page_str.strip()}")
                    total_chars += len(page_str)
                if total_chars >= max_chars:
                    break
            return "\n\n".join(pages_text), num_pages
        except Exception as e:
            return f"[Error parsing PDF content: {e}]", 0

    def fetch_url(self, url: str, max_chars: int = 6000) -> str:
        """Fetch webpage, JSON or PDF document and return clean structured text."""
        if not url:
            return "[Error: fetch_url requires a 'url' argument]"
        if not str(url).startswith(("http://", "https://")):
            url = "https://" + str(url).lstrip("/")

        max_chars = max(500, min(_as_int(max_chars, 6000), 25000))
        try:
            import requests
            from bs4 import BeautifulSoup
        except ImportError as e:
            return f"[Error: fetch_url requires requests and beautifulsoup4 ({e})]"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept-Language": "ru,en-US;q=0.9,en;q=0.8",
        }

        try:
            response = requests.get(url, headers=headers, timeout=25)
            status = response.status_code
            content_type = response.headers.get("Content-Type", "").lower()
            clean_url_path = url.split("?")[0].lower()

            if status != 200 and status != 304:
                return f"[fetch_url {url}: HTTP {status} returned by server]"

            # Check if PDF
            is_pdf = (
                "application/pdf" in content_type
                or clean_url_path.endswith(".pdf")
                or response.content.startswith(b"%PDF")
            )
            if is_pdf:
                text, pages = self._extract_pdf_text(response.content, max_chars)
                truncated = ""
                if len(text) > max_chars:
                    truncated = f"\n[Truncated: {len(text)} chars total, shown {max_chars}]"
                    text = text[:max_chars]
                return f"--- {url} (HTTP {status}, PDF Document: {pages} pages) ---\n\n{text}{truncated}"

            if (
                "html" not in content_type
                and "xml" not in content_type
                and "text" not in content_type
                and "json" not in content_type
            ):
                return f"[fetch_url {url}: HTTP {status}, non-text content ({content_type})]"

            if "json" in content_type:
                text = response.text
                truncated = ""
                if len(text) > max_chars:
                    truncated = f"\n[Truncated: {len(text)} chars total, shown {max_chars}]"
                    text = text[:max_chars]
                return f"--- {url} (HTTP {status}, JSON) ---\n\n{text}{truncated}"

            soup = BeautifulSoup(response.text, "html.parser")
            for tag in soup(["script", "style", "noscript", "svg", "iframe"]):
                tag.decompose()

            # Convert tables into structured Markdown tables
            self._convert_tables_to_markdown(soup)

            title = soup.title.get_text(strip=True) if soup.title else ""
            text = re.sub(r"\n{3,}", "\n\n", soup.get_text("\n", strip=True))

            truncated = ""
            if len(text) > max_chars:
                truncated = f"\n[Truncated: {len(text)} chars total, shown {max_chars}]"
                text = text[:max_chars]
            return f"--- {url} (HTTP {status}) ---\nTitle: {title}\n\n{text}{truncated}"
        except Exception as e:
            return f"[Error fetching '{url}': {e}]"
