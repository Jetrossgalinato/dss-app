import type { ElectronAPI } from '@electron-toolkit/preload'
import type { EnrollmentApi } from '../shared/enrollment'

declare global {
  interface Window {
    electron: ElectronAPI
    api: EnrollmentApi
  }
}

export {}
