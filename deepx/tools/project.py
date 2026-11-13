from datetime import datetime, timezone
import json
import os

                                                                                
                    
                                                                                

class ProjectToolsMixin:
    def _check_memory_protected(self):
        checker = getattr(self, "is_protected", None)
        if getattr(self, "protect_self", False) and callable(checker) and checker(self.project_memory_file):
            deny_fn = getattr(self, "_deny", None)
            return deny_fn(self.project_memory_file) if callable(deny_fn) else "[Access denied]"
        return None
    def _load_project_memory(self) -> dict:
                                                                           
        default = {
            "version": 1,
            "project": os.path.basename(self.cwd),
            "updated_at": None,
            "summary": "",
            "current_task": "",
            "completed": [],
            "next_steps": [],
            "important_files": [],
            "facts": [],
            "events": [],
        }
        if not os.path.exists(self.project_memory_file):
            return default
        try:
            with open(self.project_memory_file, "r", encoding="utf-8") as file:
                stored = json.load(file)
            if not isinstance(stored, dict):
                raise ValueError("memory root must be an object")
            for key, value in default.items():
                stored.setdefault(key, value)
            return stored
        except Exception as error:
            raise RuntimeError(f"Cannot read project memory: {error}") from error

    def _save_project_memory(self, memory: dict):
                                                                                          
        memory["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        temp_path = self.project_memory_file + ".tmp"
        with open(temp_path, "w", encoding="utf-8") as file:
            json.dump(memory, file, ensure_ascii=False, indent=2)
            file.write("\n")
        os.replace(temp_path, self.project_memory_file)

    @staticmethod
    def _memory_list(value, name: str) -> list:
        if value is None:
            return []
        if isinstance(value, str):
            value = [value]
        if not isinstance(value, list):
            raise ValueError(f"{name} must be a list")
        return [str(item).strip() for item in value if str(item).strip()]

    def project_memory(self, action: str, args: dict) -> str:
        denied = self._check_memory_protected()
        if denied:
            return denied
        action = (action or "get").strip().lower()
        try:
            memory = self._load_project_memory()
            if action in ("get", "view", "status"):
                return json.dumps(memory, ensure_ascii=False, indent=2)

            if action == "update":
                scalar_fields = ("summary", "current_task")
                list_fields = ("completed", "next_steps", "important_files", "facts")
                for field in scalar_fields:
                    if field in args:
                        memory[field] = str(args[field]).strip()
                for field in list_fields:
                    if field in args:
                        memory[field] = self._memory_list(args[field], field)
                self._save_project_memory(memory)
                return f"[Success: Project memory updated at '{self.project_memory_file}']"

            if action in ("append_event", "log"):
                event = {
                    "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "task": str(args.get("task", "")).strip(),
                    "result": str(args.get("result", "")).strip(),
                    "status": str(args.get("status", "completed")).strip() or "completed",
                    "files": self._memory_list(args.get("files", []), "files"),
                }
                if not event["task"] or not event["result"]:
                    return "[Error: append_event requires non-empty task and result]"
                memory["events"].append(event)
                memory["events"] = memory["events"][-50:]
                self._save_project_memory(memory)
                return f"[Success: Project event recorded ({len(memory['events'])} retained)]"

            return "[Error: project_memory action must be get, update, or append_event]"
        except Exception as error:
            return f"[Error in project_memory: {error}]"

