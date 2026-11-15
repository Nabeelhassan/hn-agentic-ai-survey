You are clustering short phrases that Hacker News commenters used to describe their AI setup.

Each input line is `count<TAB>phrase`. Many are near-duplicates or variations of one idea.

Group them into 12–25 themes with clear, short labels (two to five words). Every input phrase must appear in exactly one group. Prefer concrete themes ("subscription fatigue", "local privacy") over vague ones ("other", "misc") — use an `other` group only for phrases that genuinely fit nowhere.

Return ONE JSON object and nothing else:

{"themes": [{"label": "short theme label", "phrases": ["exact input phrase", "..."]}]}

Rules:
1. Labels are lowercase, two to five words, and read well in a chart axis.
2. Copy phrases exactly as given; do not rewrite them.
3. Do not invent phrases that are not in the input.
4. Order groups by the sum of their input counts, descending.
5. Output JSON only.

## Phrases

{{PHRASES}}
