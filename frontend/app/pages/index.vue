<script setup lang="ts">
import type { FleetSummaryResponse } from '~/types/aeroguard'

const api = useAeroGuardApi()

const warningThreshold = ref<number>(45)
const criticalThreshold = ref<number>(20)

const resetThresholds = () => {
  warningThreshold.value = 45
  criticalThreshold.value = 20
}

const { data: fleet, status, error, refresh } = await useAsyncData<FleetSummaryResponse>(
  'fleet-summary',
  () => api.getFleetSummary(warningThreshold.value, criticalThreshold.value),
  {
    watch: [warningThreshold, criticalThreshold]
  }
)

const isLoading = computed(() => status.value === 'pending')

const dynamicTitle = computed(() => {
  const count = fleet.value?.engine_count || 100
  return `Fleet Command Center — ${count} Turbofan Units (FD001 Test Set)`
})

const narrativeText = computed(() => {
  if (!fleet.value) return 'Loading fleet telemetry and RUL predictions from backend...'
  const crit = fleet.value.critical_count ?? 0
  const warn = fleet.value.warning_count ?? 0
  const healthy = fleet.value.healthy_count ?? 0
  const med = fleet.value.rul_stats?.median?.toFixed(1) ?? '87.3'
  return `Fleet inspection posture: ${crit} units require expedited priority teardown (<${criticalThreshold.value} cycles RUL), ${warn} units are in advisory inspection window (${criticalThreshold.value}–${warningThreshold.value} cycles), and ${healthy} units maintain nominal health margin. Fleet median RUL is ${med} cycles.`
})

const narrativeTone = computed(() => {
  if (!fleet.value) return 'neutral'
  if ((fleet.value.critical_count || 0) > 0) return 'critical'
  if ((fleet.value.warning_count || 0) > 0) return 'warning'
  return 'info'
})
</script>

<template>
  <UDashboardPanel id="fleet-command">
    <template #header>
      <UDashboardNavbar :title="dynamicTitle" :ui="{ right: 'gap-3' }">
        <template #leading>
          <UDashboardSidebarCollapse />
        </template>

        <template #right>
          <div class="flex items-center gap-2">
            <DataQualityModal />

            <UBadge color="neutral" variant="outline" class="font-mono text-xs hidden sm:inline-flex">
              HGB Regressor
            </UBadge>

            <UButton
              icon="i-lucide-refresh-cw"
              color="neutral"
              variant="outline"
              size="sm"
              :loading="isLoading"
              @click="() => refresh()"
            >
              Refresh
            </UButton>
          </div>
        </template>
      </UDashboardNavbar>

      <UDashboardToolbar>
        <template #left>
          <div class="flex flex-wrap items-center gap-4 text-xs text-slate-300">
            <div class="flex items-center gap-2">
              <span class="font-medium text-slate-400">Warning Threshold:</span>
              <UInput
                v-model.number="warningThreshold"
                type="number"
                size="xs"
                class="w-20 font-mono"
                min="25"
                max="80"
              />
              <span class="text-slate-500">cycles</span>
            </div>

            <div class="flex items-center gap-2">
              <span class="font-medium text-slate-400">Critical Threshold:</span>
              <UInput
                v-model.number="criticalThreshold"
                type="number"
                size="xs"
                class="w-20 font-mono"
                min="5"
                max="40"
              />
              <span class="text-slate-500">cycles</span>
            </div>

            <UButton
              size="xs"
              color="neutral"
              variant="ghost"
              icon="i-lucide-rotate-ccw"
              @click="resetThresholds"
            >
              Reset Thresholds
            </UButton>
          </div>
        </template>

        <template #right>
          <span class="text-[11px] text-slate-400 hidden md:inline">
            Historical NASA C-MAPSS FD001 Dataset — Model-Generated Estimates
          </span>
        </template>
      </UDashboardToolbar>
    </template>

    <template #body>
      <div class="space-y-6 shrink-0">
        <!-- Error State -->
      <UAlert
        v-if="error"
        color="error"
        variant="subtle"
        icon="i-lucide-alert-octagon"
        title="Fleet Telemetry API Offline"
        :description="error.message || 'Unable to connect to the FastAPI backend at http://localhost:8000.'"
        class="mb-6"
      >
        <template #actions>
          <UButton color="error" variant="solid" size="xs" @click="() => refresh()">
            Retry Connection
          </UButton>
        </template>
      </UAlert>

      <!-- Smart Narrative Summary Block -->
      <div class="mb-6">
        <SmartNarrative
          title="Fleet Health & Dispatch Decision Directive"
          :narrative="narrativeText"
          action-hint="Prioritize non-destructive eddy-current and borescope inspections for top critical units in shop hangar."
          badge-text="NASA C-MAPSS FD001"
          :tone="narrativeTone"
        />
      </div>

      <!-- KPI Summary Cards (Yafa-UI Standard) -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <YafaKpiCard
          title="Monitored Fleet"
          tooltip="Total active turbofan engine assets evaluated in the NASA C-MAPSS FD001 held-out test cohort."
          :value="fleet?.engine_count ?? 100"
          unit="Turbofan Units"
          accent-color="#64748b"
          :comparison="`Coverage: ${(fleet?.total_cycles ?? 13096).toLocaleString()} operating cycles`"
        />

        <YafaKpiCard
          title="Critical Priority"
          :tooltip="`Engines with predicted Remaining Useful Life below ${criticalThreshold} cycles requiring immediate maintenance intervention.`"
          :value="fleet?.critical_count ?? '--'"
          unit="Engines"
          accent-color="#ef4444"
          status-type="critical"
          status-label="Immediate Action"
          :comparison="`Threshold: < ${criticalThreshold} cycles`"
        />

        <YafaKpiCard
          title="Maintenance Advisory"
          :tooltip="`Engines with predicted RUL between ${criticalThreshold} and ${warningThreshold} cycles recommended for scheduled shop visit.`"
          :value="fleet?.warning_count ?? '--'"
          unit="Engines"
          accent-color="#f59e0b"
          status-type="warning"
          status-label="Advisory Review"
          :comparison="`Threshold: ${criticalThreshold}–${warningThreshold} cycles`"
        />

        <YafaKpiCard
          title="Nominal Operating State"
          :tooltip="`Engines with predicted RUL exceeding ${warningThreshold} cycles operating safely within acceptable durability boundaries.`"
          :value="fleet?.healthy_count ?? '--'"
          unit="Engines"
          accent-color="#10b981"
          status-type="nominal"
          status-label="Nominal Safe Band"
          :comparison="`Median RUL: ${fleet?.rul_stats?.median?.toFixed(1) ?? '--'} cycles`"
        />
      </div>

      <!-- Fleet Analytics Row -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <!-- RUL Distribution Histogram -->
        <UCard class="lg:col-span-2 border border-slate-800 bg-slate-900/60">
          <template #header>
            <div class="flex items-center justify-between">
              <div>
                <h3 class="text-sm font-semibold text-slate-100 flex items-center gap-2">
                  <UIcon name="i-lucide-bar-chart-3" class="size-4 text-teal-400" />
                  Remaining Useful Life (RUL) Distribution
                </h3>
                <p class="text-xs text-slate-400">Terminal predicted cycle distribution across 100 test fleet engines</p>
              </div>
              <span class="text-xs font-mono text-slate-400 tabular-nums">
                Mean: {{ fleet?.rul_stats?.mean?.toFixed(1) ?? '--' }}c | Std: {{ fleet?.rul_stats?.std?.toFixed(1) ?? '--' }}c
              </span>
            </div>
          </template>

          <div v-if="fleet?.histogram" class="space-y-3 py-2">
            <div
              v-for="bin in fleet.histogram"
              :key="bin.label"
              class="flex items-center gap-3 text-xs"
            >
              <span class="w-16 font-mono text-slate-400 shrink-0 text-right tabular-nums">{{ bin.label }}</span>
              <div class="flex-1 bg-slate-950 rounded-full h-4 overflow-hidden border border-slate-800 flex items-center px-0.5">
                <div
                  class="h-2.5 rounded-full transition-all duration-500"
                  :class="[
                    bin.bin_start < criticalThreshold ? 'bg-red-500' :
                    bin.bin_start < warningThreshold ? 'bg-amber-500' : 'bg-emerald-500'
                  ]"
                  :style="{ width: `${Math.max((bin.count / (fleet?.engine_count || 100)) * 100, bin.count > 0 ? 3 : 0)}%` }"
                />
              </div>
              <span class="w-16 font-mono font-medium text-slate-200 text-right tabular-nums">{{ bin.count }} units</span>
            </div>
          </div>
          <div v-else class="h-44 flex items-center justify-center text-slate-500 text-sm">
            Ingesting fleet distribution telemetry…
          </div>
        </UCard>

        <!-- Status Breakdown Donut/Summary -->
        <UCard class="border border-slate-800 bg-slate-900/60">
          <template #header>
            <h3 class="text-sm font-semibold text-slate-100 flex items-center gap-2">
              <UIcon name="i-lucide-pie-chart" class="size-4 text-teal-400" />
              Fleet Health Status
            </h3>
            <p class="text-xs text-slate-400">Current categorization under configured thresholds</p>
          </template>

          <div v-if="fleet" class="space-y-3.5 py-1">
            <div class="p-3 rounded-lg bg-slate-950/80 border border-slate-800 flex items-center justify-between">
              <div class="flex items-center gap-2.5">
                <span class="size-2 rounded-full bg-red-400 shrink-0"></span>
                <div>
                  <div class="text-xs font-semibold text-slate-200">Critical Priority</div>
                  <div class="text-[10px] text-slate-400 font-mono">RUL &lt; {{ criticalThreshold }} cycles</div>
                </div>
              </div>
              <span class="text-xl font-bold font-mono text-red-400 tabular-nums">{{ fleet.critical_count }}</span>
            </div>

            <div class="p-3 rounded-lg bg-slate-950/80 border border-slate-800 flex items-center justify-between">
              <div class="flex items-center gap-2.5">
                <span class="size-2 rounded-full bg-amber-400 shrink-0"></span>
                <div>
                  <div class="text-xs font-semibold text-slate-200">Advisory Warning</div>
                  <div class="text-[10px] text-slate-400 font-mono">{{ criticalThreshold }} ≤ RUL ≤ {{ warningThreshold }} cycles</div>
                </div>
              </div>
              <span class="text-xl font-bold font-mono text-amber-400 tabular-nums">{{ fleet.warning_count }}</span>
            </div>

            <div class="p-3 rounded-lg bg-slate-950/80 border border-slate-800 flex items-center justify-between">
              <div class="flex items-center gap-2.5">
                <span class="size-2 rounded-full bg-emerald-400 shrink-0"></span>
                <div>
                  <div class="text-xs font-semibold text-slate-200">Nominal Operation</div>
                  <div class="text-[10px] text-slate-400 font-mono">RUL &gt; {{ warningThreshold }} cycles</div>
                </div>
              </div>
              <span class="text-xl font-bold font-mono text-emerald-400 tabular-nums">{{ fleet.healthy_count }}</span>
            </div>

            <div class="pt-2 border-t border-slate-800/80 text-[11px] text-slate-400 space-y-1.5">
              <div class="flex justify-between">
                <span>Min Lifespan Observed:</span>
                <span class="font-mono text-slate-300 tabular-nums">{{ fleet.min_cycles }} cycles</span>
              </div>
              <div class="flex justify-between">
                <span>Max Lifespan Observed:</span>
                <span class="font-mono text-slate-300 tabular-nums">{{ fleet.max_cycles }} cycles</span>
              </div>
              <div class="flex justify-between">
                <span>Mean Trajectory Length:</span>
                <span class="font-mono text-slate-300 tabular-nums">{{ fleet.avg_trajectory_length }} cycles</span>
              </div>
            </div>
          </div>
        </UCard>
      </div>

      <!-- Priority Review Queue Table -->
      <UCard class="border border-slate-800 bg-slate-900/60">
        <template #header>
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-sm font-semibold text-slate-100 flex items-center gap-2">
                <UIcon name="i-lucide-list-ordered" class="size-4 text-teal-400" />
                Priority Engine Triage Queue
              </h3>
              <p class="text-xs text-slate-400">Most degraded turbofan units requiring immediate engineering evaluation</p>
            </div>
            <UButton
              to="/maintenance"
              variant="outline"
              color="neutral"
              size="xs"
              trailing-icon="i-lucide-arrow-right"
            >
              Full Maintenance Queue
            </UButton>
          </div>
        </template>

        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs border-collapse">
            <thead>
              <tr class="border-b border-slate-800 text-slate-400 uppercase tracking-wider font-medium text-[11px]">
                <th class="py-2.5 px-4">Engine ID</th>
                <th class="py-2.5 px-4">Observed Cycle</th>
                <th class="py-2.5 px-4">Predicted RUL</th>
                <th class="py-2.5 px-4">Advisory Severity</th>
                <th class="py-2.5 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-800/60">
              <tr
                v-for="item in fleet?.priority_engines"
                :key="item.engine_id"
                class="hover:bg-slate-800/40 transition-colors"
              >
                <td class="py-2.5 px-4 font-semibold text-slate-200 font-mono">
                  Unit #{{ item.engine_id }}
                </td>
                <td class="py-2.5 px-4 text-slate-300 font-mono tabular-nums">
                  Cycle {{ item.last_cycle }}
                </td>
                <td class="py-2.5 px-4 font-mono tabular-nums font-bold" :class="item.predicted_rul < criticalThreshold ? 'text-red-400' : item.predicted_rul < warningThreshold ? 'text-amber-400' : 'text-emerald-400'">
                  {{ item.predicted_rul.toFixed(1) }} cycles
                </td>
                <td class="py-2.5 px-4">
                  <!-- Anti-capsule: 6px semantic dot + neutral text -->
                  <div class="inline-flex items-center gap-2">
                    <span
                      class="size-1.5 rounded-full shrink-0"
                      :class="[
                        item.status === 'critical' ? 'bg-red-400' :
                        item.status === 'warning' ? 'bg-amber-400' : 'bg-emerald-400'
                      ]"
                    />
                    <span class="text-xs text-slate-300 capitalize font-medium">
                      {{ item.status }}
                    </span>
                  </div>
                </td>
                <td class="py-2.5 px-4 text-right">
                  <UButton
                    :to="`/engines?id=${item.engine_id}`"
                    size="xs"
                    color="neutral"
                    variant="outline"
                    trailing-icon="i-lucide-activity"
                  >
                    Digital Twin
                  </UButton>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </UCard>
    </div>
  </template>
</UDashboardPanel>
</template>
