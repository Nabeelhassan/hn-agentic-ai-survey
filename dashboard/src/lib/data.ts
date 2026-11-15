import type {
  CooccurrenceData,
  Dataset,
  ExplorerData,
  HarnessesData,
  MethodologyData,
  ModelsData,
  OrchestrationData,
  OverviewData,
  SubscriptionsData,
  ThemesData,
} from "./types";

const BASE = import.meta.env.BASE_URL;

async function loadJson<T>(name: string): Promise<T> {
  const response = await fetch(`${BASE}data/${name}.json`);
  if (!response.ok) {
    throw new Error(`Could not load ${name}.json (${response.status}). Run \`make dashboard-data\`.`);
  }
  return (await response.json()) as T;
}

export async function loadDataset(): Promise<Dataset> {
  const [
    overview,
    subscriptions,
    models,
    harnesses,
    orchestration,
    themes,
    cooccurrence,
    explorer,
    methodology,
  ] = await Promise.all([
    loadJson<OverviewData>("overview"),
    loadJson<SubscriptionsData>("subscriptions"),
    loadJson<ModelsData>("models"),
    loadJson<HarnessesData>("harnesses"),
    loadJson<OrchestrationData>("orchestration"),
    loadJson<ThemesData>("themes"),
    loadJson<CooccurrenceData>("cooccurrence"),
    loadJson<ExplorerData>("explorer"),
    loadJson<MethodologyData>("methodology"),
  ]);
  return {
    overview,
    subscriptions,
    models,
    harnesses,
    orchestration,
    themes,
    cooccurrence,
    explorer,
    methodology,
  };
}

export const commentUrl = (id: string) => `https://news.ycombinator.com/item?id=${id}`;
