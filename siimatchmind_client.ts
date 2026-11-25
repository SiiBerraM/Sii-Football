export const SPORT_CATEGORIES = [
  "world-football",
  "basketball",
  "motorsport",
  "tennis",
  "amputee-football",
  "blind-football",
  "cp-football",
  "multi-sport",
] as const;

export type SportCategory = (typeof SPORT_CATEGORIES)[number];
export type DataSourceMode = "network" | "cache";

export interface ApiEnvelope<T> {
  data: T;
  updatedAt: string | null;
  source: DataSourceMode;
  isStale: boolean;
}

export interface CategoryItem {
  category?: string;
  [key: string]: unknown;
}

const DEFAULT_BASE_URL = "https://raw.githubusercontent.com/SiiBerraM/Sii-Football/main/api";

export function normalizeSportCategory(category: string): SportCategory {
  const normalized = category.trim().toLowerCase() as SportCategory;
  if (!SPORT_CATEGORIES.includes(normalized)) {
    throw new Error(`Unsupported sport category: ${category}`);
  }
  return normalized;
}

export function filterByCategory<T extends CategoryItem>(
  items: T[] | null | undefined,
  category: SportCategory | string
): T[] {
  const target = normalizeSportCategory(category);
  if (!Array.isArray(items)) return [];
  return items.filter((item) => (item?.category || "").toLowerCase() === target);
}

export async function fetchApiEndpoint<T extends Record<string, unknown>>(
  endpoint: string,
  options?: {
    baseUrl?: string;
    cacheKeyPrefix?: string;
    maxAgeMs?: number;
  }
): Promise<ApiEnvelope<T>> {
  const cleanEndpoint = endpoint.replace(/^\/+/, "");
  const baseUrl = (options?.baseUrl || DEFAULT_BASE_URL).replace(/\/+$/, "");
  const url = `${baseUrl}/${cleanEndpoint}`;
  const cacheKey = `${options?.cacheKeyPrefix || "siimatchmind_api"}:${cleanEndpoint}`;
  const maxAgeMs = options?.maxAgeMs ?? 6 * 60 * 60 * 1000;

  let cachedRaw: string | null = null;
  try {
    cachedRaw = globalThis.localStorage?.getItem(cacheKey) ?? null;
  } catch {
    cachedRaw = null;
  }

  try {
    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const payload = (await res.json()) as T;
    const updatedAt = typeof payload.updated_at === "string" ? payload.updated_at : null;
    try {
      globalThis.localStorage?.setItem(
        cacheKey,
        JSON.stringify({ payload, updatedAt, cachedAt: Date.now() })
      );
    } catch {
      // Ignore storage quota/environment errors
    }
    return {
      data: payload,
      updatedAt,
      source: "network",
      isStale: false,
    };
  } catch {
    if (cachedRaw) {
      const parsed = JSON.parse(cachedRaw) as {
        payload: T;
        updatedAt?: string | null;
        cachedAt?: number;
      };
      const age = parsed.cachedAt ? Date.now() - parsed.cachedAt : maxAgeMs + 1;
      return {
        data: parsed.payload,
        updatedAt: parsed.updatedAt ?? (typeof parsed.payload?.updated_at === "string" ? parsed.payload.updated_at : null),
        source: "cache",
        isStale: age > maxAgeMs,
      };
    }
    throw new Error(`Failed to fetch ${url} and no cache available`);
  }
}

export async function fetchFilteredEndpointByCategory<T extends CategoryItem>(
  endpoint: string,
  listKey: string,
  category: SportCategory | string,
  options?: {
    baseUrl?: string;
    cacheKeyPrefix?: string;
    maxAgeMs?: number;
  }
): Promise<ApiEnvelope<T[]> & { category: SportCategory }> {
  const target = normalizeSportCategory(category);
  const envelope = await fetchApiEndpoint<Record<string, unknown>>(endpoint, options);
  const rawList = envelope.data[listKey] as T[] | undefined;
  return {
    data: filterByCategory<T>(rawList, target),
    updatedAt: envelope.updatedAt,
    source: envelope.source,
    isStale: envelope.isStale,
    category: target,
  };
}
