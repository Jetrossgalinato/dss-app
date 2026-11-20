import { beforeEach, describe, expect, it } from 'vitest'

import {
  buildCacheKey,
  cacheSize,
  getCached,
  invalidateAll,
  setCached,
} from './api-cache'

describe('api-cache', () => {
  beforeEach(() => {
    invalidateAll()
  })

  it('stores and retrieves values by endpoint and params', () => {
    const params = { horizon: 3, programs: ['BSIT'] }
    setCached('reports/dashboard', params, { total: 10 })

    expect(getCached('reports/dashboard', params)).toEqual({ total: 10 })
    expect(getCached('reports/dashboard', { horizon: 2 })).toBeUndefined()
    expect(cacheSize()).toBe(1)
  })

  it('builds stable keys', () => {
    expect(buildCacheKey('enrollments/list', { page: 1 })).toBe(
      'enrollments/list:{"page":1}',
    )
  })

  it('clears all entries on invalidate', () => {
    setCached('a', null, 1)
    setCached('b', { x: 1 }, 2)
    expect(cacheSize()).toBe(2)

    invalidateAll()
    expect(cacheSize()).toBe(0)
    expect(getCached('a')).toBeUndefined()
  })
})
