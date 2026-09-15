import { contextBridge } from 'electron'
import { electronAPI } from '@electron-toolkit/preload'

const BACKEND_HEALTH_URL = 'http://127.0.0.1:8000/health'

export type HealthResult =
  | { ok: true; status: string }
  | { ok: false; error: string }

const api = {
  getBackendHealth: async (): Promise<HealthResult> => {
    try {
      const response = await fetch(BACKEND_HEALTH_URL)
      if (!response.ok) {
        return { ok: false, error: `HTTP ${response.status}` }
      }
      const data = (await response.json()) as { status?: string }
      return { ok: true, status: data.status ?? 'unknown' }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Request failed'
      return { ok: false, error: message }
    }
  }
}

contextBridge.exposeInMainWorld('electron', electronAPI)
contextBridge.exposeInMainWorld('api', api)
