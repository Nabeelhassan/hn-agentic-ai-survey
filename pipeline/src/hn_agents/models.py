from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Subscription(BaseModel):
    model_config = ConfigDict(extra="ignore")

    node: str
    tier_raw: str | None = None
    count: int = 1
    confidence: float = 0.8


class OutsideModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    node: str
    access: Literal["api", "local", "openrouter", "other"] = "other"
    purpose: str | None = None


class Harness(BaseModel):
    model_config = ConfigDict(extra="ignore")

    node: str
    role: Literal["primary", "secondary"] = "primary"
    switched_from: str | None = None
    switch_reason: str | None = None


class Orchestration(BaseModel):
    model_config = ConfigDict(extra="ignore")

    node: str
    description: str | None = None


class Platform(BaseModel):
    model_config = ConfigDict(extra="ignore")

    node: str
    use_cases: list[str] = Field(default_factory=list)


class Evidence(BaseModel):
    model_config = ConfigDict(extra="ignore")

    field: str
    quote: str


class CommentExtraction(BaseModel):
    model_config = ConfigDict(extra="ignore")

    comment_id: str
    answers_questions: Literal["full", "partial", "none", "meta", "off_topic"]
    q1_subscriptions: list[Subscription] = Field(default_factory=list)
    q1_multi_subscription: bool | None = None
    q2_outside: list[OutsideModel] = Field(default_factory=list)
    q3_harnesses: list[Harness] = Field(default_factory=list)
    q4_orchestration: list[Orchestration] = Field(default_factory=list)
    q5_platforms: list[Platform] = Field(default_factory=list)
    spend_monthly_usd: float | None = None
    second_hand: bool = False
    evidence: list[Evidence] = Field(default_factory=list)
    themes: list[str] = Field(default_factory=list)
    confidence: float = 0.7


class ExtractionBatch(BaseModel):
    model_config = ConfigDict(extra="ignore")

    results: list[CommentExtraction]
