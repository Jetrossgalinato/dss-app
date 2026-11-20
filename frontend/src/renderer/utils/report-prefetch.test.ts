import { beforeEach, describe, expect, it, vi } from 'vitest'

import { cacheSize, getCached, invalidateAll } from './api-cache'
import {
  REPORT_CACHE_ENDPOINT,
  defaultDashboardRequest,
  getCachedDashboardReport,
  prefetchDefaultDashboardReport,
  setCachedDashboardReport,
} from './report-prefetch'

describe('report-prefetch', () => {
  beforeEach(() => {
    invalidateAll()
    vi.unstubAllGlobals()
  })

  it('builds the default dashboard request', () => {
    expect(defaultDashboardRequest()).toEqual({
      horizon: 3,
      max_class_size: 25,
      programs: null,
      year_levels: null,
      locations: null,
    })
  })

  it('stores and reads dashboard cache entries', () => {
    const request = defaultDashboardRequest()
    const payload = { summary: { total_forecast: 10 } } as never
    setCachedDashboardReport(request, payload)

    expect(getCachedDashboardReport(request)).toEqual(payload)
    expect(getCached(REPORT_CACHE_ENDPOINT, request)).toEqual(payload)
  })

  it('writes to cache on successful prefetch and skips when already cached', async () => {
    const request = defaultDashboardRequest()
    const payload = { summary: { total_forecast: 42 } } as never
    const getDashboardReport = vi.fn().mockResolvedValue({ ok: true, data: payload })
    vi.stubGlobal('window', { api: { getDashboardReport } })

    await prefetchDefaultDashboardReport()
    expect(getDashboardReport).toHaveBeenCalledTimes(1)
    expect(getCachedDashboardReport(request)).toEqual(payload)

    await prefetchDefaultDashboardReport()
    expect(getDashboardReport).toHaveBeenCalledTimes(1)
    expect(cacheSize()).toBe(1)
  })

  it('does not throw when prefetch fails', async () => {
    const getDashboardReport = vi.fn().mockRejectedValue(new Error('offline'))
    vi.stubGlobal('window', { api: { getDashboardReport } })

    await expect(prefetchDefaultDashboardReport()).resolves.toBeUndefined()
    expect(cacheSize()).toBe(0)
  })

  it('does not cache unsuccessful prefetch responses', async () => {
    const getDashboardReport = vi
      .fn()
      .mockResolvedValue({ ok: false, error: { message: 'no data', errors: [] } })
    vi.stubGlobal('window', { api: { getDashboardReport } })

    await prefetchDefaultDashboardReport()
    expect(getCachedDashboardReport()).toBeUndefined()
  })
})
