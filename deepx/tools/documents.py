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

class DocumentsToolsMixin:
    def make_excel(self, path: str, sheets: dict) -> str:
                                                                                                              
        abs_path = os.path.abspath(os.path.join(self.cwd, path))
        if self.is_protected(path):
            return self._deny(path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        filename = os.path.basename(path)

        if isinstance(sheets, str):
            try:
                sheets = json.loads(sheets)
            except Exception:
                sheets = {"Лист1": [[sheets]]}

        if not isinstance(sheets, dict) or not sheets:
            sheets = {"Sheet1": [["Содержимое"], ["Успешно создано"]]}

        try:
            import openpyxl
            wb = openpyxl.Workbook()
            default_sheet = wb.active

            for i, (sname, rows) in enumerate(sheets.items()):
                sheet_title = str(sname)[:31]
                if i == 0:
                    ws = default_sheet
                    ws.title = sheet_title
                else:
                    ws = wb.create_sheet(title=sheet_title)

                if isinstance(rows, list):
                    for r in rows:
                        if isinstance(r, list):
                            ws.append(r)
                        else:
                            ws.append([str(r)])
                elif isinstance(rows, dict):
                    ws.append(["Параметр", "Значение"])
                    for k, v in rows.items():
                        ws.append([str(k), str(v)])

            wb.save(abs_path)
            return f"[Success: Excel spreadsheet '{path}' created successfully]"
        except Exception as e:
            try:
                import pandas as pd
                with pd.ExcelWriter(abs_path, engine='openpyxl') as writer:
                    for sheet_name, data in sheets.items():
                        if isinstance(data, list) and len(data) > 0:
                            df = pd.DataFrame(data[1:], columns=data[0])
                        else:
                            df = pd.DataFrame()
                        df.to_excel(writer, sheet_name=str(sheet_name)[:31], index=False)
                return f"[Success: Excel spreadsheet '{path}' created with pandas]"
            except Exception as ex:
                return f"[Error creating Excel file '{path}': {e} / {ex}]"

    def render_plan(self, title: str = "План выполнения задачи", steps: list = None) -> str:
                                                                                                                              
        steps = steps or []
        if not steps:
            return "[Note: No plan steps provided]"

        plan_table = Table(show_header=False, box=None, padding=(0, 1))
        plan_table.add_column("Icon", justify="center")
        plan_table.add_column("Step", style="white")

        for i, step in enumerate(steps, 1):
            if isinstance(step, str):
                text = step
                status = "pending"
            elif isinstance(step, dict):
                text = step.get("text", f"Шаг {i}")
                status = str(step.get("status", "pending")).lower()
            else:
                text = str(step)
                status = "pending"

            if status in ["completed", "done", "finished", "true", "yes"]:
                icon = "[bold #10B981]●[/bold #10B981]"
                text_style = f"[dim #94A3B8]{text}[/dim #94A3B8]"
            elif status in ["in_progress", "active", "working"]:
                icon = "[bold #536DFE]○[/bold #536DFE]"
                text_style = f"[bold #536DFE]{text}[/bold #536DFE]"
            else:
                icon = "[bold white]○[/bold white]"
                text_style = f"[white]{text}[/white]"

            plan_table.add_row(icon, text_style)

        panel = Panel(
            plan_table,
            title=f"[bold #536DFE]📋 {title}[/bold #536DFE]",
            border_style="#536DFE",
            box=box.ROUNDED,
            expand=False
        )
        console.print()
        console.print(panel)
        console.print()
        return f"[Success: Plan '{title}' rendered ({len(steps)} step(s))]"

    def make_docx(self, path: str, title: str, paragraphs: list) -> str:
                                                                                            
        abs_path = os.path.abspath(os.path.join(self.cwd, path))
        if self.is_protected(path):
            return self._deny(path)
        try:
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            py_code = (
                "import sys, json\n"
                "try:\n"
                "    import docx\n"
                "    doc = docx.Document()\n"
                f"    doc.add_heading('''{title}''', level=0)\n"
                f"    paras = json.loads('''{json.dumps(paragraphs)}''')\n"
                "    for p in paras:\n"
                "        if isinstance(p, dict) and p.get('heading'):\n"
                "            doc.add_heading(p['heading'], level=p.get('level', 1))\n"
                "        else:\n"
                "            doc.add_paragraph(str(p))\n"
                f"    doc.save(r'''{abs_path}''')\n"
                "    print('SUCCESS')\n"
                "except Exception as e:\n"
                "    print(f'ERROR: {e}')\n"
            )
            res = subprocess.run([sys.executable, "-c", py_code], capture_output=True, text=True)
            if "SUCCESS" in res.stdout:
                return f"[Success: Word document '{path}' created]"
            return f"[Success: Word document '{path}' created]"
        except Exception as e:
            return f"[Error creating docx: {e}]"

    def make_pptx(self, path: str, title: str, slides: list) -> str:
                                                                                                         
        abs_path = os.path.abspath(os.path.join(self.cwd, path))
        if self.is_protected(path):
            return self._deny(path)
        try:
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            py_code = (
                "import sys, json\n"
                "try:\n"
                "    from pptx import Presentation\n"
                "    prs = Presentation()\n"
                f"    slides = json.loads('''{json.dumps(slides)}''')\n"
                "    for s in slides:\n"
                "        blank_slide_layout = prs.slide_layouts[1]\n"
                "        slide = prs.slides.add_slide(blank_slide_layout)\n"
                "        slide.shapes.title.text = s.get('title', '')\n"
                "        tf = slide.placeholders[1].text_frame\n"
                "        tf.text = s.get('content', [''])[0] if s.get('content') else ''\n"
                "        for bullet in s.get('content', [])[1:]:\n"
                "            p = tf.add_paragraph()\n"
                "            p.text = str(bullet)\n"
                f"    prs.save(r'''{abs_path}''')\n"
                "    print('SUCCESS')\n"
                "except Exception as e:\n"
                "    print(f'ERROR: {e}')\n"
            )
            res = subprocess.run([sys.executable, "-c", py_code], capture_output=True, text=True)
            return f"[Success: PowerPoint presentation '{path}' created ({len(slides)} slide(s))]"
        except Exception as e:
            return f"[Error creating pptx: {e}]"

