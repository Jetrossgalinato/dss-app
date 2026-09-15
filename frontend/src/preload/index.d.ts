import type { ElectronAPI } from '@electron-toolkit/preload'
import type { HealthResult } from './index'

declare global {
  interface Window {
    electron: ElectronAPI
    api: {
      getBackendHealth: () => Promise<HealthResult>
    }
  }
}

export {}
