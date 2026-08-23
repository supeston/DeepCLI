import asyncio
import concurrent.futures
import ctypes
import difflib
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version as package_version
import json
import os
import py_compile
import re
import shutil
import signal
import subprocess
import sys
import textwrap
import unicodedata
from pathlib import Path

import pyperclip
from prompt_toolkit import PromptSession
from prompt_toolkit.document import Document
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.shortcuts import radiolist_dialog
from prompt_toolkit.styles import Style as PTStyle

from rich.align import Align
from rich.console import Console, Group
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from deepx.api.deep_api import DeepAPI
from deepx.tools.dadata_osint import DadataOSINTTool
from deepx.tools.funstat_osint import FunstatOSINTTool

                                                                                
                    
                                                                                

from deepx.core.constants import *
from deepx.core.config import *
from deepx.ui.markup import *
from deepx.ui.terminal import console

class BrowserToolsMixin:
    async def init_browser(self):
        if not self.playwright:
            from playwright.async_api import async_playwright
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=self.browser_headless)
            context_options = dict(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1440, "height": 900},
                accept_downloads=True,
                locale="ru-RU"
            )
            if os.path.exists(self.browser_state_file):
                context_options["storage_state"] = self.browser_state_file
            self.browser_context = await self.browser.new_context(**context_options)
            await self._enable_browser_stealth()
            self.page = await self.browser_context.new_page()
            self._configure_browser_page(self.page)

    async def _enable_browser_stealth(self):
        try:
            installed_version = package_version("playwright-stealth")
            major_version = int(installed_version.split(".", 1)[0])
            if major_version < 2:
                raise RuntimeError(
                    f"установлена устаревшая версия {installed_version}; требуется 2.x"
                )
            from playwright_stealth import Stealth

            await Stealth().apply_stealth_async(self.browser_context)
            self.browser_stealth_status = (
                f"always enabled (playwright-stealth {installed_version})"
            )
        except (ImportError, PackageNotFoundError) as exc:
            self.browser_stealth_status = "unavailable"
            raise RuntimeError(
                "DEEPX запрещено запускать без playwright-stealth 2.x. "
                "Выполните: python -m pip install -U \"playwright-stealth>=2,<3\""
            ) from exc
        except Exception as exc:
            self.browser_stealth_status = f"failed: {type(exc).__name__}: {exc}"
            raise RuntimeError(
                f"DEEPX остановлен: playwright-stealth не удалось включить: {exc}"
            ) from exc

    def _configure_browser_page(self, page):
        page.set_default_timeout(self.browser_timeout)
        page.set_default_navigation_timeout(30000)
        page.on("dialog", lambda dialog: asyncio.create_task(dialog.accept()))

    async def close_browser(self):
        if self.browser_context:
            try:
                await self.browser_context.storage_state(path=self.browser_state_file)
            except Exception:
                pass
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        self.page = None
        self.browser_context = None
        self.browser = None
        self.playwright = None

    async def _browser_locator(self, args: dict):
                                                                             
        if args.get("ref"):
            return self.page.locator(f'[data-deepx-ref="{args["ref"]}"]').first
        if args.get("selector"):
            return self.page.locator(args["selector"]).first
        name = args.get("name") or args.get("target")
        exact = bool(args.get("exact", False))
        if args.get("role") and name:
            return self.page.get_by_role(args["role"], name=name, exact=exact).first
        if args.get("label"):
            return self.page.get_by_label(args["label"], exact=exact).first
        if args.get("placeholder"):
            return self.page.get_by_placeholder(args["placeholder"], exact=exact).first
        if name:
            return self.page.get_by_text(name, exact=exact).first
        raise ValueError("Specify ref, selector, role+name, label, placeholder, or target")

    async def _browser_settle(self, delay: int = 500):
        await self.page.wait_for_timeout(delay)
        try:
            await self.page.wait_for_load_state("domcontentloaded", timeout=3000)
        except Exception:
            pass

    async def browser_snapshot(self, max_elements: int = 120, max_text: int = 12000) -> str:
                                                                              
        state = await self.page.evaluate(
            """
            ({maxElements, maxText}) => {
              document.querySelectorAll("[data-deepx-ref]").forEach(
                el => el.removeAttribute("data-deepx-ref")
              );
              const clean = (value, limit) =>
                String(value || "").replace(/\\s+/g, " ").trim().slice(0, limit);
              const visible = el => {
                const r = el.getBoundingClientRect(), s = getComputedStyle(el);
                return r.width > 0 && r.height > 0 && s.display !== "none" &&
                       s.visibility !== "hidden" && Number(s.opacity || 1) > 0;
              };
              const query = [
                "a[href]", "button", "input", "textarea", "select", "summary",
                "[contenteditable='true']", "[role='button']", "[role='link']",
                "[role='textbox']", "[role='checkbox']", "[role='radio']",
                "[role='combobox']", "[role='menuitem']", "[role='tab']"
              ].join(",");
              const elements = [];
              for (const el of document.querySelectorAll(query)) {
                if (!visible(el) || elements.length >= maxElements) continue;
                const ref = "e" + (elements.length + 1);
                el.dataset.deepxRef = ref;
                const tag = el.tagName.toLowerCase();
                const type = (el.getAttribute("type") || "").toLowerCase();
                let role = el.getAttribute("role");
                if (!role) role =
                  tag === "a" ? "link" :
                  tag === "button" || tag === "summary" ? "button" :
                  tag === "select" ? "combobox" :
                  type === "checkbox" ? "checkbox" :
                  type === "radio" ? "radio" :
                  ["button", "submit", "reset"].includes(type) ? "button" :
                  ["input", "textarea"].includes(tag) || el.isContentEditable ? "textbox" : tag;
                const by = el.getAttribute("aria-labelledby");
                const byText = by ? by.split(/\\s+/).map(
                  id => document.getElementById(id)?.innerText || ""
                ).join(" ") : "";
                const labels = el.labels ? Array.from(el.labels).map(x => x.innerText).join(" ") : "";
                const name = clean(
                  el.getAttribute("aria-label") || byText || labels ||
                  el.getAttribute("placeholder") || el.innerText ||
                  el.getAttribute("value") || el.getAttribute("title"), 180
                );
                const item = {ref, role, name};
                if (tag === "a") item.href = el.href;
                if ("value" in el && ["input", "textarea", "select"].includes(tag))
                  item.value = clean(el.value, 100);
                if ("checked" in el) item.checked = Boolean(el.checked);
                if (el.disabled || el.getAttribute("aria-disabled") === "true")
                  item.disabled = true;
                elements.push(item);
              }
              return {
                url: location.href, title: document.title,
                text: clean(document.body?.innerText, maxText), elements,
                scroll: {
                  y: Math.round(scrollY),
                  maxY: Math.max(0, document.documentElement.scrollHeight - innerHeight)
                }
              };
            }
            """,
            {"maxElements": max_elements, "maxText": max_text}
        )
        state["tabs"] = [
            {"index": i, "active": page == self.page, "url": page.url}
            for i, page in enumerate(self.browser_context.pages)
        ]
        return json.dumps(state, ensure_ascii=False, indent=2)

    async def browser_action(self, action: str, args: dict) -> str:
        await self.init_browser()
        args = args or {}
        raw_action = str(action or args.get("action") or "snapshot").lower().strip().replace("-", "_")

        # Normalize action aliases
        _ACTION_ALIASES = {
            "goto": "navigate",
            "open": "navigate",
            "visit": "navigate",
            "load": "navigate",
            "browse": "navigate",
            "eval": "evaluate",
            "js": "evaluate",
            "execute": "evaluate",
            "run": "evaluate",
            "script": "evaluate",
            "input": "fill",
            "type": "fill",
            "write": "fill",
            "set_text": "fill",
            "press_key": "press",
            "keypress": "press",
            "key": "press",
            "page_source": "extract_html",
            "html": "extract_html",
            "get_html": "extract_html",
            "source": "extract_html",
            "text": "extract_text",
            "get_text": "extract_text",
            "tabs": "list_tabs",
            "get_tabs": "list_tabs",
            "newtab": "new_tab",
            "open_tab": "new_tab",
            "switchtab": "switch_tab",
            "closetab": "close_tab",
            "observe": "snapshot",
            "look": "snapshot",
        }
        action = _ACTION_ALIASES.get(raw_action, raw_action)

        try:
            if action in ("snapshot", "observe"):
                return await self.browser_snapshot(
                    int(args.get("max_elements", 120)), int(args.get("max_text", 12000))
                )
            if action in ("navigate", "open"):
                url = str(args.get("url") or args.get("link") or args.get("target") or args.get("path") or "").strip().strip("'\"`")
                if not url:
                    raise ValueError("url is required")
                if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", url):
                    url = "https://" + url
                await self.page.goto(url, wait_until="domcontentloaded")
            elif action == "click":
                loc = await self._browser_locator(args)
                await loc.scroll_into_view_if_needed()
                old_pages = len(self.browser_context.pages)
                await loc.click()
                await self._browser_settle(800)
                if len(self.browser_context.pages) > old_pages:
                    self.page = self.browser_context.pages[-1]
                    self._configure_browser_page(self.page)
            elif action in ("fill", "type"):
                loc = await self._browser_locator(args)
                value = str(
                    args.get("value")
                    if args.get("value") is not None
                    else args.get("text")
                    if args.get("text") is not None
                    else args.get("content")
                    if args.get("content") is not None
                    else args.get("input", "")
                )
                await loc.scroll_into_view_if_needed()
                if raw_action == "type" and args.get("append"):
                    await loc.type(value, delay=int(args.get("delay", 0)))
                else:
                    await loc.fill(value)
            elif action == "press":
                targeted = any(args.get(k) for k in (
                    "ref", "selector", "role", "name", "label", "placeholder", "target"
                ))
                key = str(args.get("key") or args.get("value") or "Enter")
                if targeted:
                    await (await self._browser_locator(args)).press(key)
                else:
                    await self.page.keyboard.press(key)
            elif action == "select":
                loc = await self._browser_locator(args)
                if args.get("option_label") is not None:
                    await loc.select_option(label=str(args["option_label"]))
                else:
                    await loc.select_option(value=str(args.get("value", "")))
            elif action in ("check", "uncheck", "hover", "focus"):
                loc = await self._browser_locator(args)
                await getattr(loc, action)()
            elif action == "scroll":
                if args.get("ref") or args.get("selector") or args.get("target"):
                    await (await self._browser_locator(args)).scroll_into_view_if_needed()
                else:
                    direction = -1 if args.get("direction") == "up" else 1
                    await self.page.mouse.wheel(0, int(args.get("amount", 700)) * direction)
            elif action == "wait":
                timeout = min(int(args.get("timeout", args.get("delay", args.get("ms", 10000)))), 60000)
                wait_text = args.get("text") or args.get("content")
                if wait_text:
                    await self.page.get_by_text(wait_text, exact=bool(args.get("exact"))).first.wait_for(
                        state=args.get("state", "visible"), timeout=timeout
                    )
                elif args.get("selector"):
                    await self.page.locator(args["selector"]).first.wait_for(
                        state=args.get("state", "visible"), timeout=timeout
                    )
                elif args.get("url"):
                    await self.page.wait_for_url(args["url"], timeout=timeout)
                else:
                    await self.page.wait_for_timeout(timeout)
            elif action in ("back", "forward"):
                await getattr(self.page, "go_" + action)(wait_until="domcontentloaded")
            elif action == "reload":
                await self.page.reload(wait_until="domcontentloaded")
            elif action == "new_tab":
                self.page = await self.browser_context.new_page()
                self._configure_browser_page(self.page)
                tab_url = args.get("url") or args.get("link")
                if tab_url:
                    await self.page.goto(str(tab_url).strip().strip("'\"`"), wait_until="domcontentloaded")
            elif action == "switch_tab":
                self.page = self.browser_context.pages[int(args.get("index", -1))]
                await self.page.bring_to_front()
            elif action == "close_tab":
                if len(self.browser_context.pages) < 2:
                    raise ValueError("Cannot close the only tab")
                await self.page.close()
                self.page = self.browser_context.pages[-1]
            elif action == "list_tabs":
                return json.dumps([
                    {"index": i, "active": p == self.page, "title": await p.title(), "url": p.url}
                    for i, p in enumerate(self.browser_context.pages)
                ], ensure_ascii=False, indent=2)
            elif action == "upload":
                files = args.get("files", args.get("path", args.get("file", [])))
                if isinstance(files, str):
                    files = [files]
                await (await self._browser_locator(args)).set_input_files([
                    os.path.abspath(os.path.join(self.cwd, p)) for p in files
                ])
            elif action == "download":
                async with self.page.expect_download(timeout=30000) as info:
                    await (await self._browser_locator(args)).click()
                download = await info.value
                target = os.path.abspath(os.path.join(
                    self.cwd, args.get("path") or download.suggested_filename
                ))
                os.makedirs(os.path.dirname(target), exist_ok=True)
                await download.save_as(target)
                return f"[Success: Downloaded to {target}]\n" + await self.browser_snapshot()
            elif action == "screenshot":
                target = os.path.abspath(os.path.join(
                    self.cwd, args.get("path", "browser_screenshot.png")
                ))
                os.makedirs(os.path.dirname(target), exist_ok=True)
                await self.page.screenshot(path=target, full_page=bool(args.get("full_page", True)))
                return f"[Success: Screenshot saved to {target}]\n" + await self.browser_snapshot()
            elif action == "extract_text":
                loc = self.page.locator(args.get("selector", "body")).first
                return (await loc.inner_text())[:int(args.get("max_text", 20000))]
            elif action == "extract_html":
                html = await self.page.content() if not args.get("selector") else (
                    await self.page.locator(args["selector"]).first.inner_html()
                )
                return html[:int(args.get("max_text", 30000))]
            elif action == "evaluate":
                script = args.get("script") or args.get("code") or args.get("expression") or args.get("content") or args.get("command") or ""
                result = await self.page.evaluate(script)
                return json.dumps(result, ensure_ascii=False, default=str)[:30000]
            else:
                return f"[Error: Unknown browser action '{action}']"

            await self._browser_settle(int(args.get("settle_ms", 500)))
            return f"[Success: browser {action}]\n" + await self.browser_snapshot()
        except Exception as e:
            try:
                state = await self.browser_snapshot(60, 6000)
            except Exception:
                state = "{}"
            return f"[Error in browser '{action}': {type(e).__name__}: {e}]\nCurrent state:\n{state}"

