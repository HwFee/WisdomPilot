"""Judge0 API client for code execution with base64 encoding."""

import asyncio
import base64

import httpx

JUDGE0_TIMEOUT_SECONDS = 60.0
JUDGE0_CPU_TIME_LIMIT_SECONDS = 10
JUDGE0_MEMORY_LIMIT_KILOBYTES = 256_000
JUDGE0_PENDING_STATUS_IDS = frozenset({1, 2})
JUDGE0_POLL_ATTEMPTS = 20
JUDGE0_POLL_INTERVAL_SECONDS = 0.3


class Judge0Client:
    def __init__(self, base_url: str, client: httpx.AsyncClient | None = None) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = client
        self._owns_client = client is None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=JUDGE0_TIMEOUT_SECONDS)
        return self._client

    def _encode_text(self, text: str) -> str:
        return base64.b64encode(text.encode()).decode()

    def _submission_payload(
        self, code: str, language_id: int, stdin: str, expected_output: str
    ) -> dict[str, object]:
        payload: dict[str, object] = {
            "source_code": self._encode_text(code),
            "language_id": language_id,
            "stdin": self._encode_text(stdin),
            "cpu_time_limit": JUDGE0_CPU_TIME_LIMIT_SECONDS,
            "memory_limit": JUDGE0_MEMORY_LIMIT_KILOBYTES,
        }
        if expected_output:
            payload["expected_output"] = self._encode_text(expected_output)
        return payload

    def _status_id(self, result: dict) -> int:
        status = result.get("status")
        if isinstance(status, dict):
            return int(status.get("id", 13))
        return int(result.get("status_id", 13))

    def _decode_output_fields(self, result: dict) -> dict:
        for field in ("stdout", "stderr", "compile_output"):
            value = result.get(field)
            if value and isinstance(value, str):
                result[field] = base64.b64decode(value).decode()
        return result

    def _normalize_result(self, result: dict) -> dict[str, object]:
        result = self._decode_output_fields(dict(result))
        result["status_id"] = self._status_id(result)
        return result

    async def submit(
        self, code: str, language_id: int, stdin: str = "", expected_output: str = ""
    ) -> dict[str, object]:
        response = await self._get_client().post(
            f"{self._base_url}/submissions",
            params={"base64_encoded": "true", "wait": "true"},
            json=self._submission_payload(code, language_id, stdin, expected_output),
        )
        response.raise_for_status()
        return self._normalize_result(response.json())

    async def _poll_submission(self, token: str) -> dict:
        client = self._get_client()
        last_result: dict | None = None
        for attempt in range(JUDGE0_POLL_ATTEMPTS):
            response = await client.get(
                f"{self._base_url}/submissions/{token}",
                params={"base64_encoded": "true"},
            )
            response.raise_for_status()
            result = self._normalize_result(response.json())
            last_result = result
            if result["status_id"] not in JUDGE0_PENDING_STATUS_IDS:
                return result
            if attempt < JUDGE0_POLL_ATTEMPTS - 1:
                await asyncio.sleep(JUDGE0_POLL_INTERVAL_SECONDS)
        if last_result is not None:
            last_result["message"] = "Polling timeout"
            return last_result
        return {"status_id": 13, "message": "Invalid token"}

    async def submit_batch(
        self, code: str, language_id: int, test_cases: list[dict[str, str]]
    ) -> list[dict[str, object]]:
        # The service owns the whitespace-tolerant verdict comparison.
        submissions = [
            self._submission_payload(
                code, language_id, tc.get("input", ""), ""
            )
            for tc in test_cases
        ]
        response = await self._get_client().post(
            f"{self._base_url}/submissions/batch",
            params={"base64_encoded": "true"},
            json={"submissions": submissions},
        )
        response.raise_for_status()
        tokens_data = response.json()

        if isinstance(tokens_data, list):
            tokens = [item.get("token") for item in tokens_data]
        else:
            tokens = [item.get("token") for item in tokens_data.get("submissions", [])]

        if not tokens:
            return []

        return await self._poll_tokens(tokens)

    async def _poll_tokens(self, tokens: list[str | None]) -> list[dict[str, object]]:
        coros = [
            self._poll_submission(token) if token else self._invalid_token_result()
            for token in tokens
        ]
        tasks = [asyncio.create_task(coro) for coro in coros]
        try:
            done, pending = await asyncio.wait(
                tasks, return_when=asyncio.FIRST_EXCEPTION
            )
            first_exception: BaseException | None = None
            for task in done:
                exc = task.exception()
                if exc is not None:
                    first_exception = exc
                    break
            if first_exception is not None:
                for task in pending:
                    task.cancel()
                await asyncio.gather(*pending, return_exceptions=True)
                raise first_exception
            if pending:
                await asyncio.gather(*pending)
            return [task.result() for task in tasks]
        finally:
            for task in tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _invalid_token_result(self) -> dict[str, object]:
        return {"status_id": 13, "message": "Invalid token"}

    async def close(self) -> None:
        if self._owns_client and self._client is not None:
            await self._client.aclose()
            self._client = None
