type CacheKey = string

const store = new Map<CacheKey, unknown>()

export function buildCacheKey(endpoint: string, params: unknown = null): CacheKey {
  return `${endpoint}:${JSON.stringify(params)}`
}

export function getCached<T>(endpoint: string, params: unknown = null): T | undefined {
  return store.get(buildCacheKey(endpoint, params)) as T | undefined
}

export function setCached<T>(endpoint: string, params: unknown, value: T): void {
  store.set(buildCacheKey(endpoint, params), value)
}

export function invalidateAll(): void {
  store.clear()
}

export function cacheSize(): number {
  return store.size
}
