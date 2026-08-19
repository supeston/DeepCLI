import asyncio
import json
import os
from pathlib import Path
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
class DadataOSINTTool:
    """Restricted DaData client for legitimate OSINT and due-diligence work."""
    SUGGEST_BASE = "https://suggestions.dadata.ru/suggestions/api/4_1/rs"
    CLEAN_BASE = "https://cleaner.dadata.ru/api/v1/clean"
    APP_DIR = Path(__file__).resolve().parents[2]
    ACTIONS = {                                                            "address": ("suggest", "address", False),        "address_by_id": ("findById", "address", False),        "reverse_geocode": ("geolocate", "address", False),        "ip_location": ("iplocate", "address", False),        "postal_by_index": ("findById", "postal_unit", False),        "postal_nearby": ("geolocate", "postal_unit", False),        "party": ("suggest", "party", False),        "party_by_id": ("findById", "party", False),        "bank": ("suggest", "bank", False),        "bank_by_id": ("findById", "bank", False),        "fio": ("suggest", "fio", False),        "email": ("suggest", "email", False),        "passport_issuer": ("suggest", "fms_unit", False),                                                                                    "clean_address": ("clean", "address", True),        "clean_fio": ("clean", "name", True),        "clean_phone": ("clean", "phone", True),        "clean_email": ("clean", "email", True),        "clean_passport": ("clean", "passport", True),        "clean_vehicle": ("clean", "vehicle", True),        "brand_by_inn": ("brand", "brand", True),    }
    def __init__(        self,        api_key: str | None = None,        secret_key: str | None = None,    ):
        dotenv = self._read_dotenv()
        self.api_key = (            api_key or os.getenv("DADATA_API_KEY") or dotenv.get("DADATA_API_KEY", "")        ).strip()
        self.secret_key = (            secret_key            or os.getenv("DADATA_SECRET_KEY")            or dotenv.get("DADATA_SECRET_KEY", "")        ).strip()
        allow_paid = (            os.getenv("DADATA_ALLOW_PAID")            or dotenv.get("DADATA_ALLOW_PAID", "false")        )
        self.allow_paid = str(allow_paid).strip().lower() in {"1", "true", "yes", "on"}
    @classmethod
    def _read_dotenv(cls) -> dict[str, str]:
        values: dict[str, str] = {}
        candidates = [
            Path(__file__).resolve().parents[1] / "core" / ".env",
            Path(__file__).resolve().parents[2] / ".env",
            Path.cwd() / "deepx" / "core" / ".env",
            Path.cwd() / ".env",
        ]
        for env_file in candidates:
            if env_file.is_file():
                try:
                    lines = env_file.read_text(encoding="utf-8-sig").splitlines()
                    for raw_line in lines:
                        line = raw_line.strip()
                        if not line or line.startswith("#") or "=" not in line:
                            continue
                        name, value = line.split("=", 1)
                        value = value.strip()
                        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                            value = value[1:-1]
                        values[name.strip()] = value
                    if values:
                        return values
                except OSError:
                    continue
        return values
    def _redact(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {str(key): self._redact(item) for key, item in value.items()}
        if isinstance(value, list):
            return [self._redact(item) for item in value]
        if isinstance(value, str):
            result = value
            for secret in (self.api_key, self.secret_key):
                if secret:
                    result = result.replace(secret, "[REDACTED]")
            result = re.sub(                r"([?&]token=)[^&\s\"']+",                r"\1[REDACTED]",                result,                flags=re.IGNORECASE,            )
            return result
        return value
    @staticmethod
    def _count(value: Any) -> int:
        try:
            return max(1, min(int(value), 20))
        except (TypeError, ValueError):
            return 10
    @staticmethod
    def _number(value: Any, name: str, minimum: float, maximum: float) -> float:
        try:
            number = float(value)
        except (TypeError, ValueError) as error:
            raise ValueError(f"{name} must be a number") from error
        if not minimum <= number <= maximum:
            raise ValueError(f"{name} must be between {minimum} and {maximum}")
        return number
    def _headers(self, require_secret: bool = False) -> dict[str, str]:
        headers = {            "Accept": "application/json",            "Content-Type": "application/json",            "Authorization": f"Token {self.api_key}",            "User-Agent": "DEEPX-DaData-OSINT/1.0",        }
        if require_secret:
            headers["X-Secret"] = self.secret_key
        return headers
    @staticmethod
    def _request_sync(        url: str,        headers: dict[str, str],        payload: Any,        method: str = "POST",    ) -> Any:
        body = None if payload is None else json.dumps(            payload, ensure_ascii=False        ).encode("utf-8")
        request = Request(url, data=body, headers=headers, method=method)
        try:
            with urlopen(request, timeout=20) as response:
                content = response.read()
                content_type = response.headers.get("Content-Type", "")
                if "json" in content_type:
                    return json.loads(content.decode("utf-8"))
                return content
        except HTTPError as error:
            body_text = error.read().decode("utf-8", errors="replace")
            try:
                details = json.loads(body_text)
            except json.JSONDecodeError:
                details = body_text[:1000]
            raise RuntimeError(f"DaData HTTP {error.code}: {details}") from error
        except URLError as error:
            raise RuntimeError(f"DaData network error: {error.reason}") from error
    def _payload(        self,        action: str,        query: Any,        lat: Any,        lon: Any,        count: Any,        options: dict[str, Any],    ) -> Any:
        if action in {"reverse_geocode", "postal_nearby"}:
            payload = {                "lat": self._number(lat, "lat", -90, 90),                "lon": self._number(lon, "lon", -180, 180),                "count": self._count(count),            }
            if "radius_meters" in options:
                payload["radius_meters"] = int(                    self._number(options["radius_meters"], "radius_meters", 1, 1000)                )
            for name in ("language", "division"):
                if options.get(name):
                    payload[name] = options[name]
            return payload
        text = str(query or "").strip()
        if not text:
            raise ValueError(f"query is required for action '{action}'")
        if len(text) > 300:
            raise ValueError("query must not exceed 300 characters")
        if action.startswith("clean_"):
            return [text]
        payload: dict[str, Any] = {"query": text}
        if action == "brand_by_inn":
            return payload
        if action == "ip_location":
            return {"ip": text, **{                key: options[key]                for key in ("language", "division")                if options.get(key)            }}
        payload["count"] = self._count(count)
        allowed_options = {            "kpp", "branch_type", "type", "status", "language", "division",            "from_bound", "to_bound", "locations", "locations_boost", "filters",        }
        for name in allowed_options:
            if name in options and options[name] not in (None, ""):
                payload[name] = options[name]
        if action == "address" and "locations" not in payload:
            payload["locations"] = [{"country": "*"}]
        return payload
    async def _logo_by_domain(self, query: Any) -> str:
        domain = str(query or "").strip().lower()
        domain = re.sub(r"^https?://", "", domain).split("/", 1)[0].split(":", 1)[0]
        if not re.fullmatch(            r"(?:[a-z0-9а-яё](?:[a-z0-9а-яё-]{0,61}[a-z0-9а-яё])?\.)+"            r"[a-zа-яё]{2,63}",            domain,            flags=re.IGNORECASE,        ):
            return self._json_error("Provide a valid domain for logo_by_domain.")
        safe_name = re.sub(r"[^a-zA-Z0-9.-]+", "_", domain)
        target_dir = self.APP_DIR / "dadata_logos"
        target_dir.mkdir(exist_ok=True)
        target = target_dir / f"{safe_name}.png"
        url = f"https://cdn.dadata.ru/logo/{domain}?{urlencode({'token': self.api_key})}"
        try:
            content = await asyncio.to_thread(                self._request_sync,                url,                {"Accept": "image/*", "User-Agent": "DEEPX-DaData-OSINT/1.0"},                None,                "GET",            )
            if not isinstance(content, bytes) or not content:
                raise RuntimeError("DaData returned no image data")
            target.write_bytes(content)
            return json.dumps({                "ok": True,                "source": "DaData company logos",                "action": "logo_by_domain",                "domain": domain,                "local_path": str(target),                "bytes": len(content),            }, ensure_ascii=False, indent=2)
        except Exception as error:
            return self._json_error(str(self._redact(str(error))), "logo_by_domain")
    def _json_error(self, message: str, action: str | None = None) -> str:
        result = {"ok": False, "source": "DaData API", "error": message}
        if action:
            result["action"] = action
        return json.dumps(result, ensure_ascii=False, indent=2)
    async def run(        self,        action: str,        query: Any = None,        lat: Any = None,        lon: Any = None,        count: Any = 10,        options: dict[str, Any] | None = None,    ) -> str:
        action = str(action or "").strip().lower()
        options = options if isinstance(options, dict) else {}
        if not self.api_key:
            return self._json_error(                "DADATA_API_KEY is not configured in .env.", action            )
        if action == "logo_by_domain":
            return await self._logo_by_domain(query)
        if action not in self.ACTIONS:
            return self._json_error(                "Unsupported action. Available actions: "                + ", ".join(sorted((*self.ACTIONS, "logo_by_domain"))),                action,            )
        family, resource, paid = self.ACTIONS[action]
        if paid and not self.allow_paid:
            return self._json_error(                "This action may consume a paid DaData balance and is disabled. "                "Set DADATA_ALLOW_PAID=true only after the user explicitly approves paid calls.",                action,            )
        if paid and not self.secret_key:
            return self._json_error(                "DADATA_SECRET_KEY is required for this action.", action            )
        try:
            payload = self._payload(action, query, lat, lon, count, options)
            if family == "clean":
                url = f"{self.CLEAN_BASE}/{resource}"
            elif family == "brand":
                url = "https://api.dadata.ru/findById/brand"
            else:
                url = f"{self.SUGGEST_BASE}/{family}/{resource}"
            result = await asyncio.to_thread(                self._request_sync,                url,                self._headers(require_secret=paid),                payload,            )
            return json.dumps({                "ok": True,                "source": "DaData API",                "action": action,                "paid_method": paid,                "result": self._redact(result),            }, ensure_ascii=False, indent=2)
        except Exception as error:
            return self._json_error(str(self._redact(str(error))), action)
