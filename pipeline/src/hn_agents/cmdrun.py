from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field

PRICES_PER_MTOK: dict[str, tuple[float, float]] = {
    "z-ai/glm-5.3-flash": (0.15, 0.50),
    "deepseek/deepseek-v4.1-flash": (0.15, 0.60),
    "z-ai/glm-5.3-flashx": (0.37, 1.25),
}


@dataclass
class CmdRun:
    final_text: str
    usage: dict = field(default_factory=dict)
    duration_ms: int = 0
    subtype: str = "success"
    exit_code: int = 0


def _pick(usage: dict, *names: str) -> int:
    for name in names:
        value = usage.get(name)
        if isinstance(value, (int, float)):
            return int(value)
    return 0


def token_counts(usage: dict) -> tuple[int, int, int]:
    input_tokens = _pick(usage, "input_tokens", "inputTokens", "prompt_tokens")
    output_tokens = _pick(usage, "output_tokens", "outputTokens", "completion_tokens")
    cache_read = _pick(usage, "cache_read_input_tokens", "cacheReadInputTokens", "cached_tokens")
    return input_tokens, output_tokens, cache_read


def estimate_cost(usage: dict, model: str) -> float:
    input_tokens, output_tokens, cache_read = token_counts(usage)
    price_in, price_out = PRICES_PER_MTOK.get(model, (0.0, 0.0))
    billable_in = max(input_tokens - cache_read, 0)
    return (billable_in * price_in + output_tokens * price_out) / 1_000_000


async def run_cmd(
    prompt: str, model: str, *, max_turns: int = 4, timeout: float = 420.0, effort: str = "low"
) -> CmdRun:
    proc = await asyncio.create_subprocess_exec(
        "cmd",
        "-p",
        "--output-format",
        "json",
        "--model",
        model,
        "--effort",
        effort,
        "--max-turns",
        str(max_turns),
        "--skip-onboarding",
        "--trust",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(prompt.encode("utf-8")), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        raise RuntimeError(f"cmd timed out after {timeout}s on {model}")

    text = stdout.decode("utf-8", errors="replace")
    err = stderr.decode("utf-8", errors="replace")
    result: dict | None = None
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            frame = json.loads(line)
        except json.JSONDecodeError:
            continue
        if frame.get("type") == "result":
            result = frame

    if result is None:
        tail = err.strip().splitlines()[-3:]
        raise RuntimeError(f"cmd produced no result frame (exit {proc.returncode}): {' | '.join(tail)}")

    if result.get("subtype") != "success":
        error = result.get("error") or result.get("finalText") or result.get("subtype")
        raise RuntimeError(f"cmd run failed: {error}")

    return CmdRun(
        final_text=result.get("finalText") or "",
        usage=result.get("usage") or {},
        duration_ms=int(result.get("durationMs") or 0),
        subtype=result.get("subtype") or "success",
        exit_code=proc.returncode or 0,
    )


def parse_json_object(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned
        if cleaned.rstrip().endswith("```"):
            cleaned = cleaned.rstrip()[:-3]
    cleaned = cleaned.strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON object in response")
    return json.loads(cleaned[start : end + 1])
