import { createRouter, createWebHashHistory } from 'vue-router'

import EnrollmentDataView from '../views/EnrollmentDataView.vue'
import ReportsDashboardView from '../views/ReportsDashboardView.vue'

export const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    {
      path: '/',
      name: 'enrollment',
      component: EnrollmentDataView,
      meta: {
        title: 'Enrollment data',
        description: 'Upload and manage historical enrollment totals used by forecasting.',
      },
    },
    {
      path: '/reports',
      name: 'reports',
      component: ReportsDashboardView,
      meta: {
        title: 'Reports dashboard',
        description: 'Explore historical enrollment, forecasts, and section recommendations.',
      },
    },
  ],
})
