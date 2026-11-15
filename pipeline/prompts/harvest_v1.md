You are building a controlled vocabulary from Hacker News comments about AI tooling.

For each comment, list every named product, service, company, model, or tool that is mentioned. Include the ones mentioned critically or dismissively.

Return ONE JSON object and nothing else:

{"mentions": [{"raw": "text as written", "normalized": "lowercase canonical guess", "category": "subscription | harness | orchestration | platform | model-source | unknown", "comment_id": "the enclosing comment id"}]}

Rules:
1. One mention per distinct product per comment, even if named several times.
2. `normalized` should be the product's common name, lowercase, without tier or version text ("Claude Max" -> "claude", "GPT-5.1 Codex" -> "codex", "Opus 5.5" -> "opus").
3. Categories:
   - `subscription` — a company selling a paid plan (Anthropic, OpenAI, Cursor, GitHub).
   - `harness` — an interface for driving a coding model (Claude Code, Codex CLI, Cursor, Aider, OpenCode, Pi, Zed).
   - `orchestration` — tooling for coordinating multiple agents (Gas Town, Munder Difflin, Ruflo, custom scripts).
   - `platform` — an agent product used outside coding (OpenClaw, Hermes Agent, Dots, Muse).
   - `model-source` — a way to obtain models (OpenRouter, Ollama, LM Studio, a provider API).
   - `unknown` — a product you cannot place.
4. Skip generic technology (Linux, Python, Git, VS Code) unless the comment treats it as the AI setup itself.
5. Do not explain. Output JSON only.

## Comments

{{COMMENTS}}
