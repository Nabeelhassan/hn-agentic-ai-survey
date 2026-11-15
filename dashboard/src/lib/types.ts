export interface BreakdownRow {
  node: string;
  label: string;
  count: number;
  pct: number | null;
  n_denominator: number;
  comment_ids: string[];
}

export interface TierRow {
  node: string;
  label: string;
  tier_raw: string;
  count: number;
  n_denominator: number;
  comment_ids: string[];
}

export interface Story {
  id: number;
  title: string;
  by: string;
  score: number;
  descendants: number;
  time: number;
  url?: string;
}

export interface OverviewData {
  snapshot_id: string;
  generated_at: string;
  story: Story | null;
  comments: number;
  comments_with_text: number;
  top_level_comments: number;
  commenters: number;
  deleted: number;
  dead: number;
  respondents: number;
  second_hand_comments: number;
  answer_distribution: BreakdownRow[];
  notes: string[];
}

export interface SubscriptionsData {
  n_denominator: number;
  n_with_subscription: number;
  providers: BreakdownRow[];
  tiers: TierRow[];
  multi_subscription: BreakdownRow[];
  spend: {
    stated: number;
    values: { author: string; usd: number; comment_ids: string[] }[];
    buckets: { label: string; count: number; n_denominator: number; comment_ids: string[] }[];
  };
}

export interface ModelsData {
  n_denominator: number;
  sources: BreakdownRow[];
  models: BreakdownRow[];
  access: BreakdownRow[];
  local_share: BreakdownRow | null;
}

export interface Migration {
  from: string;
  from_label: string;
  to: string;
  to_label: string;
  author: string;
  comment_ids: string[];
}

export interface HarnessesData {
  n_denominator: number;
  adoption: BreakdownRow[];
  primary: BreakdownRow[];
  migrations: Migration[];
  switch_reasons: {
    node: string;
    reason: string;
    author: string;
    comment_ids: string[];
  }[];
}

export interface OrchestrationData {
  n_denominator: number;
  orchestration: BreakdownRow[];
  platforms: BreakdownRow[];
  platform_use_cases: Record<string, string[]>;
  orchestration_users: string[];
}

export interface ThemesData {
  n_denominator: number;
  themes: {
    theme: string;
    count: number;
    n_denominator: number;
    comment_ids: string[];
  }[];
}

export interface CooccurrenceData {
  nodes: { node: string; label: string; count: number }[];
  edges: {
    a: string;
    a_label: string;
    b: string;
    b_label: string;
    count: number;
    comment_ids: string[];
  }[];
}

export interface ExplorerRow {
  author: string;
  n_comments: number;
  answers: { full: number; partial: number };
  subscriptions: {
    node: string;
    label: string;
    tier_raw: string | null;
    comment_ids: string[];
  }[];
  outside: { node: string; label: string; access: string }[];
  harnesses: { node: string; label: string; role: string }[];
  orchestration: { node: string; label: string }[];
  platforms: { node: string; label: string }[];
  spend_monthly_usd: number | null;
  comment_ids: string[];
  first_comment_url: string | null;
  has_conflict: boolean;
}

export interface ExplorerData {
  rows: ExplorerRow[];
  n_denominator: number;
}

export interface MethodologyData {
  snapshot_id: string;
  generated_at: string;
  story_url: string;
  taxonomy: {
    version: string;
    nodes: { id: string; label: string; category: string; aliases?: string[] }[];
  };
  extraction: {
    runs: {
      model: string;
      records_written: number;
      cost_usd: number;
      usage: Record<string, number>;
    }[];
    records: number;
    comments_extracted: number;
    review_items: number;
    total_cost_usd: number;
  } | null;
  normalize: Record<string, unknown> | null;
  merge: Record<string, unknown> | null;
  eval: {
    gold_cases: number;
    evaluated: number;
    answers_questions_accuracy: number | null;
    fields: Record<string, { label: string; precision: number | null; recall: number | null; f1: number | null }>;
    misses: { comment_id: string; field: string; expected: string[]; predicted: string[] }[];
  } | null;
  conventions: string[];
}

export interface Dataset {
  overview: OverviewData;
  subscriptions: SubscriptionsData;
  models: ModelsData;
  harnesses: HarnessesData;
  orchestration: OrchestrationData;
  themes: ThemesData;
  cooccurrence: CooccurrenceData;
  explorer: ExplorerData;
  methodology: MethodologyData;
}
