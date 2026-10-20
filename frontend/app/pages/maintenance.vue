<script setup lang="ts">
import type { MaintenanceItem } from '~/types/aeroguard'

const api = useAeroGuardApi()

const warningThreshold = ref<number>(45)
const criticalThreshold = ref<number>(20)
const statusFilter = ref<'all' | 'critical' | 'warning' | 'healthy'>('all')
const searchQuery = ref<string>('')
const sortAscending = ref<boolean>(true)

const resetFilters = () => {
  warningThreshold.value = 45
  criticalThreshold.value = 20
  statusFilter.value = 'all'
  searchQuery.value = ''
  sortAscending.value = true
}

const { data: queueData, status, error, refresh } = await useAsyncData<MaintenanceItem[]>(
  'maintenance-queue',
  () => api.getMaintenanceQueue(warningThreshold.value, criticalThreshold.value, statusFilter.value),
  {
    watch: [warningThreshold, criticalThreshold, statusFilter]
  }
)

const rawItems = computed(() => {
  if (!queueData.value) return []
  return Array.isArray(queueData.value) ? queueData.value : ((queueData.value as any)?.items || [])
})

const totalCount = computed(() => rawItems.value.length)
const criticalCount = computed(() => rawItems.value.filter(it => (it.predicted_rul ?? it.pred_rul) < criticalThreshold.value).length)
const warningCount = computed(() => rawItems.value.filter(it => {
  const r = it.predicted_rul ?? it.pred_rul
  return r >= criticalThreshold.value && r <= warningThreshold.value
}).length)
const healthyCount = computed(() => rawItems.value.filter(it => (it.predicted_rul ?? it.pred_rul) > warningThreshold.value).length)

const filteredItems = computed(() => {
  let items = [...rawItems.value]

  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase().trim()
    items = items.filter(it =>
      String(it.engine_id).includes(q) ||
      (it.reason || it.rationale || '').toLowerCase().includes(q) ||
      (it.status || it.health_status || '').toLowerCase().includes(q) ||
      (it.action || it.action_recommendation || '').toLowerCase().includes(q)
    )
  }

  items.sort((a, b) => {
    const valA = a.predicted_rul ?? a.pred_rul ?? 0
    const valB = b.predicted_rul ?? b.pred_rul ?? 0
    return sortAscending.value ? valA - valB : valB - valA
  })

  return items
})

const exportUrl = computed(() => {
  return api.getExportUrl(warningThreshold.value, criticalThreshold.value, statusFilter.value)
})

const dynamicTitle = computed(() => {
  return `Maintenance Operations & Triage — ${filteredItems.value.length} Work Orders (${criticalCount.value} Critical Priority)`
})

const narrativeText = computed(() => {
  return `Priority maintenance triage queue: ${criticalCount.value} turbofan engines require immediate shop floor teardown (<${criticalThreshold.value} cycles RUL). ${warningCount.value} engines are flagged for scheduled inspection (${criticalThreshold.value}–${warningThreshold.value} cycles), while ${healthyCount.value} units remain in nominal service buffer. Orders are sorted by ascending estimated remaining cycle life.`
})

const narrativeTone = computed(() => {
  if (criticalCount.value > 0) return 'critical'
  if (warningCount.value > 0) return 'warning'
  return 'info'
})
</script>

<template>
  <UDashboardPanel id="maintenance-ops">
    <template #header>
      <UDashboardNavbar :title="dynamicTitle" :ui="{ right: 'gap-3' }">
        <template #leading>
          <UDashboardSidebarCollapse />
        </template>

        <template #right>
          <div class="flex items-center gap-2">
            <DataQualityModal />

            <!-- Direct CSV Download Button (Rectangular Yafa Action) -->
            <a
              :href="exportUrl"
              download="aeroguard_maintenance_queue.csv"
              class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-200 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-md transition-colors focus-visible:ring-2 focus-visible:ring-teal-500"
            >
              <UIcon name="i-lucide-download" class="size-3.5 text-teal-400" />
              <span>Export CSV</span>
            </a>

            <UButton
              icon="i-lucide-refresh-cw"
              color="neutral"
              variant="outline"
              size="sm"
              :loading="status === 'pending'"
              @click="() => refresh()"
            >
              Sync
            </UButton>
          </div>
        </template>
      </UDashboardNavbar>

      <UDashboardToolbar>
        <template #left>
          <div class="flex flex-wrap items-center gap-3">
            <!-- Status filters -->
            <div class="flex items-center gap-1">
              <UButton
                size="xs"
                :variant="statusFilter === 'all' ? 'solid' : 'ghost'"
                :color="statusFilter === 'all' ? 'primary' : 'neutral'"
                @click="statusFilter = 'all'"
              >
                All ({{ totalCount }})
              </UButton>
              <UButton
                size="xs"
                :variant="statusFilter === 'critical' ? 'solid' : 'ghost'"
                :color="statusFilter === 'critical' ? 'primary' : 'neutral'"
                @click="statusFilter = 'critical'"
              >
                Critical ({{ criticalCount }})
              </UButton>
              <UButton
                size="xs"
                :variant="statusFilter === 'warning' ? 'solid' : 'ghost'"
                :color="statusFilter === 'warning' ? 'primary' : 'neutral'"
                @click="statusFilter = 'warning'"
              >
                Advisory ({{ warningCount }})
              </UButton>
              <UButton
                size="xs"
                :variant="statusFilter === 'healthy' ? 'solid' : 'ghost'"
                :color="statusFilter === 'healthy' ? 'primary' : 'neutral'"
                @click="statusFilter = 'healthy'"
              >
                Nominal ({{ healthyCount }})
              </UButton>
            </div>

            <!-- Filter Search -->
            <div class="border-l border-slate-800 pl-3">
              <UInput
                v-model="searchQuery"
                icon="i-lucide-search"
                placeholder="Filter by engine #, action, reason…"
                size="xs"
                class="w-56"
              />
            </div>

            <UButton
              size="xs"
              color="neutral"
              variant="ghost"
              icon="i-lucide-rotate-ccw"
              @click="resetFilters"
            >
              Reset Filters
            </UButton>
          </div>
        </template>

        <template #right>
          <div class="flex items-center gap-3 text-xs text-slate-400">
            <div class="flex items-center gap-1.5">
              <span>Warn:</span>
              <input
                v-model.number="warningThreshold"
                type="number"
                min="20"
                max="80"
                class="w-14 bg-slate-900 border border-slate-700 rounded px-1.5 py-0.5 text-xs font-mono text-slate-200"
              />
              <span class="text-slate-500">c</span>
            </div>
            <div class="flex items-center gap-1.5">
              <span>Crit:</span>
              <input
                v-model.number="criticalThreshold"
                type="number"
                min="5"
                max="40"
                class="w-14 bg-slate-900 border border-slate-700 rounded px-1.5 py-0.5 text-xs font-mono text-slate-200"
              />
              <span class="text-slate-500">c</span>
            </div>
          </div>
        </template>
      </UDashboardToolbar>
    </template>

    <template #body>
      <div class="space-y-6 shrink-0">
        <!-- Error banner -->
      <UAlert
        v-if="error"
        color="error"
        variant="subtle"
        title="Maintenance API Error"
        :description="error.message"
        class="mb-6"
      />

      <!-- Smart Decision Narrative -->
      <div class="mb-6">
        <SmartNarrative
          title="Maintenance Dispatch Directive"
          :narrative="narrativeText"
          action-hint="Issue immediate shop work orders for Critical units; stage spare turbine blades and HPC seal kits in hangar bay."
          badge-text="NASA C-MAPSS FD001"
          :tone="narrativeTone"
        />
      </div>

      <!-- KPI Summary Cards (Yafa-UI Standard) -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <YafaKpiCard
          title="Queue Coverage"
          tooltip="Total turbofan units actively monitored and prioritized in maintenance queue."
          :value="totalCount"
          unit="Turbofan Units"
          accent-color="#64748b"
          comparison="Full held-out test cohort"
        />

        <YafaKpiCard
          title="Immediate Teardown"
          :tooltip="`Engines with predicted RUL below ${criticalThreshold} cycles requiring immediate hangar intake.`"
          :value="criticalCount"
          unit="Work Orders"
          accent-color="#ef4444"
          status-type="critical"
          status-label="Immediate Priority"
          :comparison="`Threshold: < ${criticalThreshold} cycles`"
        />

        <YafaKpiCard
          title="Scheduled Overhaul"
          :tooltip="`Engines with predicted RUL between ${criticalThreshold} and ${warningThreshold} cycles staged for regular line maintenance.`"
          :value="warningCount"
          unit="Work Orders"
          accent-color="#f59e0b"
          status-type="warning"
          status-label="Advisory Window"
          :comparison="`Threshold: ${criticalThreshold}–${warningThreshold} cycles`"
        />

        <YafaKpiCard
          title="Nominal Turnaround"
          :tooltip="`Engines operating with healthy RUL margin (> ${warningThreshold} cycles) cleared for routine turnaround.`"
          :value="healthyCount"
          unit="Nominal Assets"
          accent-color="#10b981"
          status-type="nominal"
          status-label="Normal Service"
          :comparison="`Buffer: > ${warningThreshold} cycles`"
        />
      </div>

      <!-- Maintenance Queue Table Card -->
      <UCard class="border border-slate-800 bg-slate-900/60 mb-6">
        <template #header>
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-sm font-semibold text-slate-100 flex items-center gap-2">
                <UIcon name="i-lucide-clipboard-list" class="size-4 text-teal-400" />
                Fleet Maintenance Priority Review Queue
              </h3>
              <p class="text-xs text-slate-400">Chronological ranking of degradation urgency based on causal ML inference</p>
            </div>

            <div class="flex items-center gap-2">
              <UButton
                size="xs"
                variant="ghost"
                color="neutral"
                :icon="sortAscending ? 'i-lucide-arrow-up-narrow-wide' : 'i-lucide-arrow-down-wide-narrow'"
                @click="sortAscending = !sortAscending"
              >
                Sort RUL ({{ sortAscending ? 'Ascending' : 'Descending' }})
              </UButton>
              <span class="text-xs font-mono text-slate-400 tabular-nums">
                {{ filteredItems.length }} Entries
              </span>
            </div>
          </div>
        </template>

        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs border-collapse">
            <thead>
              <tr class="border-b border-slate-800 text-slate-400 uppercase tracking-wider font-medium text-[11px]">
                <th class="py-2.5 px-3">Unit</th>
                <th class="py-2.5 px-3">Observed Cycle</th>
                <th class="py-2.5 px-3 font-mono">Predicted RUL</th>
                <th class="py-2.5 px-3 font-mono">Ground Truth</th>
                <th class="py-2.5 px-3">Advisory Level</th>
                <th class="py-2.5 px-3">Diagnostic Rationale & Action</th>
                <th class="py-2.5 px-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-800/60">
              <tr
                v-for="item in filteredItems"
                :key="item.engine_id"
                class="hover:bg-slate-800/40 transition-colors"
              >
                <td class="py-3 px-3 font-mono font-semibold text-slate-200">
                  Unit #{{ item.engine_id }}
                </td>
                <td class="py-3 px-3 font-mono text-slate-300 tabular-nums">
                  Cycle {{ item.cycle }}
                </td>
                <td class="py-3 px-3 font-mono tabular-nums font-bold" :class="(item.predicted_rul ?? item.pred_rul) < criticalThreshold ? 'text-red-400' : (item.predicted_rul ?? item.pred_rul) < warningThreshold ? 'text-amber-400' : 'text-emerald-400'">
                  {{ (item.predicted_rul ?? item.pred_rul).toFixed(1) }}c
                </td>
                <td class="py-3 px-3 font-mono text-slate-400 tabular-nums">
                  {{ item.true_rul !== null && item.true_rul !== undefined ? item.true_rul + 'c' : 'N/A' }}
                </td>
                <td class="py-3 px-3">
                  <!-- Anti-capsule: 6px semantic dot + neutral text -->
                  <div class="inline-flex items-center gap-2">
                    <span
                      class="size-1.5 rounded-full shrink-0"
                      :class="[
                        (item.predicted_rul ?? item.pred_rul) < criticalThreshold ? 'bg-red-400' :
                        (item.predicted_rul ?? item.pred_rul) < warningThreshold ? 'bg-amber-400' : 'bg-emerald-400'
                      ]"
                    />
                    <span class="text-xs text-slate-300 capitalize font-medium">
                      {{ item.status || item.health_status }}
                    </span>
                  </div>
                </td>
                <td class="py-3 px-3 max-w-sm">
                  <div class="text-slate-200 font-medium truncate">{{ item.action || item.action_recommendation }}</div>
                  <div class="text-[11px] text-slate-400 truncate">{{ item.reason || item.rationale }}</div>
                </td>
                <td class="py-3 px-3 text-right">
                  <UButton
                    :to="`/engines?id=${item.engine_id}`"
                    size="xs"
                    color="neutral"
                    variant="outline"
                    trailing-icon="i-lucide-activity"
                  >
                    Twin View
                  </UButton>
                </td>
              </tr>
              <tr v-if="filteredItems.length === 0">
                <td colspan="7" class="py-8 text-center text-slate-500 font-mono text-xs">
                  No maintenance records match active query or filter criteria.
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
