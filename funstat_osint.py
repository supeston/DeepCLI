import asyncio
from collections import Counter
import json
import os
from pathlib import Path
import re
import time
from typing import Any


class FunstatOSINTTool:
    ALLOWED_ACTIONS = {"free_scan", "stats_min", "reputation", "counts"}
    SWAGGER_URLS = (
        "https://telelog.org/swagger/v1/swagger.json",
        "https://raw.githubusercontent.com/chizumeiji/funstat-api/main/swagger.json",
    )
    METHOD_ROUTES = {
        "stats_min": "/api/v1/users/{id}/stats_min",
        "full_stats": "/api/v1/users/{id}/stats",
        "reputation": "/api/v1/users/reputation",
        "messages_count": "/api/v1/users/{id}/messages_count",
        "groups_count": "/api/v1/users/{id}/groups_count",
        "messages": "/api/v1/users/{id}/messages",
        "stickers": "/api/v1/users/{id}/stickers",
        "gifts": "/api/v1/users/{id}/gifts_relation",
    }
    FALLBACK_FREE = {
        "stats_min",
        "reputation",
        "messages_count",
        "groups_count",
    }
    _pricing_cache: tuple[float, dict[str, Any]] | None = None

    def __init__(self, token: str | None = None):
        self.token = (
            token
            or os.getenv("FUNSTAT_API_TOKEN", "")
            or self._token_from_dotenv()
        ).strip()

    @staticmethod
    def _token_from_dotenv() -> str:
        env_file = Path(__file__).resolve().with_name(".env")
        try:
            lines = env_file.read_text(encoding="utf-8-sig").splitlines()
        except OSError:
            return ""
        for raw_line in lines:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, value = line.split("=", 1)
            if name.strip() != "FUNSTAT_API_TOKEN":
                continue
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            if value == "ВСТАВЬТЕ_СЮДА_ТОКЕН":
                return ""
            return value.strip()
        return ""

    @staticmethod
    def _telegram_id(value: Any) -> int:
        if isinstance(value, bool):
            raise ValueError("telegram_id must be a numeric Telegram user ID")
        text = str(value or "").strip()
        if not text.isdigit():
            raise ValueError(
                "telegram_id must be numeric. To search by username, pass it in the username field."
            )
        telegram_id = int(text)
        if telegram_id <= 0:
            raise ValueError("telegram_id must be greater than zero")
        return telegram_id

    @staticmethod
    def _plain(value: Any) -> Any:
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        if hasattr(value, "model_dump"):
            return FunstatOSINTTool._plain(value.model_dump(mode="json"))
        if isinstance(value, dict):
            return {str(key): FunstatOSINTTool._plain(item) for key, item in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [FunstatOSINTTool._plain(item) for item in value]
        return str(value)

    @staticmethod
    def _cell(value: Any) -> str:
        if value is None or value == "":
            return "не найдено"
        if isinstance(value, bool):
            return "да" if value else "нет"
        return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ")

    def _safe_error(self, error: BaseException) -> str:
        message = str(error).replace(self.token, "[REDACTED]") if self.token else str(error)
        message = " ".join(message.split())
        return message[:500] or type(error).__name__

    @staticmethod
    def _classify_summary(summary: str) -> dict[str, Any]:
        normalized = " ".join(str(summary or "").split())
        costs = [
            float(value)
            for value in re.findall(
                r"\bcost\b[^\d]{0,12}(\d+(?:[.,]\d+)?)",
                normalized,
                flags=re.IGNORECASE,
            )
        ]
        if costs:
            cost = max(costs)
            return {
                "status": "free" if cost == 0 else "paid",
                "declared_cost": cost,
                "summary": normalized,
            }
        if re.search(r"\bfree\b", normalized, flags=re.IGNORECASE):
            return {"status": "free", "declared_cost": 0.0, "summary": normalized}
        return {"status": "unknown", "declared_cost": None, "summary": normalized}

    @classmethod
    def _fallback_pricing(cls, reason: str) -> dict[str, Any]:
        methods = {}
        for name in cls.METHOD_ROUTES:
            methods[name] = {
                "status": "free" if name in cls.FALLBACK_FREE else "blocked",
                "declared_cost": 0.0 if name in cls.FALLBACK_FREE else None,
                "summary": "Conservative built-in fallback",
            }
        return {
            "source": "built-in conservative fallback",
            "warning": reason,
            "methods": methods,
        }

    @classmethod
    async def _load_pricing(cls) -> dict[str, Any]:
        now = time.monotonic()
        if cls._pricing_cache and now - cls._pricing_cache[0] < 600:
            return cls._pricing_cache[1]
        errors = []
        try:
            import httpx
        except ImportError:
            return cls._fallback_pricing("httpx is unavailable")

        for url in cls.SWAGGER_URLS:
            try:
                async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as http:
                    response = await http.get(url)
                    response.raise_for_status()
                    document = response.json()
                paths = document.get("paths", {})
                methods = {}
                for name, route in cls.METHOD_ROUTES.items():
                    operation = paths.get(route, {}).get("get")
                    if not isinstance(operation, dict):
                        methods[name] = {
                            "status": "unavailable",
                            "declared_cost": None,
                            "summary": "Route is absent from the current Swagger document",
                        }
                        continue
                    methods[name] = cls._classify_summary(operation.get("summary", ""))
                    if methods[name]["status"] == "unknown":
                        methods[name]["status"] = "blocked"
                pricing = {
                    "source": url,
                    "api_title": document.get("info", {}).get("title"),
                    "methods": methods,
                }
                cls._pricing_cache = (now, pricing)
                return pricing
            except Exception as error:
                errors.append(f"{url}: {type(error).__name__}")
        pricing = cls._fallback_pricing("; ".join(errors))
        cls._pricing_cache = (now, pricing)
        return pricing

    @staticmethod
    def _tech_cost(payload: Any) -> float:
        tech = getattr(payload, "tech", None)
        value = getattr(tech, "request_cost", 0) if tech is not None else 0
        try:
            return float(value or 0)
        except (TypeError, ValueError):
            return 0.0

    async def _call(self, name: str, awaitable) -> dict[str, Any]:
        try:
            result = await awaitable
            return {
                "status": "ok",
                "cost_reported": self._tech_cost(result),
                "data": self._plain(result),
            }
        except Exception as error:
            return {
                "status": "error",
                "error_type": type(error).__name__,
                "error": self._safe_error(error),
            }

    @staticmethod
    def _payload_data(result: dict[str, Any]) -> Any:
        payload = result.get("data")
        if isinstance(payload, dict) and "data" in payload:
            return payload.get("data")
        return payload

    def _render_report(
        self,
        telegram_id: int,
        action: str,
        methods: dict[str, dict[str, Any]],
        requested_username: str = "",
        pricing: dict[str, Any] | None = None,
    ) -> str:
        resolution = self._payload_data(methods.get("username_resolution", {}))
        minimal_stats = self._payload_data(methods.get("stats_min", {}))
        full_stats = self._payload_data(methods.get("full_stats", {}))
        reputation = self._payload_data(methods.get("reputation", {}))
        messages_count = self._payload_data(methods.get("messages_count", {}))
        groups = self._payload_data(methods.get("groups_count", {}))
        message_rows = self._payload_data(methods.get("messages", {}))
        gifts = self._payload_data(methods.get("gifts", {}))
        stickers = self._payload_data(methods.get("stickers", {}))
        resolution = (
            resolution[0]
            if isinstance(resolution, list) and resolution and isinstance(resolution[0], dict)
            else {}
        )
        minimal_stats = minimal_stats if isinstance(minimal_stats, dict) else {}
        full_stats = full_stats if isinstance(full_stats, dict) else {}
        stats = {**resolution, **minimal_stats, **full_stats}
        reputation = reputation if isinstance(reputation, dict) else {}
        message_rows = message_rows if isinstance(message_rows, list) else []
        gifts = gifts if isinstance(gifts, list) else []
        stickers = stickers if isinstance(stickers, list) else []

        full_name = " ".join(
            part for part in (
                str(stats.get("first_name") or "").strip(),
                str(stats.get("last_name") or "").strip(),
            )
            if part
        )
        total_messages = (
            messages_count
            if isinstance(messages_count, int)
            else stats.get("total_msg_count")
        )
        total_groups = groups if isinstance(groups, int) else stats.get("total_groups")
        words = Counter()
        for message in message_rows:
            if not isinstance(message, dict):
                continue
            for word in re.findall(
                r"[0-9A-Za-zА-Яа-яЁё_]{2,}",
                str(message.get("text") or "").lower(),
            ):
                words[word] += 1
        word_frequency = words.most_common(25)

        if isinstance(total_messages, int):
            if total_messages >= 10000:
                activity = "высокая"
            elif total_messages >= 1000:
                activity = "средняя"
            elif total_messages > 0:
                activity = "низкая"
            else:
                activity = "сообщения не обнаружены"
        else:
            activity = "недостаточно данных"

        lines = [
            f"# Funstat / Telelog: бесплатный OSINT-отчёт",
            "",
            f"- **Telegram ID:** `{telegram_id}`",
            *(
                [f"- **Запрошенный username:** `@{requested_username}`"]
                if requested_username
                else []
            ),
            f"- **Режим:** `{action}`",
            (
                "- **Политика расходов:** одно разрешение username в ID (`≈0,1 💠`), "
                "после него только маршруты `0 💠`"
                if requested_username
                else "- **Политика расходов:** только маршруты с текущей стоимостью `0 💠`"
            ),
            "",
            "## Профиль",
            "",
            "| Поле | Значение |",
            "| --- | --- |",
            f"| Имя в базе | {self._cell(full_name)} |",
            f"| Username | {self._cell(stats.get('username') or requested_username)} |",
            f"| Premium | {self._cell(stats.get('has_premium'))} |",
            f"| Бот | {self._cell(stats.get('is_bot'))} |",
            f"| Активный аккаунт | {self._cell(stats.get('is_active'))} |",
            f"| Первое сообщение | {self._cell(stats.get('first_msg_date'))} |",
            f"| Последнее сообщение | {self._cell(stats.get('last_msg_date'))} |",
            "",
            "## Активность",
            "",
            "| Метрика | Значение |",
            "| --- | --- |",
            f"| Сообщений | {self._cell(total_messages)} |",
            f"| Групп | {self._cell(total_groups)} |",
            f"| Сообщений в группах | {self._cell(stats.get('msg_in_groups_count'))} |",
            f"| Групп с правами администратора | {self._cell(stats.get('adm_in_groups'))} |",
            f"| Зафиксировано имён | {self._cell(stats.get('names_count'))} |",
            f"| Зафиксировано username | {self._cell(stats.get('usernames_count'))} |",
            f"| Реплаи | {self._cell(stats.get('reply_percent'))} |",
            f"| Медиа | {self._cell(stats.get('media_percent'))} |",
            f"| Голосовые | {self._cell(stats.get('voice_count'))} |",
            f"| Кружки | {self._cell(stats.get('circle_count'))} |",
            "",
            "## Репутация",
            "",
            "| Метрика | Значение |",
            "| --- | --- |",
            f"| Уровень | {self._cell(reputation.get('reputation_name'))} |",
            f"| Голосов | {self._cell(reputation.get('num_votes'))} |",
            f"| Положительных | {self._cell(reputation.get('positive_count'))} |",
            f"| Отрицательных | {self._cell(reputation.get('negative_count'))} |",
            f"| Отзывов | {self._cell(reputation.get('review_count'))} |",
            f"| Байесовская оценка | {self._cell(reputation.get('bayesian_average'))} |",
            "",
            "## Аналитическая сводка",
            "",
            f"- Наблюдаемая активность по объёму сообщений: **{activity}**.",
        ]

        if word_frequency:
            lines.extend([
                "",
                "## Частота слов",
                "",
                f"Анализ по доступной выборке из {len(message_rows)} сообщений:",
                "",
                "| Слово | Количество |",
                "| --- | ---: |",
                *[
                    f"| {self._cell(word)} | {count} |"
                    for word, count in word_frequency
                ],
            ])
        if stickers:
            lines.extend([
                "",
                "## Стикеры",
                "",
                f"Найдено наборов: **{len(stickers)}**.",
            ])
        if gifts:
            lines.extend([
                "",
                "## Подарки",
                "",
                f"Найдено связей по подаркам: **{len(gifts)}**.",
            ])

        failed = [
            f"`{name}` ({result.get('error_type', 'Error')}: {result.get('error', 'unknown error')})"
            for name, result in methods.items()
            if result.get("status") != "ok"
        ]
        if failed:
            lines.append("- Не удалось получить: " + "; ".join(failed) + ".")
        if reputation.get("num_votes") in (None, 0):
            lines.append("- Репутационных голосов недостаточно для надёжного вывода о доверии.")
        blocked = []
        if pricing:
            blocked = [
                name
                for name, details in pricing.get("methods", {}).items()
                if details.get("status") != "free"
            ]
        lines.extend([
            "",
            "## Ограничения бесплатного режима",
            "",
            (
                "- Заблокированные по актуальному Swagger методы: "
                + (", ".join(f"`{name}`" for name in blocked) if blocked else "нет")
                + "."
            ),
            "- Методы с неизвестной или ненулевой ценой не вызываются.",
            "- Отсутствие записи означает только отсутствие данных в базе Telelog, а не отсутствие факта в реальности.",
        ])
        return "\n".join(lines)

    async def run(
        self,
        action: str = "free_scan",
        telegram_id: Any = None,
        username: Any = None,
    ) -> str:
        action = str(action or "free_scan").strip().lower()
        if action not in self.ALLOWED_ACTIONS:
            return json.dumps({
                "ok": False,
                "error": (
                    f"Unsupported action '{action}'. Allowed free-only actions: "
                    + ", ".join(sorted(self.ALLOWED_ACTIONS))
                ),
            }, ensure_ascii=False, indent=2)
        if not self.token:
            return json.dumps({
                "ok": False,
                "error": (
                    "FUNSTAT_API_TOKEN is not configured. Set it in the environment "
                    "before starting DEEPX."
                ),
            }, ensure_ascii=False, indent=2)

        try:
            from funstat_api import AsyncFunstatClient
        except ImportError:
            return json.dumps({
                "ok": False,
                "error": "Dependency missing: install it with `python -m pip install funstat-api`.",
            }, ensure_ascii=False, indent=2)

        pricing = await self._load_pricing()
        method_pricing = pricing.get("methods", {})

        def is_free(method: str) -> bool:
            return method_pricing.get(method, {}).get("status") == "free"

        requested_username = ""
        resolution_result = None
        async with AsyncFunstatClient(self.token) as client:
            if telegram_id not in (None, ""):
                try:
                    user_id = self._telegram_id(telegram_id)
                except ValueError as error:
                    return json.dumps(
                        {"ok": False, "error": str(error)},
                        ensure_ascii=False,
                        indent=2,
                    )
            else:
                requested_username = str(username or "").strip()
                if requested_username.startswith("https://t.me/"):
                    requested_username = requested_username.split("https://t.me/", 1)[1]
                requested_username = requested_username.strip().lstrip("@").split("?", 1)[0].strip("/")
                if not requested_username or not all(
                    char.isalnum() or char == "_" for char in requested_username
                ):
                    return json.dumps({
                        "ok": False,
                        "error": "Provide telegram_id or a valid Telegram username.",
                    }, ensure_ascii=False, indent=2)

                resolution_result = await self._call(
                    "username_resolution",
                    client.resolve_username(requested_username),
                )
                resolution_payload = self._payload_data(resolution_result)
                if (
                    resolution_result.get("status") != "ok"
                    or not isinstance(resolution_payload, list)
                    or not resolution_payload
                    or not isinstance(resolution_payload[0], dict)
                    or not resolution_payload[0].get("id")
                ):
                    return json.dumps({
                        "ok": False,
                        "source": "Funstat / Telelog API",
                        "requested_username": requested_username,
                        "error": "Username could not be resolved to a Telegram ID.",
                        "username_resolution": resolution_result,
                    }, ensure_ascii=False, indent=2)
                user_id = int(resolution_payload[0]["id"])

            calls = {}
            if action in ("free_scan", "stats_min") and is_free("stats_min"):
                calls["stats_min"] = self._call("stats_min", client.stats_min(user_id))
            if action == "free_scan" and is_free("full_stats"):
                calls["full_stats"] = self._call("full_stats", client.stats(user_id))
            if action in ("free_scan", "reputation") and is_free("reputation"):
                calls["reputation"] = self._call("reputation", client.rep(user_id))
            if action in ("free_scan", "counts") and is_free("messages_count"):
                calls["messages_count"] = self._call(
                    "messages_count",
                    client.messages_count(user_id),
                )
            if action in ("free_scan", "counts") and is_free("groups_count"):
                calls["groups_count"] = self._call(
                    "groups_count",
                    client.groups_count(user_id, only_msg=False),
                )
            if action == "free_scan" and is_free("stickers"):
                calls["stickers"] = self._call("stickers", client.get_stickers(user_id))
            if action == "free_scan" and is_free("gifts"):
                calls["gifts"] = self._call(
                    "gifts",
                    client.get_gifts(user_id, limit=100, page=1),
                )
            if action == "free_scan" and is_free("messages"):
                calls["messages"] = self._call(
                    "messages",
                    client.get_messages(user_id, limit=100, page=1),
                )
            results = dict(zip(calls, await asyncio.gather(*calls.values())))
            if resolution_result is not None:
                results = {"username_resolution": resolution_result, **results}

        charged = {
            name: result.get("cost_reported")
            for name, result in results.items()
            if name != "username_resolution"
            and float(result.get("cost_reported") or 0) > 0
        }
        report = self._render_report(
            user_id,
            action,
            results,
            requested_username=requested_username,
            pricing=pricing,
        )
        return json.dumps({
            "ok": not charged,
            "source": "Funstat / Telelog API",
            "telegram_id": user_id,
            "requested_username": requested_username or None,
            "free_only_after_username_resolution": True,
            "pricing_policy": pricing,
            "unexpected_reported_costs": charged,
            "report_markdown": report,
            "methods": results,
        }, ensure_ascii=False, indent=2)
