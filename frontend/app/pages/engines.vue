<script setup lang="ts">
import type { EngineListResponse, EngineDetailResponse } from '~/types/aeroguard'

const route = useRoute()
const router = useRouter()
const api = useAeroGuardApi()

const selectedEngineId = ref<number>(Number(route.query.id) || 1)
const selectedDataset = ref<'test' | 'train'>('test')
const cutoffCycle = ref<number | null>(null)
const selectedSensor = ref<string>('sensor_2')

// Fetch engine list
const { data: engineListData } = await useAsyncData<EngineListResponse>(
  'engines-list',
  () => api.getEngines(selectedDataset.value)
)

const engines = computed(() => engineListData.value?.engines || [])

// Watch route query
watch(() => route.query.id, (newId) => {
  if (newId && Number(newId) !== selectedEngineId.value) {
    selectedEngineId.value = Number(newId)
  }
})

// Fetch engine detail
const { data: engineDetail, status: detailStatus, error: detailError, refresh: refreshDetail } = await useAsyncData<EngineDetailResponse>(
  'engine-detail',
  () => api.getEngineDetail(selectedEngineId.value, selectedDataset.value, cutoffCycle.value || undefined),
  {
    watch: [selectedEngineId, selectedDataset, cutoffCycle]
  }
)

const maxAvailableCycle = computed(() => engineDetail.value?.max_cycle || 100)
const minAvailableCycle = computed(() => engineDetail.value?.min_cycle || 1)

// Initialize or clamp cutoff cycle
watch(engineDetail, (newVal) => {
  if (newVal && (cutoffCycle.value === null || cutoffCycle.value > newVal.max_cycle)) {
    cutoffCycle.value = newVal.max_cycle
  }
}, { immediate: true })

const selectEngine = (id: number) => {
  selectedEngineId.value = id
  cutoffCycle.value = null // reset to engine's latest cycle
  router.replace({ query: { ...route.query, id } })
}

const resetCutoff = () => {
  cutoffCycle.value = maxAvailableCycle.value
}

const sensorLabels: Record<string, string> = {
  sensor_2: 's2: LPC Outlet Temp (T24 - °R)',
  sensor_3: 's3: HPC Outlet Temp (T30 - °R)',
  sensor_4: 's4: LPT Outlet Temp (T50 - °R)',
  sensor_7: 's7: HPC Outlet Pressure (P30 - psia)',
  sensor_8: 's8: Physical Fan Speed (Nf - rpm)',
  sensor_9: 's9: Physical Core Speed (Nc - rpm)',
  sensor_11: 's11: HPC Static Pressure (Ps30 - psia)',
  sensor_12: 's12: Fuel Flow Ratio (Phi - pps/psi)',
  sensor_13: 's13: Corrected Fan Speed (NRf - rpm)',
  sensor_14: 's14: Corrected Core Speed (NRc - rpm)',
  sensor_15: 's15: Bypass Ratio (BPR)',
  sensor_17: 's17: Bleed Enthalpy (htBleed)',
  sensor_20: 's20: HPT Coolant Bleed (W31 - lbm/s)',
  sensor_21: 's21: LPT Coolant Bleed (W32 - lbm/s)'
}

const observations = computed(() => engineDetail.value?.observations || [])

// Trajectory min and max for the selected sensor to scale chart
const sensorValues = computed(() =>
  observations.value.map(o => Number(o[selectedSensor.value] ?? o[selectedSensor.value.replace('sensor_', 's')]) || 0)
)
const sensorMin = computed(() => sensorValues.value.length ? Math.min(...sensorValues.value) : 0)
const sensorMax = computed(() => sensorValues.value.length ? Math.max(...sensorValues.value) : 1)

// SVG points generator for causal sensor trajectory
const svgPath = computed(() => {
  if (observations.value.length < 2) return ''
  const w = 800
  const h = 220
  const pad = 30
  const range = (sensorMax.value - sensorMin.value) || 1

  return observations.value.map((obs, i) => {
    const x = pad + (i / (observations.value.length - 1)) * (w - 2 * pad)
    const val = Number(obs[selectedSensor.value] ?? obs[selectedSensor.value.replace('sensor_', 's')]) || 0
    const y = h - pad - ((val - sensorMin.value) / range) * (h - 2 * pad)
    return `${i === 0 ? 'M' : 'L'} ${x.toFixed(1)},${y.toFixed(1)}`
  }).join(' ')
})

const dynamicTitle = computed(() => {
  return `Engine Digital Twin — Unit #${selectedEngineId.value} (Cycle ${cutoffCycle.value ?? maxAvailableCycle.value} of ${maxAvailableCycle.value})`
})

const narrativeText = computed(() => {
  if (!engineDetail.value) return 'Fetching turbofan telemetry and causal RUL predictions...'
  const id = engineDetail.value.engine_id
  const cycle = engineDetail.value.cutoff_cycle
  const rul = engineDetail.value.pred_rul.toFixed(1)
  const status = engineDetail.value.health_status
  const trueRul = engineDetail.value.true_rul !== null && engineDetail.value.true_rul !== undefined
    ? `Ground truth RUL: ${engineDetail.value.true_rul.toFixed(1)} cycles (error: ${engineDetail.value.prediction_error ?? '--'}c).`
    : ''
  return `Turbofan Unit #${id} diagnostic state at observed cycle ${cycle}: Health classification is ${status} with estimated RUL of ${rul} operating cycles. ${trueRul} Recommended action: ${engineDetail.value.action_recommendation}`
})

const narrativeTone = computed(() => {
  if (!engineDetail.value) return 'neutral'
  const st = engineDetail.value.health_status.toLowerCase()
  if (st.includes('critical')) return 'critical'
  if (st.includes('warning') || st.includes('advisory')) return 'warning'
  return 'info'
})
</script>

<template>
  <UDashboardPanel id="engine-twin">
    <template #header>
      <UDashboardNavbar :title="dynamicTitle" :ui="{ right: 'gap-3' }">
        <template #leading>
          <UDashboardSidebarCollapse />
        </template>

        <template #right>
          <div class="flex items-center gap-2">
            <DataQualityModal />

            <UBadge color="neutral" variant="outline" class="font-mono text-xs hidden sm:inline-flex">
              Unit #{{ selectedEngineId }}
            </UBadge>

            <UButton
              icon="i-lucide-refresh-cw"
              color="neutral"
              variant="outline"
              size="sm"
              :loading="detailStatus === 'pending'"
              @click="() => refreshDetail()"
            >
              Sync
            </UButton>
          </div>
        </template>
      </UDashboardNavbar>

      <UDashboardToolbar>
        <template #left>
          <div class="flex flex-wrap items-center gap-3">
            <!-- Engine Select Dropdown -->
            <div class="flex items-center gap-2">
              <label for="engine-select" class="text-xs font-medium text-slate-400">Select Engine:</label>
              <select
                id="engine-select"
                :value="selectedEngineId"
                class="bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-md px-2.5 py-1.5 font-mono focus:border-teal-500 focus:outline-hidden"
                @change="(e) => selectEngine(Number((e.target as HTMLSelectElement).value))"
              >
                <option v-for="eng in engines" :key="eng.engine_id" :value="eng.engine_id">
                  Unit #{{ eng.engine_id }} ({{ eng.total_observations }} cycles)
                </option>
              </select>
            </div>

            <!-- Dataset toggle -->
            <div class="flex items-center gap-1.5 border-l border-slate-800 pl-3">
              <span class="text-xs text-slate-400">Set:</span>
              <UButton
                size="xs"
                :variant="selectedDataset === 'test' ? 'solid' : 'ghost'"
                :color="selectedDataset === 'test' ? 'primary' : 'neutral'"
                @click="() => { selectedDataset = 'test'; cutoffCycle = null; }"
              >
                Test Set (100)
              </UButton>
              <UButton
                size="xs"
                :variant="selectedDataset === 'train' ? 'solid' : 'ghost'"
                :color="selectedDataset === 'train' ? 'primary' : 'neutral'"
                @click="() => { selectedDataset = 'train'; cutoffCycle = null; }"
              >
                Train Set (100)
              </UButton>
            </div>

            <UButton
              size="xs"
              color="neutral"
              variant="ghost"
              icon="i-lucide-rotate-ccw"
              @click="resetCutoff"
            >
              Reset Cutoff
            </UButton>
          </div>
        </template>

        <template #right>
          <span class="text-[11px] text-slate-400 hidden lg:inline">
            Strict causal windowing: strictly zero future observation leakage
          </span>
        </template>
      </UDashboardToolbar>
    </template>

    <template #body>
      <div class="space-y-6 shrink-0">
        <!-- Error banner -->
      <UAlert
        v-if="detailError"
        color="error"
        variant="subtle"
        title="Telemetry Ingestion Failure"
        :description="detailError.message"
        class="mb-6"
      />

      <!-- Smart Decision Narrative -->
      <div class="mb-6">
        <SmartNarrative
          title="Digital Twin Operational Status"
          :narrative="narrativeText"
          :action-hint="engineDetail?.action_recommendation"
          :badge-text="`Unit #${selectedEngineId}`"
          :tone="narrativeTone"
        />
      </div>

      <!-- Overview KPI Cards (Yafa-UI Standard) -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <YafaKpiCard
          title="Unit Lifecycle"
          tooltip="Operating cycles recorded up to active timeline cutoff point."
          :value="cutoffCycle ?? maxAvailableCycle"
          :unit="`/ ${maxAvailableCycle} max cycles`"
          accent-color="#64748b"
          :comparison="`Logged trajectory: ${engineDetail?.fleet_type?.toUpperCase()} fleet`"
        />

        <YafaKpiCard
          title="Predicted RUL"
          tooltip="HistGradientBoosting model estimate of remaining cycles before failure."
          :value="engineDetail?.pred_rul?.toFixed(1) ?? '--'"
          unit="cycles"
          :accent-color="(engineDetail?.pred_rul ?? 100) < 20 ? '#ef4444' : (engineDetail?.pred_rul ?? 100) < 45 ? '#f59e0b' : '#10b981'"
          :status-type="(engineDetail?.pred_rul ?? 100) < 20 ? 'critical' : (engineDetail?.pred_rul ?? 100) < 45 ? 'warning' : 'nominal'"
          :status-label="engineDetail?.health_status ?? 'Nominal'"
          :comparison="`Model: HistGradientBoosting (clipped 125c)`"
        />

        <YafaKpiCard
          title="Ground Truth Benchmark"
          tooltip="True remaining cycles for held-out evaluation from NASA C-MAPSS FD001 verification."
          :value="engineDetail?.true_rul !== null && engineDetail?.true_rul !== undefined ? engineDetail.true_rul.toFixed(1) : 'N/A'"
          unit="cycles"
          accent-color="#0ea5e9"
          :comparison="`Prediction error: ${engineDetail?.prediction_error !== null && engineDetail?.prediction_error !== undefined ? (engineDetail.prediction_error > 0 ? '+' : '') + engineDetail.prediction_error + 'c' : 'N/A'}`"
        />

        <YafaKpiCard
          title="Causal Integrity"
          tooltip="Enforces that all rolling statistics and lags expand strictly up to the cutoff cycle."
          value="Zero Leakage"
          accent-color="#14b8a6"
          status-type="nominal"
          status-label="100% Causal"
          :comparison="`Cutoff cycle: ${cutoffCycle ?? maxAvailableCycle} of ${maxAvailableCycle}`"
        />
      </div>

      <!-- Cutoff Timeline Slider -->
      <UCard class="border border-slate-800 bg-slate-900/60 mb-6">
        <template #header>
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <UIcon name="i-lucide-sliders" class="size-4 text-teal-400" />
              <h3 class="text-sm font-semibold text-slate-100">Observation Cutoff Control</h3>
            </div>
            <span class="text-xs font-mono text-teal-400 tabular-nums">
              Active Cutoff: Cycle {{ cutoffCycle ?? maxAvailableCycle }} of {{ maxAvailableCycle }}
            </span>
          </div>
        </template>

        <div class="py-2 space-y-3">
          <label for="cutoff-slider" class="sr-only">Observation Cutoff Slider</label>
          <input
            id="cutoff-slider"
            v-model.number="cutoffCycle"
            type="range"
            :min="minAvailableCycle"
            :max="maxAvailableCycle"
            class="w-full accent-teal-500 cursor-pointer bg-slate-800 rounded-lg h-2"
          />
          <div class="flex justify-between text-[11px] font-mono text-slate-400 tabular-nums">
            <span>Cycle {{ minAvailableCycle }} (Start)</span>
            <span class="text-slate-500 font-sans">Simulate In-Service Flight Progression</span>
            <span>Cycle {{ maxAvailableCycle }} (Terminal)</span>
          </div>
        </div>
      </UCard>

      <!-- Sensor Trajectory Chart -->
      <UCard class="border border-slate-800 bg-slate-900/60 mb-6">
        <template #header>
          <div class="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h3 class="text-sm font-semibold text-slate-100 flex items-center gap-2">
                <UIcon name="i-lucide-line-chart" class="size-4 text-teal-400" />
                Degradation Trajectory Telemetry
              </h3>
              <p class="text-xs text-slate-400">Observed sensor response along engine operating cycles</p>
            </div>

            <!-- Sensor selection -->
            <div class="flex items-center gap-2">
              <label for="sensor-channel-select" class="text-xs text-slate-400">Sensor Channel:</label>
              <select
                id="sensor-channel-select"
                v-model="selectedSensor"
                class="bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-md px-2.5 py-1.5 font-mono focus:border-teal-500 focus:outline-hidden"
              >
                <option v-for="(name, code) in sensorLabels" :key="code" :value="code">
                  {{ name }}
                </option>
              </select>
            </div>
          </div>
        </template>

        <!-- SVG Line Chart with Axis and Grid -->
        <div class="relative bg-slate-950 rounded-lg border border-slate-800 p-4">
          <div class="flex justify-between text-xs font-mono text-slate-400 mb-2 tabular-nums">
            <span>Range: [{{ sensorMin.toFixed(2)}}, {{ sensorMax.toFixed(2) }}]</span>
            <span class="text-teal-400 font-semibold font-sans">{{ sensorLabels[selectedSensor] }}</span>
            <span>Cycles: 1 → {{ observations.length }}</span>
          </div>

          <svg class="w-full h-56" viewBox="0 0 800 220" preserveAspectRatio="none">
            <!-- Grid lines -->
            <line x1="30" y1="30" x2="770" y2="30" stroke="#1e293b" stroke-dasharray="4" />
            <line x1="30" y1="80" x2="770" y2="80" stroke="#1e293b" stroke-dasharray="4" />
            <line x1="30" y1="130" x2="770" y2="130" stroke="#1e293b" stroke-dasharray="4" />
            <line x1="30" y1="190" x2="770" y2="190" stroke="#1e293b" stroke-dasharray="4" />

            <!-- Sensor Trajectory line -->
            <path
              :d="svgPath"
              fill="none"
              stroke="#14b8a6"
              stroke-width="2.5"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>

          <div class="flex justify-between text-[11px] font-mono text-slate-500 mt-2">
            <span>Cycle 1 (Commissioning)</span>
            <span class="text-teal-400">Cutoff: Cycle {{ cutoffCycle ?? maxAvailableCycle }}</span>
          </div>
        </div>
      </UCard>

      <!-- Raw Sensor Observations Table -->
      <UCard class="border border-slate-800 bg-slate-900/60">
        <template #header>
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-sm font-semibold text-slate-100 flex items-center gap-2">
                <UIcon name="i-lucide-database" class="size-4 text-teal-400" />
                Historical Sensor Telemetry Log
              </h3>
              <p class="text-xs text-slate-400">Most recent observations up to selected cutoff cycle</p>
            </div>
            <span class="text-xs text-slate-400 font-mono tabular-nums">Showing {{ Math.min(10, observations.length) }} of {{ observations.length }} observations</span>
          </div>
        </template>

        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs border-collapse">
            <thead>
              <tr class="border-b border-slate-800 text-slate-400 uppercase tracking-wider font-medium text-[11px]">
                <th class="py-2.5 px-3">Cycle</th>
                <th class="py-2.5 px-3">s2 (°R)</th>
                <th class="py-2.5 px-3">s3 (°R)</th>
                <th class="py-2.5 px-3">s4 (°R)</th>
                <th class="py-2.5 px-3">s7 (psia)</th>
                <th class="py-2.5 px-3">s8 (rpm)</th>
                <th class="py-2.5 px-3">s9 (rpm)</th>
                <th class="py-2.5 px-3">s11 (psia)</th>
                <th class="py-2.5 px-3">s12 (ratio)</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-800/60 font-mono tabular-nums">
              <tr
                v-for="row in observations.slice(-10).reverse()"
                :key="Number(row.cycle)"
                class="hover:bg-slate-800/40 transition-colors"
              >
                <td class="py-2 px-3 font-semibold text-teal-400">{{ row.cycle }}</td>
                <td class="py-2 px-3 text-slate-300">{{ Number(row.sensor_2 ?? row.s2 ?? 0).toFixed(2) }}</td>
                <td class="py-2 px-3 text-slate-300">{{ Number(row.sensor_3 ?? row.s3 ?? 0).toFixed(2) }}</td>
                <td class="py-2 px-3 text-slate-300">{{ Number(row.sensor_4 ?? row.s4 ?? 0).toFixed(2) }}</td>
                <td class="py-2 px-3 text-slate-300">{{ Number(row.sensor_7 ?? row.s7 ?? 0).toFixed(2) }}</td>
                <td class="py-2 px-3 text-slate-300">{{ Number(row.sensor_8 ?? row.s8 ?? 0).toFixed(2) }}</td>
                <td class="py-2 px-3 text-slate-300">{{ Number(row.sensor_9 ?? row.s9 ?? 0).toFixed(2) }}</td>
                <td class="py-2 px-3 text-slate-300">{{ Number(row.sensor_11 ?? row.s11 ?? 0).toFixed(2) }}</td>
                <td class="py-2 px-3 text-slate-300">{{ Number(row.sensor_12 ?? row.s12 ?? 0).toFixed(2) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </UCard>
    </div>
  </template>
</UDashboardPanel>
</template>
