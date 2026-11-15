# Extraction runs through Command Code headless, not a vendor SDK

Extraction shells out to `cmd -p --output-format json` with a pinned model id instead of calling
a provider API directly. The billed account is the existing Command Code plan, there is no second
key to manage, and the final NDJSON line reports real token usage so `meta.json` can record actual
spend. The cost is a dependency on a local CLI at extraction time — acceptable because committed
snapshot outputs are the artifact; CI never re-extracts.
