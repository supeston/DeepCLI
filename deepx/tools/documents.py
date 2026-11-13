import json
import os
import subprocess
import sys

from rich.markup import escape as rich_escape
from rich.panel import Panel
from rich.table import Table
from rich import box

from deepx.ui.terminal import console


class DocumentsToolsMixin:
    def make_excel(self, path: str, sheets: dict) -> str:
        abs_path = os.path.abspath(os.path.join(self.cwd, path))
        if self.is_protected(path) or self.is_protected(abs_path):
            return self._deny(path)
        os.makedirs(os.path.dirname(abs_path) or ".", exist_ok=True)
        if getattr(self, "checkpoints", None) is not None:
            self.checkpoints.record_before_modify(abs_path, "make_excel")

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
                sheet_title = str(sname)[:31] or f"Sheet{i + 1}"
                if i == 0:
                    ws = default_sheet
                    ws.title = sheet_title
                else:
                    ws = wb.create_sheet(title=sheet_title)

                if isinstance(rows, list):
                    if rows and all(isinstance(r, dict) for r in rows):
                        headers = []
                        for r in rows:
                            for k in r.keys():
                                ks = str(k)
                                if ks not in headers:
                                    headers.append(ks)
                        ws.append(headers)
                        for r in rows:
                            ws.append([r.get(h, "") for h in headers])
                    else:
                        for r in rows:
                            if isinstance(r, (list, tuple)):
                                ws.append(list(r))
                            else:
                                ws.append([str(r)])
                elif isinstance(rows, dict):
                    ws.append(["Параметр", "Значение"])
                    for k, v in rows.items():
                        ws.append([str(k), str(v)])

            wb.save(abs_path)
            if not os.path.isfile(abs_path):
                return f"[Error creating Excel file '{path}': output file was not written]"
            return f"[Success: Excel spreadsheet '{path}' created successfully]"
        except Exception as e:
            try:
                import pandas as pd
                with pd.ExcelWriter(abs_path, engine="openpyxl") as writer:
                    for sheet_name, data in sheets.items():
                        if isinstance(data, list) and len(data) > 0:
                            if all(isinstance(r, dict) for r in data):
                                df = pd.DataFrame(data)
                            elif isinstance(data[0], (list, tuple)):
                                df = pd.DataFrame(data[1:], columns=data[0])
                            else:
                                df = pd.DataFrame({"Value": data})
                        elif isinstance(data, dict):
                            df = pd.DataFrame(list(data.items()), columns=["Параметр", "Значение"])
                        else:
                            df = pd.DataFrame()
                        df.to_excel(writer, sheet_name=str(sheet_name)[:31] or "Sheet1", index=False)
                if not os.path.isfile(abs_path):
                    return f"[Error creating Excel file '{path}': output file was not written]"
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

            safe_text = rich_escape(str(text))
            if status in ["completed", "done", "finished", "true", "yes"]:
                icon = "[bold #10B981][x][/bold #10B981]"
                text_style = f"[dim #94A3B8]{safe_text}[/dim #94A3B8]"
            elif status in ["in_progress", "active", "working"]:
                icon = "[bold #536DFE][>][/bold #536DFE]"
                text_style = f"[bold #536DFE]{safe_text}[/bold #536DFE]"
            else:
                icon = "[bold white][ ][/bold white]"
                text_style = f"[white]{safe_text}[/white]"

            plan_table.add_row(icon, text_style)

        panel = Panel(
            plan_table,
            title=f"[bold #536DFE]{rich_escape(str(title))}[/bold #536DFE]",
            border_style="#536DFE",
            box=box.ROUNDED,
            expand=False,
        )
        console.print()
        console.print(panel)
        console.print()
        return f"[Success: Plan '{title}' rendered ({len(steps)} step(s))]"

    def make_docx(self, path: str, title: str = "", paragraphs: list = None) -> str:
        abs_path = os.path.abspath(os.path.join(self.cwd, path))
        if self.is_protected(path) or self.is_protected(abs_path):
            return self._deny(path)
        paragraphs = paragraphs if paragraphs is not None else []
        if isinstance(paragraphs, str):
            paragraphs = [paragraphs]
        try:
            os.makedirs(os.path.dirname(abs_path) or ".", exist_ok=True)
            if getattr(self, "checkpoints", None) is not None:
                self.checkpoints.record_before_modify(abs_path, "make_docx")
            payload = json.dumps(
                {"path": abs_path, "title": str(title or ""), "paragraphs": list(paragraphs)},
                ensure_ascii=False,
            )
            py_code = (
                "import sys, json, docx\n"
                "data = json.loads(sys.stdin.read())\n"
                "doc = docx.Document()\n"
                "if data.get('title'):\n"
                "    doc.add_heading(str(data['title']), level=0)\n"
                "for p in data.get('paragraphs') or []:\n"
                "    if isinstance(p, dict) and p.get('heading'):\n"
                "        doc.add_heading(str(p['heading']), level=int(p.get('level', 1)))\n"
                "    elif isinstance(p, dict) and p.get('text') is not None:\n"
                "        doc.add_paragraph(str(p['text']))\n"
                "    else:\n"
                "        doc.add_paragraph(str(p))\n"
                "doc.save(data['path'])\n"
                "print('SUCCESS')\n"
            )
            res = subprocess.run(
                [sys.executable, "-c", py_code],
                input=payload,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            if res.returncode != 0 or "SUCCESS" not in res.stdout or not os.path.isfile(abs_path):
                err = (res.stderr or res.stdout or "unknown error").strip()
                return f"[Error creating docx '{path}': {err}]"
            return f"[Success: Word document '{path}' created]"
        except Exception as e:
            return f"[Error creating docx: {e}]"

    def make_pptx(self, path: str, title: str = "", slides: list = None) -> str:
        abs_path = os.path.abspath(os.path.join(self.cwd, path))
        if self.is_protected(path) or self.is_protected(abs_path):
            return self._deny(path)
        slides = slides if slides is not None else []
        if isinstance(slides, str):
            slides = [{"title": str(title or "Slide 1"), "content": [slides]}]
        try:
            os.makedirs(os.path.dirname(abs_path) or ".", exist_ok=True)
            if getattr(self, "checkpoints", None) is not None:
                self.checkpoints.record_before_modify(abs_path, "make_pptx")
            payload = json.dumps(
                {"path": abs_path, "title": str(title or ""), "slides": list(slides)},
                ensure_ascii=False,
            )
            py_code = (
                "import sys, json\n"
                "from pptx import Presentation\n"
                "data = json.loads(sys.stdin.read())\n"
                "prs = Presentation()\n"
                "deck_title = data.get('title') or ''\n"
                "slides_data = data.get('slides') or []\n"
                "if deck_title and not slides_data:\n"
                "    s0 = prs.slides.add_slide(prs.slide_layouts[0])\n"
                "    if s0.shapes.title: s0.shapes.title.text = str(deck_title)\n"
                "for idx, s in enumerate(slides_data):\n"
                "    if isinstance(s, str):\n"
                "        s = {'title': deck_title if idx == 0 else f'Slide {idx + 1}', 'content': [s]}\n"
                "    elif not isinstance(s, dict):\n"
                "        s = {'title': f'Slide {idx + 1}', 'content': [str(s)]}\n"
                "    slide = prs.slides.add_slide(prs.slide_layouts[1])\n"
                "    slide_title = s.get('title') or (deck_title if idx == 0 else '')\n"
                "    if slide.shapes.title: slide.shapes.title.text = str(slide_title)\n"
                "    raw_content = s.get('content', s.get('bullets', []))\n"
                "    if isinstance(raw_content, str):\n"
                "        bullets = [ln for ln in raw_content.splitlines() if ln.strip()] or [raw_content]\n"
                "    elif isinstance(raw_content, (list, tuple)):\n"
                "        bullets = [str(item) for item in raw_content]\n"
                "    elif raw_content is None:\n"
                "        bullets = []\n"
                "    else:\n"
                "        bullets = [str(raw_content)]\n"
                "    if len(slide.placeholders) > 1:\n"
                "        tf = slide.placeholders[1].text_frame\n"
                "        tf.text = bullets[0] if bullets else ''\n"
                "        for b in bullets[1:]:\n"
                "            p = tf.add_paragraph()\n"
                "            p.text = b\n"
                "prs.save(data['path'])\n"
                "print('SUCCESS')\n"
            )
            res = subprocess.run(
                [sys.executable, "-c", py_code],
                input=payload,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            if res.returncode != 0 or "SUCCESS" not in res.stdout or not os.path.isfile(abs_path):
                err = (res.stderr or res.stdout or "unknown error").strip()
                return f"[Error creating pptx '{path}': {err}]"
            return f"[Success: PowerPoint presentation '{path}' created ({len(slides)} slide(s))]"
        except Exception as e:
            return f"[Error creating pptx: {e}]"

