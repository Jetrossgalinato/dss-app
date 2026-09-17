import type { ElectronAPI } from '@electron-toolkit/preload'
import type { EnrollmentApi } from '../shared/enrollment'
import type { SectionPlanningApi } from '../shared/section-planning'

declare global {
  interface Window {
    electron: ElectronAPI
    api: EnrollmentApi & SectionPlanningApi
  }
}

export {}
