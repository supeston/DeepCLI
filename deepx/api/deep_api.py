import asyncio
import os
import re
from importlib.metadata import PackageNotFoundError, version as package_version
from playwright.async_api import async_playwright


COMPLETE_TOOL_CALL_STALL_SECONDS = 4.0
# DeepSeek can reuse an existing message container between agent turns.  In
# that case waiting a full minute for a newly attached response node only
# delays the fallback to the latest message; it does not improve recovery.
RESPONSE_ELEMENT_ATTACH_TIMEOUT_MS = 5000


_THINK_STATUS_RE = re.compile(
    r"^[ \t]*(?:(?:\u0420\u0430\u0437\u043c\u044b\u0448\u043b\u0435\u043d\u0438\u0435|\u0420\u0430\u0437\u043c\u044b\u0448\u043b\u044f\u043b|\u0414\u0443\u043c\u0430\u043b)"
    r"\s+\d+(?:[.,]\d+)?\s+(?:\u0441\u0435\u043a\u0443\u043d\u0434(?:\u0443|\u044b|\u0430)?|\u0441)"
    r"|(?:Thought|Thinking)\s+(?:for\s+)?\d+(?:[.,]\d+)?\s*(?:seconds?|s))\.?[ \t]*(?:\r?\n)?",
    re.IGNORECASE | re.MULTILINE,
)


def _separate_reasoning(think: str, answer: str) -> tuple[str, str]:
    """Keep UI reasoning/status text out of the executable answer channel."""
    think_value = _THINK_STATUS_RE.sub("", str(think or "")).strip()
    answer_value = str(answer or "").strip()
    answer_value = _THINK_STATUS_RE.sub("", answer_value).strip()
    if think_value and answer_value.startswith(think_value):
        answer_value = answer_value[len(think_value):].lstrip()
    return think_value, answer_value


def _has_complete_tool_call(text: str) -> bool:
    """Return True only after a supported tool-call block is closed."""
    value = str(text or "")
    return bool(
        re.search(r"```(?:tool_call|tool_calls|tools|tool|json)?\s*\n?.+?\n?```", value, re.DOTALL)
        or re.search(r"<(?:tool_call|function_call)>\s*.+?\s*</(?:tool_call|function_call)>", value, re.DOTALL | re.IGNORECASE)
        or re.search(r"<tool_calls>\s*.+?\s*</tool_calls>", value, re.DOTALL | re.IGNORECASE)
        or re.search(r"<invoke\b.+?</invoke\s*>", value, re.DOTALL | re.IGNORECASE)
    )


class DeepAPI:
    def __init__(self, state_file: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "core", "state.json"), headless: bool = False):
        self.state_file = state_file
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.stealth_status = "not initialized"

    async def _require_stealth(self):
        try:
            installed_version = package_version("playwright-stealth")
            if int(installed_version.split(".", 1)[0]) < 2:
                raise RuntimeError(
                    f"установлена устаревшая версия {installed_version}; требуется 2.x"
                )
            from playwright_stealth import Stealth

            await Stealth().apply_stealth_async(self.context)
            self.stealth_status = (
                f"always enabled (playwright-stealth {installed_version})"
            )
        except (ImportError, PackageNotFoundError) as exc:
            self.stealth_status = "unavailable"
            raise RuntimeError(
                "DEEPX запрещено запускать без playwright-stealth 2.x. "
                "Выполните: python -m pip install -U \"playwright-stealth>=2,<3\""
            ) from exc
        except Exception as exc:
            self.stealth_status = f"failed: {type(exc).__name__}: {exc}"
            raise RuntimeError(
                f"DEEPX остановлен: playwright-stealth не удалось включить: {exc}"
            ) from exc

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def start(self):
        last_error = None
        for attempt in range(3):
            try:
                await self._start_once()
                return
            except Exception as exc:
                last_error = exc
                message = str(exc).lower()
                recoverable = any(marker in message for marker in (
                    "target page", "context or browser has been closed",
                    "browser has been closed", "connection closed", "page closed"
                ))
                await self.close()
                if not recoverable or attempt == 2:
                    raise
                await asyncio.sleep(0.5 * (attempt + 1))
        raise last_error

    async def _start_once(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=["--disable-blink-features=AutomationControlled"]
        )

        if os.path.exists(self.state_file):
            self.context = await self.browser.new_context(storage_state=self.state_file)
        else:
            self.context = await self.browser.new_context()

        await self._require_stealth()
        self.page = await self.context.new_page()
        await self.page.goto(
            "https://chat.deepseek.com",
            wait_until="domcontentloaded",
            timeout=60000
        )

        if not os.path.exists(self.state_file):
            await self.page.wait_for_selector("textarea, div[contenteditable='true']", timeout=120000)
            await self.context.storage_state(path=self.state_file)

    async def wait_for_login_and_save(self):
                                                                                      
        self.headless = False
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        self.context = await self.browser.new_context()
        await self._require_stealth()
        self.page = await self.context.new_page()

        try:
            await self.page.goto(
                "https://chat.deepseek.com",
                wait_until="domcontentloaded",
                timeout=60000
            )

                                                                              
                                                                    
            while True:
                if self.page.is_closed():
                    raise RuntimeError(
                        "Окно DeepSeek было закрыто до завершения авторизации."
                    )

                composer = self.page.locator(
                    "textarea, div[contenteditable='true']"
                ).first
                try:
                    if await composer.count() and await composer.is_visible():
                        await asyncio.sleep(1.0)
                        state_dir = os.path.dirname(os.path.abspath(self.state_file))
                        os.makedirs(state_dir, exist_ok=True)
                        await self.context.storage_state(path=self.state_file)
                        return
                except Exception as exc:
                    if self.page.is_closed():
                        raise RuntimeError(
                            "Окно DeepSeek было закрыто до завершения авторизации."
                        ) from exc

                await asyncio.sleep(0.75)
        finally:
            await self.close()

    async def close(self):
        context = self.context
        browser = self.browser
        playwright = self.playwright
        self.page = None
        self.context = None
        self.browser = None
        self.playwright = None

        if context and os.path.exists(self.state_file):
            try:
                await context.storage_state(path=self.state_file)
            except Exception:
                pass
        if context:
            try:
                await context.close()
            except Exception:
                pass
        if browser:
            try:
                await browser.close()
            except Exception:
                pass
        if playwright:
            try:
                await playwright.stop()
            except Exception:
                pass

    async def _get_element(self, labels: list):
        if not self.page or self.page.is_closed():
            try:
                await self.start()
            except Exception:
                return None
        if not self.page:
            return None
        for label in labels:
            btn = self.page.get_by_role("button", name=label, exact=True)
            if await btn.count() > 0:
                return btn.first
            txt = self.page.get_by_text(label, exact=True)
            if await txt.count() > 0:
                return txt.first

        for label in labels:
            btn = self.page.locator(f"button:has-text('{label}'), div:has-text('{label}')").first
            if await btn.count() > 0:
                return btn

        return None

    async def is_option_active(self, labels: list) -> bool:
        el = await self._get_element(labels)
        if not el:
            return False

        class_attr = (await el.get_attribute("class")) or ""
        aria_checked = await el.get_attribute("aria-checked")
        aria_pressed = await el.get_attribute("aria-pressed")

        if aria_checked == "true" or aria_pressed == "true":
            return True

        active_indicators = ["active", "checked", "selected", "ds-toggle--active", "ds-toggle-button--selected", "ds-button--primary"]
        if any(indicator in class_attr.lower() for indicator in active_indicators):
            return True

        parent = el.locator("xpath=..")
        if await parent.count() > 0:
            parent_class = (await parent.get_attribute("class")) or ""
            parent_aria_checked = await parent.get_attribute("aria-checked")
            parent_aria_pressed = await parent.get_attribute("aria-pressed")
            if parent_aria_checked == "true" or parent_aria_pressed == "true":
                return True
            if any(indicator in parent_class.lower() for indicator in active_indicators):
                return True

        return False

    async def is_generating(self) -> bool:
        try:
            return await self.page.evaluate("""
                () => {
                    const visible = el => {
                        const r = el.getBoundingClientRect();
                        const s = getComputedStyle(el);
                        return r.width > 0 && r.height > 0 &&
                            s.display !== "none" && s.visibility !== "hidden";
                    };
                    const nodes = document.querySelectorAll(
                        ".ds-icon-stop, [class*='icon-stop'], " +
                        "button, [role='button'], .ds-icon-button"
                    );
                    return Array.from(nodes).some(el => {
                        if (!visible(el)) return false;
                        const semanticMarker = [
                            el.getAttribute("aria-label") || "",
                            el.getAttribute("title") || "",
                            el.getAttribute("data-testid") || ""
                        ].join(" ").toLowerCase();
                        const classMarker = String(el.className || "").toLowerCase();
                        if (
                            /stop|останов|停止|cancel.?generat/.test(semanticMarker)
                            || /(^|\\s|-)icon-stop($|\\s|-)/.test(classMarker)
                            || /(^|\\s)ds-icon-stop($|\\s)/.test(classMarker)
                        ) return true;
                        const stopPath = el.querySelector("svg path");
                        const pathData = stopPath
                            ? (stopPath.getAttribute("d") || "")
                            : "";
                        const isPrimaryCircle = (
                            el.classList.contains("ds-button--primary") &&
                            el.classList.contains("ds-button--filled") &&
                            el.classList.contains("ds-button--circle")
                        );
                        if (!isPrimaryCircle || !pathData.startsWith("M2 4.88")) {
                            return false;
                        }
                        const input = document.querySelector(
                            "textarea, div[contenteditable='true']"
                        );
                        if (!input) return false;
                        const r = el.getBoundingClientRect();
                        const ir = input.getBoundingClientRect();
                        const cx = r.left + r.width / 2;
                        const cy = r.top + r.height / 2;
                        return (
                            cx >= ir.right - 140 &&
                            cx <= ir.right + 100 &&
                            cy >= ir.top - 80 &&
                            cy <= ir.bottom + 100
                        );
                    });
                }
            """)
        except Exception:
            return False

    async def stop_generation(self, timeout: float = 5.0) -> bool:
        if not self.page or self.page.is_closed():
            return False

        selectors = (
            "[role='button'].ds-button--primary.ds-button--filled"
            ".ds-button--circle:has(svg path[d^='M2 4.88'])",
            ".ds-icon-stop",
            "[class*='icon-stop']",
            "button[aria-label*='Stop' i]",
            "button[title*='Stop' i]",
            "button[aria-label*='Остановить' i]",
            "[role='button'][aria-label*='Stop' i]",
            "[role='button'][aria-label*='Остановить' i]",
            "button:has(svg rect)",
            "[role='button']:has(svg rect)",
            ".ds-icon-button:has(svg rect)",
        )
        deadline = asyncio.get_running_loop().time() + timeout
        clicked = False

        while asyncio.get_running_loop().time() < deadline and not clicked:
            for selector in selectors:
                try:
                    candidates = self.page.locator(selector)
                    count = min(await candidates.count(), 8)
                    for index in range(count):
                        candidate = candidates.nth(index)
                        if not await candidate.is_visible():
                            continue
                        target = candidate.locator(
                            "xpath=ancestor-or-self::*[self::button or @role='button'][1]"
                        )
                        if await target.count() == 0:
                            target = candidate
                        await target.click(force=True, timeout=1000)
                        clicked = True
                        break
                except Exception:
                    continue
                if clicked:
                    break
            if not clicked:
                try:
                    candidates = self.page.locator(
                        "button, [role='button'], .ds-icon-button"
                    )
                    count = min(await candidates.count(), 80)
                    best_index = -1
                    best_score = -1
                    for index in range(count):
                        candidate = candidates.nth(index)
                        score = await candidate.evaluate("""
                            el => {
                                const r = el.getBoundingClientRect();
                                const s = getComputedStyle(el);
                                if (
                                    r.width <= 0 || r.height <= 0 ||
                                    s.display === "none" ||
                                    s.visibility === "hidden"
                                ) return -1;
                                const marker = [
                                    el.getAttribute("aria-label") || "",
                                    el.getAttribute("title") || "",
                                    el.getAttribute("data-testid") || "",
                                    String(el.className || "")
                                ].join(" ").toLowerCase();
                                let score = 0;
                                if (/stop|останов|停止|cancel.?generat/.test(marker)) {
                                    score += 1000;
                                }
                                const pathData = (
                                    el.querySelector("svg path")?.getAttribute("d") || ""
                                );
                                if (
                                    el.classList.contains("ds-button--primary") &&
                                    el.classList.contains("ds-button--filled") &&
                                    el.classList.contains("ds-button--circle")
                                ) score += 1000;
                                if (pathData.startsWith("M2 4.88")) score += 2000;
                                if (el.querySelector("svg rect")) score += 500;
                                const input = document.querySelector(
                                    "textarea, div[contenteditable='true']"
                                );
                                if (input) {
                                    const ir = input.getBoundingClientRect();
                                    const cx = r.left + r.width / 2;
                                    const cy = r.top + r.height / 2;
                                    if (
                                        cx >= ir.right - 140 &&
                                        cx <= ir.right + 100 &&
                                        cy >= ir.top - 80 &&
                                        cy <= ir.bottom + 100
                                    ) score += 250;
                                }
                                if (el.querySelector("svg")) score += 25;
                                score += Math.max(0, r.left) / 10000;
                                return score;
                            }
                        """)
                        if score > best_score:
                            best_score = score
                            best_index = index
                    if best_index >= 0 and best_score >= 250:
                        await candidates.nth(best_index).click(
                            force=True,
                            timeout=1500,
                        )
                        clicked = True
                except Exception:
                    pass
            if not clicked:
                try:
                    await self.page.keyboard.press("Escape")
                except Exception:
                    pass
                await asyncio.sleep(0.05)

        if not clicked:
            return not await self.is_generating()

        while asyncio.get_running_loop().time() < deadline:
            if not await self.is_generating():
                return True
            await asyncio.sleep(0.05)
        return not await self.is_generating()

    async def _click_by_labels(self, labels: list):
        el = await self._get_element(labels)
        if el:
            await el.wait_for(state="visible", timeout=5000)
            await el.click()
            await asyncio.sleep(0.5)
            return True
        return False

    async def new_chat(self):
        if not self.page or self.page.is_closed():
            try:
                await self.start()
            except Exception:
                return False
        if not self.page:
            return False
        labels = ["Новый чат", "New chat", "New Chat"]
        for label in labels:
            element = self.page.get_by_text(label, exact=False).first
            if await element.count() > 0 and await element.is_visible():
                await element.click()
                await asyncio.sleep(0.5)
                return True

        await self.page.goto("https://chat.deepseek.com")
        await self.page.wait_for_load_state("networkidle")
        await asyncio.sleep(0.5)
        return True

    async def set_mode(self, mode: str):
        mode_map = {
            "instant": ["Быстрый", "Instant"],
            "expert": ["Эксперт", "Expert"],
            "vision": ["Распознавание", "Vision"]
        }
        key = mode.lower()
        if key in mode_map:
            return await self._click_by_labels(mode_map[key])
        return False

    async def set_search(self, enable: bool):
        labels = ["Умный поиск", "Search"]
        current_state = await self.is_option_active(labels)
        if current_state != enable:
            return await self._click_by_labels(labels)
        return True

    async def set_deepthink(self, enable: bool):
        labels = ["Глубокое мышление", "DeepThink"]
        current_state = await self.is_option_active(labels)
        if current_state != enable:
            return await self._click_by_labels(labels)
        return True

    async def toggle_search(self):
        return await self._click_by_labels(["Умный поиск", "Search"])

    async def toggle_deepthink(self):
        return await self._click_by_labels(["Глубокое мышление", "DeepThink"])

    async def extract_response_data(self, container_locator, is_generating: bool = False):
        try:
            data = await container_locator.evaluate("""
                (el, isGenerating) => {
                    const hasContentAfter = (node) => {
                        let next = node.nextSibling;
                        while (next) {
                            if (next.textContent && next.textContent.trim().length > 0) {
                                return true;
                            }
                            next = next.nextSibling;
                        }
                        return false;
                    };

                    const domToMarkdown = (node) => {
                        if (!node) return "";
                        if (node.nodeType === Node.TEXT_NODE) {
                            return node.nodeValue || "";
                        }
                        if (node.nodeType !== Node.ELEMENT_NODE) return "";

                        const tag = node.tagName.toLowerCase();
                        
                        if (["svg", "button", "script", "style"].includes(tag) || 
                            node.getAttribute("role") === "button" || 
                            node.classList.contains("code-info-button-text") ||
                            node.classList.contains("ds-think-header") ||
                            node.classList.contains("ds-think-title") ||
                            node.classList.contains("ds-icon-think")) {
                            return "";
                        }

                        // KaTeX Display Math
                        if (node.classList.contains("katex-display") || node.classList.contains("ds-markdown-math")) {
                            const ann = node.querySelector("annotation");
                            const tex = ann ? ann.textContent.trim() : node.textContent.trim();
                            return "\\n\\n$$ " + tex + " $$\\n\\n";
                        }

                        // KaTeX Inline Math
                        if (node.classList.contains("katex")) {
                            const ann = node.querySelector("annotation");
                            const tex = ann ? ann.textContent.trim() : node.textContent.trim();
                            return " $ " + tex + " $ ";
                        }

                        // Code Block
                        if (node.classList.contains("md-code-block")) {
                            const pres = Array.from(node.querySelectorAll("pre"));
                            const codePres = pres.length > 0 ? pres : Array.from(node.querySelectorAll("code"));
                            if (codePres.length === 0) return "";
                            
                            const langSpan = node.querySelector(".d813de27") || node.querySelector("[class*='banner']");
                            let lang = "";
                            if (langSpan) {
                                lang = langSpan.textContent.trim().split(/\\s+/)[0];
                                if (["copy", "копировать", "code"].includes(lang.toLowerCase())) lang = "";
                            }
                            const codeText = codePres.map(p => p.textContent).join("\\n");
                            const trimmedCode = codeText.trim();
                            if (!lang && (trimmedCode.startsWith("{") || trimmedCode.startsWith("<tool_call>") || trimmedCode.startsWith("tool:"))) {
                                lang = "tool_call";
                            }
                            
                            const isLastNode = !hasContentAfter(node);
                            const closing = (isLastNode && isGenerating) ? "" : "\\n```\\n\\n";
                            return "\\n\\n```" + lang + "\\n" + codeText + closing;
                        }

                        // Headings
                        if (tag.match(/^h[1-6]$/)) {
                            const level = parseInt(tag.charAt(1));
                            const prefix = "#".repeat(level) + " ";
                            const text = Array.from(node.childNodes).map(c => domToMarkdown(c)).join("").trim();
                            return "\\n\\n" + prefix + text + "\\n\\n";
                        }

                        // Paragraph
                        if (tag === "p") {
                            const text = Array.from(node.childNodes).map(c => domToMarkdown(c)).join("");
                            return "\\n\\n" + text + "\\n\\n";
                        }

                        if (tag === "table") {
                            const rows = Array.from(node.rows || []).map(row =>
                                Array.from(row.cells || []).map(cell => {
                                    const value = Array.from(cell.childNodes)
                                        .map(c => domToMarkdown(c))
                                        .join("")
                                        .replace(/\\s+/g, " ")
                                        .trim()
                                        .replace(/\\|/g, "\\\\|");
                                    return value;
                                })
                            ).filter(row => row.length > 0);
                            if (rows.length === 0) return "";
                            const width = Math.max(...rows.map(row => row.length));
                            const normalized = rows.map(row => [
                                ...row,
                                ...Array(Math.max(0, width - row.length)).fill("")
                            ]);
                            const header = normalized[0];
                            const separator = Array(width).fill("---");
                            const markdownRows = [header, separator, ...normalized.slice(1)]
                                .map(row => "| " + row.join(" | ") + " |");
                            return "\\n\\n" + markdownRows.join("\\n") + "\\n\\n";
                        }

                        const role = (node.getAttribute("role") || "").toLowerCase();
                        const className = typeof node.className === "string"
                            ? node.className.toLowerCase()
                            : "";
                        const isTableRow =
                            tag === "tr" ||
                            role === "row" ||
                            /(?:^|[-_\\s])table[-_\\s]?row(?:$|[-_\\s])/.test(className);
                        if (isTableRow && !node.closest("table")) {
                            const directChildren = Array.from(node.children || []);
                            const cells = directChildren.filter(child => {
                                const childTag = child.tagName.toLowerCase();
                                const childRole = (child.getAttribute("role") || "").toLowerCase();
                                const childClass = typeof child.className === "string"
                                    ? child.className.toLowerCase()
                                    : "";
                                return (
                                    childTag === "th" ||
                                    childTag === "td" ||
                                    childRole === "cell" ||
                                    childRole === "gridcell" ||
                                    childRole === "columnheader" ||
                                    childRole === "rowheader" ||
                                    /(?:^|[-_\\s])table[-_\\s]?(?:cell|header)(?:$|[-_\\s])/.test(childClass)
                                );
                            });
                            if (cells.length >= 2) {
                                const values = cells.map(cell =>
                                    Array.from(cell.childNodes)
                                        .map(c => domToMarkdown(c))
                                        .join("")
                                        .replace(/\\s+/g, " ")
                                        .trim()
                                        .replace(/\\|/g, "\\\\|")
                                );
                                const siblingRows = node.parentElement
                                    ? Array.from(node.parentElement.children).filter(sibling => {
                                        const siblingTag = sibling.tagName.toLowerCase();
                                        const siblingRole = (sibling.getAttribute("role") || "").toLowerCase();
                                        const siblingClass = typeof sibling.className === "string"
                                            ? sibling.className.toLowerCase()
                                            : "";
                                        return (
                                            siblingTag === "tr" ||
                                            siblingRole === "row" ||
                                            /(?:^|[-_\\s])table[-_\\s]?row(?:$|[-_\\s])/.test(siblingClass)
                                        );
                                    })
                                    : [];
                                const isFirstRow = (
                                    siblingRows.length > 1 && siblingRows[0] === node
                                );
                                const isHeader = isFirstRow || cells.every(cell => {
                                    const cellTag = cell.tagName.toLowerCase();
                                    const cellRole = (cell.getAttribute("role") || "").toLowerCase();
                                    return (
                                        cellTag === "th" ||
                                        cellRole === "columnheader" ||
                                        cellRole === "rowheader"
                                    );
                                });
                                const rowText = "| " + values.join(" | ") + " |\\n";
                                const separator = isHeader
                                    ? "| " + values.map(() => "---").join(" | ") + " |\\n"
                                    : "";
                                return rowText + separator;
                            }
                        }

                        // Compact List Items
                        if (tag === "li") {
                            const parent = node.parentElement;
                            const pTag = parent ? parent.tagName.toLowerCase() : "";
                            let prefix = "- ";
                            if (pTag === "ol") {
                                const siblings = Array.from(parent.children).filter(c => c.tagName.toLowerCase() === "li");
                                const idx = siblings.indexOf(node);
                                prefix = (idx >= 0 ? idx + 1 : 1) + ". ";
                            }
                            const text = Array.from(node.childNodes).map(c => domToMarkdown(c)).join("").trim();
                            return "\\n" + prefix + text;
                        }

                        // UL and OL containers
                        if (tag === "ul" || tag === "ol") {
                            return "\\n\\n" + Array.from(node.childNodes).map(c => domToMarkdown(c)).join("") + "\\n\\n";
                        }

                        // Blockquote
                        if (tag === "blockquote") {
                            const text = Array.from(node.childNodes).map(c => domToMarkdown(c)).join("").trim();
                            const lines = text.split("\\n").map(l => "> " + l).join("\\n");
                            return "\\n\\n" + lines + "\\n\\n";
                        }

                        // Inline elements
                        if (tag === "strong" || tag === "b") {
                            const text = Array.from(node.childNodes).map(c => domToMarkdown(c)).join("").trim();
                            return text ? ("**" + text + "**") : "";
                        }
                        if (tag === "em" || tag === "i") {
                            const text = Array.from(node.childNodes).map(c => domToMarkdown(c)).join("").trim();
                            return text ? ("*" + text + "*") : "";
                        }
                        if (tag === "code" && !node.closest(".md-code-block") && !node.closest("pre")) {
                            return "`" + node.textContent + "`";
                        }
                        if (tag === "br") return "\\n";

                        // Container node
                        return Array.from(node.childNodes).map(c => domToMarkdown(c)).join("");
                    };

                    const isThinkElement = (node) => Boolean(
                        node && node.matches && (
                            node.matches(".ds-think-content") ||
                            node.matches("[class*='think']")
                        )
                    );
                    const thinkEl = isThinkElement(el)
                        ? el
                        : (el.querySelector(".ds-think-content") || el.querySelector("[class*='think']"));
                    let thinkText = "";
                    if (thinkEl) {
                        thinkText = domToMarkdown(thinkEl).replace(/\\n{3,}/g, "\\n\\n").trim();
                    }

                    let mainEl = el.querySelector(".ds-assistant-message-main-content");
                    if (!mainEl) {
                        const markdowns = Array.from(el.querySelectorAll(".ds-markdown")).filter(m =>
                            !isThinkElement(m) && !m.closest(".ds-think-content, [class*='think']")
                        );
                        mainEl = markdowns[0] || (thinkEl ? null : el);
                    }

                    if (!mainEl || isThinkElement(mainEl)) {
                        return { think: thinkText, answer: "" };
                    }

                    const cloneMain = mainEl.cloneNode(true);
                    Array.from(cloneMain.querySelectorAll(".ds-think-content, [class*='think']"))
                        .forEach(node => node.remove());

                    Array.from(cloneMain.querySelectorAll("*")).forEach(child => {
                        const childText = (child.textContent || "")
                            .replace(/\\s+/g, " ")
                            .trim();
                        const isInternalSearchNotice =
                            /Чтение ссылок недоступно в Экспертном режиме/i.test(childText) ||
                            /(?:reading|opening) links? (?:is|are) (?:unavailable|not available) in Expert mode/i.test(childText);
                        if (isInternalSearchNotice && child.children.length === 0) {
                            child.remove();
                            return;
                        }

                        if (child.textContent && child.textContent.includes("Глубокое размышление")) {
                            if (!child.querySelector(".ds-markdown") && child.children.length === 0) {
                                child.remove();
                            }
                        }

                        const statusText = Array.from(child.childNodes)
                            .filter(node => node.nodeType === Node.TEXT_NODE)
                            .map(node => node.nodeValue || "")
                            .join(" ")
                            .replace(/\\s+/g, " ")
                            .trim();
                        const russianThinkStatus =
                            /^(?:Думал|Размышлял)\\s+\\d+(?:[.,]\\d+)?\\s+(?:секунд(?:у|ы|а)?|с)\\.?$/;
                        const englishThinkStatus =
                            /^(?:Thought|Thinking)\\s+(?:for\\s+)?\\d+(?:[.,]\\d+)?\\s*(?:seconds?|s)\\.?$/i;
                        if (statusText && statusText.length < 80 &&
                            (russianThinkStatus.test(statusText) || englishThinkStatus.test(statusText))) {
                            child.remove();
                        }
                    });

                    let answerText = domToMarkdown(cloneMain).replace(/\\n{3,}/g, "\\n\\n").trim();
                    answerText = answerText.replace(/^Глубокое размышление\\s*/i, "").trim();
                    answerText = answerText.replace(
                        /^(?:Думал|Размышлял)\\s+\\d+(?:[.,]\\d+)?\\s+(?:секунд(?:у|ы|а)?|с)\\.?\\s*/,
                        ""
                    );
                    answerText = answerText.replace(
                        /^(?:Thought|Thinking)\\s+(?:for\\s+)?\\d+(?:[.,]\\d+)?\\s*(?:seconds?|s)\\.?\\s*/i,
                        ""
                    ).trim();
                    answerText = answerText.replace(
                        /Чтение ссылок недоступно в Экспертном режиме\\.?\\s*(?:Используйте|Переключитесь на)\\s+Быстрый режим\\.?/gi,
                        ""
                    );
                    answerText = answerText.replace(
                        /(?:Reading|Opening) links? (?:is|are) (?:unavailable|not available) in Expert mode\\.?\\s*(?:Use|Switch to) (?:Fast|Instant) mode\\.?/gi,
                        ""
                    ).trim();
                    answerText = answerText.replace(/^Глубокое размышление\\s*/i, "").trim();

                    return {
                        think: thinkText,
                        answer: answerText
                    };
                }
            """, is_generating)
            if not isinstance(data, dict):
                return {"think": "", "answer": ""}
            think, answer = _separate_reasoning(
                data.get("think", ""), data.get("answer", "")
            )
            return {"think": think, "answer": answer}
        except Exception:
            return {"think": "", "answer": ""}

    async def send_message(self, prompt: str, stream: bool = False):
        try:
            await self.page.evaluate("""
                document.querySelectorAll(".ds-markdown, [class*='think']").forEach(el => {
                    el.dataset.oldMark = 'true';
                });
            """)
        except Exception:
            pass

        chat_input = self.page.locator("textarea, div[contenteditable='true']").first
        await chat_input.wait_for(state="visible", timeout=15000)
        await chat_input.fill(prompt)
        await asyncio.sleep(0.15)

        # Click send button if visible or press Enter
        submitted = False
        try:
            send_btn = self.page.locator(
                "div[role='button'].ds-button--primary.ds-button--circle, "
                "button.ds-button--primary.ds-button--circle, "
                "button[aria-label*='Send' i], button[title*='Send' i], "
                "button[aria-label*='Отправить' i], button[title*='Отправить' i], "
                ".ds-icon-send, [class*='icon-send']"
            ).last
            if await send_btn.count() > 0 and await send_btn.is_visible():
                await send_btn.click(timeout=1500)
                submitted = True
        except Exception:
            pass

        if not submitted:
            await chat_input.press("Enter")

        # Wait for generation to start or for a new response element to be attached
        target_container = None
        start_wait = asyncio.get_running_loop().time()
        while asyncio.get_running_loop().time() - start_wait < 35.0:
            if await self.is_generating():
                break

            new_el_check = self.page.locator(
                ".ds-markdown:not([data-old-mark='true']), [class*='think']:not([data-old-mark='true'])"
            ).first
            if await new_el_check.count() > 0:
                break

            # If input still has text after 3 seconds, retry clicking send
            elapsed = asyncio.get_running_loop().time() - start_wait
            if elapsed > 2.5 and int(elapsed * 2) % 4 == 0:
                try:
                    send_btn = self.page.locator(
                        "div[role='button'].ds-button--primary.ds-button--circle, "
                        "button.ds-button--primary.ds-button--circle, "
                        "button[aria-label*='Send' i], button[title*='Send' i], "
                        "button[aria-label*='Отправить' i], button[title*='Отправить' i]"
                    ).last
                    if await send_btn.count() > 0 and await send_btn.is_visible():
                        await send_btn.click(timeout=1000)
                    else:
                        await chat_input.press("Enter")
                except Exception:
                    pass

            await asyncio.sleep(0.1)

        new_el = self.page.locator(".ds-markdown:not([data-old-mark='true']), [class*='think']:not([data-old-mark='true'])").first
        if await new_el.count() > 0:
            target_container = new_el.locator("xpath=ancestor::div[contains(@class, 'message') or contains(@class, 'row') or contains(@class, 'chat') or contains(@class, 'ds-a')][1]")
            if await target_container.count() == 0:
                target_container = new_el.locator("xpath=../..")
        else:
            last_el = self.page.locator(".ds-markdown, [class*='think']").last
            if await last_el.count() > 0:
                target_container = last_el.locator("xpath=ancestor::div[contains(@class, 'message') or contains(@class, 'row') or contains(@class, 'chat') or contains(@class, 'ds-a')][1]")
                if await target_container.count() == 0:
                    target_container = last_el.locator("xpath=../..")

        for _ in range(120):
            if await self.is_generating():
                break
            if target_container and await target_container.count() > 0:
                data = await self.extract_response_data(target_container, is_generating=False)
                if data["think"] or data["answer"]:
                    break
            await asyncio.sleep(0.05)

        if not stream:
            last_text_state = ""
            loop = asyncio.get_running_loop()
            last_change_at = loop.time()
            not_generating_since = None
            while True:
                generating = await self.is_generating()
                data = await self.extract_response_data(target_container, is_generating=generating)
                curr_state = data["think"] + "|||" + data["answer"]
                now = loop.time()
                if curr_state != last_text_state:
                    last_text_state = curr_state
                    last_change_at = now

                # A stale/false-positive Stop control must not prevent the local
                # agent from executing an already complete tool call forever.
                if (
                    generating
                    and _has_complete_tool_call(data["answer"])
                    and now - last_change_at >= COMPLETE_TOOL_CALL_STALL_SECONDS
                ):
                    break

                if generating:
                    not_generating_since = None
                elif not_generating_since is None:
                    not_generating_since = now

                if not generating and not_generating_since is not None:
                    if data["answer"]:
                        grace_seconds = 1.25
                    elif data["think"]:
                        grace_seconds = 8.0
                    else:
                        grace_seconds = 4.0
                    if (
                        now - last_change_at >= grace_seconds
                        and now - not_generating_since >= grace_seconds
                    ):
                        confirm_generating = await self.is_generating()
                        confirm_data = await self.extract_response_data(
                            target_container,
                            is_generating=confirm_generating,
                        )
                        confirm_state = (
                            confirm_data["think"] + "|||" + confirm_data["answer"]
                        )
                        if confirm_generating or confirm_state != curr_state:
                            last_text_state = confirm_state
                            last_change_at = loop.time()
                            not_generating_since = (
                                None if confirm_generating else last_change_at
                            )
                            continue
                        break
                await asyncio.sleep(0.05)

            data = await self.extract_response_data(target_container, is_generating=False)
            # Reasoning is telemetry-only; non-streaming consumers also get
            # the answer channel and can never execute or display reasoning.
            return data["answer"]

        async def generator():
            last_text_state = ""
            loop = asyncio.get_running_loop()
            last_change_at = loop.time()
            not_generating_since = None

            while True:
                generating = await self.is_generating()
                data = await self.extract_response_data(target_container, is_generating=generating)
                think_str = data["think"]
                answer_str = data["answer"]

                curr_state = think_str + "|||" + answer_str
                now = loop.time()
                if curr_state != last_text_state:
                    last_text_state = curr_state
                    last_change_at = now

                complete_tool_call_stalled = (
                    generating
                    and _has_complete_tool_call(answer_str)
                    and now - last_change_at >= COMPLETE_TOOL_CALL_STALL_SECONDS
                )

                if generating:
                    not_generating_since = None
                elif not_generating_since is None:
                    not_generating_since = now

                yield {"think": think_str, "answer": answer_str}

                if complete_tool_call_stalled:
                    break

                if not generating and not_generating_since is not None:
                    if answer_str:
                        grace_seconds = 1.25
                    elif think_str:
                        grace_seconds = 8.0
                    else:
                        grace_seconds = 4.0
                    if (
                        now - last_change_at >= grace_seconds
                        and now - not_generating_since >= grace_seconds
                    ):
                        confirm_generating = await self.is_generating()
                        final_data = await self.extract_response_data(
                            target_container,
                            is_generating=confirm_generating,
                        )
                        yield {
                            "think": final_data["think"],
                            "answer": final_data["answer"],
                        }
                        final_state = (
                            final_data["think"] + "|||" + final_data["answer"]
                        )
                        if confirm_generating or final_state != curr_state:
                            last_text_state = final_state
                            last_change_at = loop.time()
                            not_generating_since = (
                                None if confirm_generating else last_change_at
                            )
                            continue
                        break

                await asyncio.sleep(0.02)

        return generator()
