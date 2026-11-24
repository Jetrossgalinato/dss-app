<template>
  <aside
    class="rounded-xl border border-blue-100 bg-blue-50 px-4 py-3 text-sm text-slate-700"
    aria-labelledby="how-forecasts-work-title"
  >
    <div class="flex gap-3">
      <svg
        aria-hidden="true"
        class="mt-0.5 h-5 w-5 shrink-0 text-blue-700"
        viewBox="0 0 24 24"
        fill="none"
      >
        <circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="1.75" />
        <path
          d="M12 11v5M12 8h.01"
          stroke="currentColor"
          stroke-width="1.75"
          stroke-linecap="round"
        />
      </svg>
      <div class="min-w-0">
        <h3 id="how-forecasts-work-title" class="font-semibold text-blue-900">
          How forecasts work
        </h3>
        <ul class="mt-1.5 list-disc space-y-1 pl-4 text-slate-700">
          <li>
            Forecasts project total enrollment for each program, year level, and
            location using historical Male and Female totals.
          </li>
          <li>
            Series with enough continuous history use ARIMA; shorter or gapped
            series use a linear trend.
          </li>
          <li>
            Recommended sections divide each forecast by the maximum class size
            (rounded up). Planned class size is the resulting average load.
          </li>
          <li>Results are computed on demand and are not saved.</li>
        </ul>
      </div>
    </div>
  </aside>
</template>
