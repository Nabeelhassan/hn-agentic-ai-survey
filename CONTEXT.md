# HN Agentic AI Survey

A tracked snapshot of what Hacker News says it uses: subscriptions, models outside those
subscriptions, coding harnesses, orchestration tools, and agent platforms. This context
exists so the same thread can be measured again later and compared honestly.

## Language

**Respondent**:
A distinct HN author who reports at least one thing about their own setup.
_Avoid_: user, participant, account, answerer

**Commenter**:
Any HN author who posted a comment in the thread, including meta and off-topic ones.
_Avoid_: respondent (when they reported nothing about their setup)

**Substantive answer**:
A comment that states something about the author's own setup. Partial answers are substantive.
_Avoid_: valid comment, real comment

**Subscription**:
A paid recurring plan the author personally pays for. Free tiers, employer-provided seats, and
trials are not subscriptions.
_Avoid_: plan (alone), licence, seat

**Tier**:
The named level of a subscription, as the author described it ("Max 20x", "Plus", "Pro").
_Avoid_: plan, level, edition

**Harness**:
The interface that drives a model for coding, whether a CLI, an IDE integration, or a custom
front end. A harness is not a model.
_Avoid_: agent (when the interface is meant), tool, client, IDE

**Platform**:
An agent product used outside coding: personal assistants, browser or desktop agents, and
hosted agent products.
_Avoid_: bot, app, assistant

**Orchestration**:
Tooling whose purpose is coordinating several agents or sessions with each other.
_Avoid_: swarm tooling, multi-agent (as a noun)

**Second-hand report**:
A statement about someone else's setup rather than the author's own.
_Avoid_: hearsay, anecdote, relayed

**Snapshot**:
One frozen fetch of the thread at a moment in time, with everything derived from it.
_Avoid_: run, scrape, dump

**Extraction run**:
One model's pass over one snapshot producing structured records.
_Avoid_: analysis, parse, enrichment
