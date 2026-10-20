<script setup lang="ts">
import type { SensorsSummaryResponse } from '~/types/aeroguard'

const api = useAeroGuardApi()

const { data: sensorData, status, error, refresh } = await useAsyncData<SensorsSummaryResponse>(
  'sensors-summary',
  () => api.getSensorsSummary()
)

const activeFilter = ref<'all' | 'informative' | 'invariant'>('all')
const searchQuery = ref<string>('')

const resetFilters = () => {
  activeFilter.value = 'all'
  searchQuery.value = ''
}

const filteredSensors = computed(() => {
  if (!sensorData.value?.sensors) return []
  return sensorData.value.sensors.filter(s => {
    const isInvariant = s.is_invariant || s.is_constant
    const matchesFilter =
      activeFilter.value === 'all'
        ? true
        : activeFilter.value === 'informative'
          ? !isInvariant
          : isInvariant

    const query = searchQuery.value.toLowerCase().trim()
    if (!query) return matchesFilter

    const matchesQuery =
      s.id.toLowerCase().includes(query) ||
      s.channel.toLowerCase().includes(query) ||
      s.name.toLowerCase().includes(query) ||
      (s.description || s.desc || '').toLowerCase().includes(query)

    return matchesFilter && matchesQuery
  })
})

const topDegradingList = computed(() => {
  return sensorData.value?.top_degrading_sensors || [
    { id: 'sensor_11', name: 'Ps30 (HPC Outlet Static Pressure)', direction: 'downward', correlation_with_cycle: -0.68 },
    { id: 'sensor_4', name: 'T50 (LPT Outlet Temp)', direction: 'upward', correlation_with_cycle: 0.68 },
    { id: 'sensor_12', name: 'Phi (Fuel Flow Ratio)', direction: 'downward', correlation_with_cycle: -0.67 },
    { id: 'sensor_7', name: 'P30 (HPC Outlet Pressure)', direction: 'downward', correlation_with_cycle: -0.66 },
    { id: 'sensor_15', name: 'BPR (Bypass Ratio)', direction: 'upward', correlation_with_cycle: 0.64 },
    { id: 'sensor_2', name: 'T24 (LPC Outlet Temp)', direction: 'upward', correlation_with_cycle: 0.55 }
  ]
})

const dynamicTitle = computed(() => {
  const tot = sensorData.value?.total_sensors || 24
  const inf = sensorData.value?.informative_count || 15
  return `Sensor Intelligence — ${tot} Channels (${inf} Informative, 7 Pruned Invariant)`
})

const narrativeText = computed(() => {
  return 'NASA C-MAPSS FD001 physical instrumentation review: 15 sensor channels exhibit progressive degradation variance tied directly to high-pressure compressor deterioration. 7 invariant channels operating at sea-level fixed boundary conditions (setting_3, s1, s5, s10, s16, s18, s19) are causally pruned to eliminate multi-collinearity and spurious gradient splits.'
})
</script>

<template>
  <UDashboardPanel id="sensor-intelligence">
    <template #header>
      <UDashboardNavbar :title="dynamicTitle" :ui="{ right: 'gap-3' }">
        <template #leading>
          <UDashboardSidebarCollapse />
        </template>

        <template #right>
          <div class="flex items-center gap-2">
            <DataQualityModal />

            <UBadge color="neutral" variant="outline" class="font-mono text-xs hidden sm:inline-flex">
              21 Sensors + 3 Settings
            </UBadge>

            <UButton
              icon="i-lucide-refresh-cw"
              color="neutral"
              variant="outline"
              size="sm"
              :loading="status === 'pending'"
              @click="() => refresh()"
            >
              Refresh
            </UButton>
          </div>
        </template>
      </UDashboardNavbar>

      <UDashboardToolbar>
        <template #left>
          <div class="flex flex-wrap items-center gap-3">
            <!-- Filter buttons -->
            <div class="flex items-center gap-1.5">
              <UButton
                size="xs"
                :variant="activeFilter === 'all' ? 'solid' : 'ghost'"
                :color="activeFilter === 'all' ? 'primary' : 'neutral'"
                @click="activeFilter = 'all'"
              >
                All ({{ sensorData?.total_sensors ?? 24 }})
              </UButton>
              <UButton
                size="xs"
                :variant="activeFilter === 'informative' ? 'solid' : 'ghost'"
                :color="activeFilter === 'informative' ? 'primary' : 'neutral'"
                @click="activeFilter = 'informative'"
              >
                Informative ({{ sensorData?.informative_count ?? 15 }})
              </UButton>
              <UButton
                size="xs"
                :variant="activeFilter === 'invariant' ? 'solid' : 'ghost'"
                :color="activeFilter === 'invariant' ? 'primary' : 'neutral'"
                @click="activeFilter = 'invariant'"
              >
                Invariant ({{ sensorData?.invariant_count ?? 7 }})
              </UButton>
            </div>

            <!-- Search box -->
            <div class="border-l border-slate-800 pl-3">
              <UInput
                v-model="searchQuery"
                icon="i-lucide-search"
                placeholder="Search channel or description…"
                size="xs"
                class="w-60"
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
          <span class="text-[11px] text-slate-400 hidden lg:inline">
            NASA C-MAPSS FD001 Sea-Level Static Conditions
          </span>
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
        title="Sensor Metadata Error"
        :description="error.message"
        class="mb-6"
      />

      <!-- Smart Decision Narrative -->
      <div class="mb-6">
        <SmartNarrative
          title="Telemetry Degradation Physics Directive"
          :narrative="narrativeText"
          action-hint="Use Ps30 (s11) static pressure and T50 (s4) turbine exhaust temperature as primary health indicators during borescopic inspections."
          badge-text="Variance Pruned"
          tone="info"
        />
      </div>

      <!-- Sensor Summary Cards (Yafa-UI Standard) -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        <YafaKpiCard
          title="Total Instrumentation"
          tooltip="Total recorded NASA C-MAPSS channels including operational settings and sensor taps."
          :value="sensorData?.total_sensors ?? 24"
          unit="Telemetry Channels"
          accent-color="#64748b"
          comparison="3 operating settings + 21 sensor stations"
        />

        <YafaKpiCard
          title="Informative Degradation Channels"
          tooltip="Channels demonstrating measurable statistical variance and monotonic drift across operating cycles."
          :value="sensorData?.informative_count ?? 15"
          unit="Active Features"
          accent-color="#10b981"
          status-type="nominal"
          status-label="In Model Pipeline"
          comparison="Used in rolling window & lag feature engineering"
        />

        <YafaKpiCard
          title="Invariant / Pruned Channels"
          tooltip="Sensors with zero variance (σ < 1e-4) due to constant sea-level operational regime."
          :value="sensorData?.invariant_count ?? 7"
          unit="Channels Pruned"
          accent-color="#f59e0b"
          status-type="warning"
          status-label="Collinearity Safe"
          comparison="setting_3, s1, s5, s10, s16, s18, s19"
        />
      </div>

      <!-- Top Degrading Trends Summary -->
      <UCard class="border border-slate-800 bg-slate-900/60 mb-6">
        <template #header>
          <div>
            <h3 class="text-sm font-semibold text-slate-100 flex items-center gap-2">
              <UIcon name="i-lucide-trending-up" class="size-4 text-teal-400" />
              Primary Wear-Indicator Channels (Cycle Lifetime Correlation)
            </h3>
            <p class="text-xs text-slate-400">Ranked by Pearson correlation with operating cycle lifetime under HPC wear</p>
          </div>
        </template>

        <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 py-2">
          <div
            v-for="trend in topDegradingList"
            :key="trend.id"
            class="p-3 rounded-lg bg-slate-950/80 border border-slate-800 flex items-center justify-between"
          >
            <div>
              <div class="flex items-center gap-1.5 font-mono text-xs font-semibold text-slate-200">
                <span>{{ trend.id }}</span>
                <span class="text-[11px] text-slate-400 font-sans font-normal truncate max-w-[140px]">{{ trend.name }}</span>
              </div>
              <div class="text-[10px] text-slate-400 capitalize mt-1">
                Trend: {{ trend.direction }} with wear
              </div>
            </div>
            <div class="text-right">
              <span
                class="font-mono font-bold text-xs px-2 py-0.5 rounded tabular-nums"
                :class="trend.correlation_with_cycle > 0 ? 'bg-amber-500/15 text-amber-400 border border-amber-500/20' : 'bg-teal-500/15 text-teal-300 border border-teal-500/20'"
              >
                {{ trend.correlation_with_cycle > 0 ? '+' : '' }}{{ trend.correlation_with_cycle.toFixed(2) }}
              </span>
            </div>
          </div>
        </div>
      </UCard>

      <!-- Sensor Catalogue Table -->
      <UCard class="border border-slate-800 bg-slate-900/60 mb-6">
        <template #header>
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-sm font-semibold text-slate-100 flex items-center gap-2">
                <UIcon name="i-lucide-table" class="size-4 text-teal-400" />
                Turbofan Sensor Instrumentation Catalogue
              </h3>
              <p class="text-xs text-slate-400">Physical descriptions, engineering units, and modeling status</p>
            </div>
            <span class="text-xs font-mono text-slate-400 tabular-nums">Showing {{ filteredSensors.length }} channels</span>
          </div>
        </template>

        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs border-collapse">
            <thead>
              <tr class="border-b border-slate-800 text-slate-400 uppercase tracking-wider font-medium text-[11px]">
                <th class="py-2.5 px-3">Channel</th>
                <th class="py-2.5 px-3">Physical Description</th>
                <th class="py-2.5 px-3">Unit</th>
                <th class="py-2.5 px-3">Status</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-800/60">
              <tr
                v-for="s in filteredSensors"
                :key="s.channel || s.id"
                class="hover:bg-slate-800/40 transition-colors"
              >
                <td class="py-2.5 px-3 font-mono font-semibold text-teal-400">
                  {{ s.channel || s.id }}
                </td>
                <td class="py-2.5 px-3 text-slate-200">
                  <div class="font-medium">{{ s.name }}</div>
                  <div class="text-[11px] text-slate-400">{{ s.description || s.desc }}</div>
                </td>
                <td class="py-2.5 px-3 font-mono text-slate-400">
                  {{ s.unit || '-' }}
                </td>
                <td class="py-2.5 px-3">
                  <!-- Anti-capsule: 6px semantic dot + neutral text -->
                  <div class="inline-flex items-center gap-2">
                    <span
                      class="size-1.5 rounded-full shrink-0"
                      :class="s.is_invariant || s.is_constant ? 'bg-slate-500' : 'bg-emerald-400'"
                    />
                    <span class="text-xs text-slate-300">
                      {{ s.is_invariant || s.is_constant ? 'Pruned (Zero Variance)' : 'Informative Signal' }}
                    </span>
                  </div>
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
