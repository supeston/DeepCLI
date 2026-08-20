import asyncio
import io
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from winsdk.windows.applicationmodel.datatransfer import (
        Clipboard,
        ClipboardHistoryItem,
        DataPackage,
        StandardDataFormats,
    )
    from winsdk.windows.storage.streams import DataReader
    WINSDK_AVAILABLE = True
except ImportError:
    WINSDK_AVAILABLE = False

try:
    from PIL import Image, ImageGrab
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False

try:
    import win32clipboard
    import win32con
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False


def _detect_text_type(text: str) -> str:
    """Classify text content in clipboard (code/text, url, json, file_path, text)."""
    stripped = text.strip()
    if not stripped:
        return "empty"

    if re.match(r"^https?://[^\s/$.?#].[^\s]*$", stripped, re.IGNORECASE):
        return "url"

    if (
        (re.match(r"^[a-zA-Z]:\\", stripped) or stripped.startswith("/"))
        and "\n" not in stripped
        and len(stripped) < 300
    ):
        return "file_path"

    if (stripped.startswith("{") and stripped.endswith("}")) or (
        stripped.startswith("[") and stripped.endswith("]")
    ):
        try:
            json.loads(stripped)
            return "json"
        except Exception:
            pass

    code_indicators = [
        r"\bdef\s+\w+\s*\(",
        r"\bclass\s+\w+",
        r"\bimport\s+[\w.]+",
        r"\bfrom\s+[\w.]+\s+import\b",
        r"\bfunction\s*\w*\s*\(",
        r"\bconst\s+\w+\s*=",
        r"\blet\s+\w+\s*=",
        r"\bvar\s+\w+\s*=",
        r"\bSELECT\s+.+\s+FROM\b",
        r"\bpublic\s+(?:class|static|void|int|string)\b",
        r"<\?php",
        r"<!DOCTYPE\s+html",
        r"<html[\s>]",
        r"```",
        r"\bconsole\.log\(",
        r"\breturn\s+",
    ]
    for pattern in code_indicators:
        if re.search(pattern, stripped, re.IGNORECASE):
            return "code/text"

    return "text"


class ClipboardMixin:
    """Windows Clipboard History tool using WinRT (winsdk) with fallback support."""

    async def _extract_winrt_bitmap(self, data_package_view, save_path: str) -> Optional[Dict[str, Any]]:
        """Extract bitmap from WinRT DataPackageView and save to disk via Pillow."""
        if not WINSDK_AVAILABLE or not PIL_AVAILABLE:
            return None
        try:
            stream_ref = await data_package_view.get_bitmap_async()
            if not stream_ref:
                return None
            stream = await stream_ref.open_read_async()
            size = stream.size
            if size == 0:
                return None
            reader = DataReader(stream)
            await reader.load_async(size)
            bytes_data = bytearray(size)
            reader.read_bytes(bytes_data)

            img = Image.open(io.BytesIO(bytes_data))
            os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
            img.save(save_path, format="PNG")

            file_size = os.path.getsize(save_path)
            return {
                "path": os.path.abspath(save_path),
                "width": img.size[0],
                "height": img.size[1],
                "format": "PNG",
                "mode": img.mode,
                "size_bytes": file_size,
            }
        except Exception:
            return None

    async def get_clipboard_history(self, limit: int = 10) -> str:
        """
        Get recent items from Windows Clipboard History (Win + V).
        Returns a structured JSON list of history entries.
        """
        limit_val = max(1, min(int(limit or 10), 30))
        cache_dir = os.path.abspath(os.path.join(self.cwd, ".deepx", "cache"))
        os.makedirs(cache_dir, exist_ok=True)

        if not WINSDK_AVAILABLE:
            # Fallback for non-WinSDK environments: return current active item
            active_text = ""
            if PYPERCLIP_AVAILABLE:
                try:
                    active_text = pyperclip.paste()
                except Exception:
                    pass
            if active_text:
                entry = {
                    "index": 0,
                    "id": "current_active",
                    "type": _detect_text_type(active_text),
                    "preview": active_text[:120] + ("..." if len(active_text) > 120 else ""),
                    "length": len(active_text),
                }
                return json.dumps([entry], ensure_ascii=False, indent=2)
            return "[]"

        try:
            if not Clipboard.is_history_enabled():
                # History disabled in Windows Settings - return current active item
                content = Clipboard.get_content()
                if content and content.contains(StandardDataFormats.text):
                    text = await content.get_text_async()
                    entry = {
                        "index": 0,
                        "id": "current_active",
                        "type": _detect_text_type(text),
                        "preview": text[:120] + ("..." if len(text) > 120 else ""),
                        "length": len(text),
                        "note": "Windows Clipboard History is disabled in Windows Settings; showing active item only.",
                    }
                    return json.dumps([entry], ensure_ascii=False, indent=2)
                return "[Windows Clipboard History is disabled in Windows Settings, and current clipboard is empty]"

            result = await Clipboard.get_history_items_async()
            if not result or not result.items:
                return "[]"

            items_list = []
            for idx, item in enumerate(result.items[:limit_val]):
                content = item.content
                ts_str = str(item.timestamp) if item.timestamp else ""
                entry = {
                    "index": idx,
                    "id": str(item.id),
                    "timestamp": ts_str,
                }

                if content.contains(StandardDataFormats.text):
                    try:
                        text = await content.get_text_async()
                        entry["type"] = _detect_text_type(text)
                        entry["preview"] = text[:120].replace("\r\n", " ").replace("\n", " ") + (
                            "..." if len(text) > 120 else ""
                        )
                        entry["length"] = len(text)
                    except Exception:
                        entry["type"] = "text"
                        entry["preview"] = "[Unable to read text stream]"
                        entry["length"] = 0

                elif content.contains(StandardDataFormats.bitmap):
                    entry["type"] = "image"
                    save_path = os.path.join(cache_dir, f"clip_history_{idx}.png")
                    img_info = await self._extract_winrt_bitmap(content, save_path)
                    if img_info:
                        entry["preview"] = f"[Image: {img_info['width']}x{img_info['height']} PNG]"
                        entry["cached_path"] = img_info["path"]
                    else:
                        entry["preview"] = "[Image Data]"

                elif content.contains(StandardDataFormats.storage_items):
                    try:
                        storage_items = await content.get_storage_items_async()
                        paths = [item.path for item in storage_items if hasattr(item, "path")]
                        entry["type"] = "files"
                        entry["preview"] = f"[{len(paths)} file(s): {', '.join(os.path.basename(p) for p in paths[:3])}]"
                        entry["file_paths"] = paths
                    except Exception:
                        entry["type"] = "files"
                        entry["preview"] = "[Copied files]"

                else:
                    entry["type"] = "unknown"
                    entry["preview"] = "[Unsupported data format]"

                items_list.append(entry)

            return json.dumps(items_list, ensure_ascii=False, indent=2)
        except Exception as e:
            return f"[Error fetching Windows clipboard history: {e}]"

    async def get_clipboard_item(
        self, index: Optional[int] = None, item_id: Optional[str] = None
    ) -> str:
        """
        Fetch full content of a specific history item by index (0, 1, 2...) or item_id GUID.
        """
        if index is None and not item_id:
            return "[Error: get_clipboard_item requires an 'index' (e.g. 0, 1) or 'item_id' argument]"

        cache_dir = os.path.abspath(os.path.join(self.cwd, ".deepx", "cache"))
        os.makedirs(cache_dir, exist_ok=True)

        if not WINSDK_AVAILABLE:
            return await asyncio.to_thread(self.read_clipboard)

        try:
            if not Clipboard.is_history_enabled():
                # Only current item
                content = Clipboard.get_content()
                if content and content.contains(StandardDataFormats.text):
                    text = await content.get_text_async()
                    return f"--- [Clipboard Active Item (Index 0)] ---\n{text}"
                return "[Windows Clipboard History is disabled and no text in clipboard]"

            result = await Clipboard.get_history_items_async()
            if not result or not result.items:
                return "[Clipboard History is empty]"

            target_item = None
            target_idx = 0
            if item_id:
                for idx, item in enumerate(result.items):
                    if str(item.id).strip("{}").lower() == str(item_id).strip("{}").lower():
                        target_item = item
                        target_idx = idx
                        break
            elif index is not None:
                try:
                    idx_int = int(index)
                    if 0 <= idx_int < len(result.items):
                        target_item = result.items[idx_int]
                        target_idx = idx_int
                except (ValueError, TypeError):
                    pass

            if not target_item:
                return f"[Error: History item with index={index} / item_id='{item_id}' not found. Total items: {len(result.items)}]"

            content = target_item.content
            ts = str(target_item.timestamp) if target_item.timestamp else ""

            if content.contains(StandardDataFormats.text):
                text = await content.get_text_async()
                type_hint = _detect_text_type(text)
                return (
                    f"--- [Clipboard Item #{target_idx} (Type: {type_hint}, Timestamp: {ts}, Length: {len(text):,} chars)] ---\n"
                    f"{text}"
                )

            elif content.contains(StandardDataFormats.bitmap):
                timestamp_safe = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_path = os.path.join(cache_dir, f"clip_item_{target_idx}_{timestamp_safe}.png")
                img_info = await self._extract_winrt_bitmap(content, save_path)
                if img_info:
                    return (
                        f"[Clipboard Item #{target_idx}: Image / Screenshot Extracted]\n"
                        f"- Saved Path: {img_info['path']}\n"
                        f"- Resolution: {img_info['width']} x {img_info['height']} pixels\n"
                        f"- Color Mode: {img_info['mode']}\n"
                        f"- File Size: {img_info['size_bytes']:,} bytes ({img_info['size_bytes'] / 1024.0:.1f} KB)\n"
                        f"- Timestamp: {ts}\n"
                        f"- Note: You can inspect this image with inspect_media path=\"{img_info['path']}\"."
                    )
                return f"[Error: Failed to decode image stream for item #{target_idx}]"

            elif content.contains(StandardDataFormats.storage_items):
                storage_items = await content.get_storage_items_async()
                paths = [item.path for item in storage_items if hasattr(item, "path")]
                return (
                    f"--- [Clipboard Item #{target_idx}: Files ({len(paths)} items, Timestamp: {ts})] ---\n"
                    + "\n".join(f"- {p}" for p in paths)
                )

            return f"[Clipboard Item #{target_idx}: Contains unsupported format]"
        except Exception as e:
            return f"[Error getting clipboard item: {e}]"

    async def set_clipboard(self, content: str = "") -> str:
        """
        Set active clipboard content via WinRT DataPackage (organically adds to Windows History).
        """
        if content is None:
            content = ""
        content_str = str(content)

        copied = False
        if WINSDK_AVAILABLE:
            try:
                pkg = DataPackage()
                pkg.set_text(content_str)
                Clipboard.set_content(pkg)
                Clipboard.flush()
                copied = True
            except Exception:
                pass

        if not copied and PYPERCLIP_AVAILABLE:
            try:
                pyperclip.copy(content_str)
                copied = True
            except Exception:
                pass

        if not copied and WIN32_AVAILABLE:
            try:
                win32clipboard.OpenClipboard()
                try:
                    win32clipboard.EmptyClipboard()
                    win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, content_str)
                    copied = True
                finally:
                    win32clipboard.CloseClipboard()
            except Exception:
                pass

        if copied:
            line_count = len(content_str.splitlines())
            return (
                f"[Success: Added to active clipboard and Windows Clipboard History ({len(content_str):,} characters, "
                f"{line_count} line(s))]"
            )
        return "[Error: Failed to write to clipboard]"

    async def delete_clipboard_item(
        self, index: Optional[int] = None, item_id: Optional[str] = None
    ) -> str:
        """
        Delete a specific entry from Windows Clipboard History.
        """
        if index is None and not item_id:
            return "[Error: delete_clipboard_item requires 'index' or 'item_id']"

        if not WINSDK_AVAILABLE:
            return "[Error: winsdk WinRT is required for deleting items from Windows History]"

        try:
            if not Clipboard.is_history_enabled():
                return "[Error: Windows Clipboard History is not enabled]"

            result = await Clipboard.get_history_items_async()
            if not result or not result.items:
                return "[Error: History is empty]"

            target_item = None
            if item_id:
                for item in result.items:
                    if str(item.id).strip("{}").lower() == str(item_id).strip("{}").lower():
                        target_item = item
                        break
            elif index is not None:
                try:
                    idx_int = int(index)
                    if 0 <= idx_int < len(result.items):
                        target_item = result.items[idx_int]
                except (ValueError, TypeError):
                    pass

            if not target_item:
                return f"[Error: Item with index={index} / item_id='{item_id}' not found]"

            deleted = Clipboard.delete_item_from_history(target_item)
            return (
                f"[Success: Item {target_item.id} deleted from Windows Clipboard History]"
                if deleted
                else "[Notice: Delete request dispatched for history item]"
            )
        except Exception as e:
            return f"[Error deleting history item: {e}]"

    def clear_clipboard_history(self) -> str:
        """
        Clear all items from Windows Clipboard History (Win + V).
        """
        if not WINSDK_AVAILABLE:
            return "[Error: winsdk WinRT is required for clearing Windows Clipboard History]"
        try:
            Clipboard.clear_history()
            return "[Success: Windows Clipboard History (Win + V) cleared]"
        except Exception as e:
            return f"[Error clearing clipboard history: {e}]"

    # Backwards-compatible shortcuts
    def read_clipboard(self) -> str:
        """Quick shortcut to read active clipboard content."""
        if PYPERCLIP_AVAILABLE:
            try:
                t = pyperclip.paste()
                if t and t.strip():
                    return f"--- Clipboard: Active Text ({len(t)} chars, Type: {_detect_text_type(t)}) ---\n{t}"
            except Exception:
                pass

        if WIN32_AVAILABLE:
            try:
                win32clipboard.OpenClipboard()
                try:
                    if win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
                        t = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
                        if t and t.strip():
                            return f"--- Clipboard: Active Text ({len(t)} chars, Type: {_detect_text_type(t)}) ---\n{t}"
                finally:
                    win32clipboard.CloseClipboard()
            except Exception:
                pass

        if PIL_AVAILABLE:
            try:
                clip_data = ImageGrab.grabclipboard()
                if isinstance(clip_data, list) and clip_data:
                    return "--- Clipboard: Copied Files ---\n" + "\n".join(f"- {f}" for f in clip_data)
                if isinstance(clip_data, Image.Image):
                    cache_dir = os.path.abspath(os.path.join(self.cwd, ".deepx", "cache"))
                    os.makedirs(cache_dir, exist_ok=True)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    save_path = os.path.join(cache_dir, f"clip_{timestamp}.png")
                    clip_data.save(save_path, format="PNG")
                    return f"[Clipboard: Image detected and saved to '{save_path}' (Resolution: {clip_data.size[0]}x{clip_data.size[1]})]"
            except Exception:
                pass

        return "[Clipboard is empty or contains non-text data]"

    def write_clipboard(self, content: str = "") -> str:
        """Quick shortcut to write to clipboard (alias to set_clipboard)."""
        content_str = str(content if content is not None else "")
        if PYPERCLIP_AVAILABLE:
            try:
                pyperclip.copy(content_str)
                return f"[Success: Copied {len(content_str)} characters to clipboard]"
            except Exception:
                pass
        return "[Error copying to clipboard]"
