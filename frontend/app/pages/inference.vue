<script setup lang="ts">
import type { EngineListResponse, PredictionResponse, EngineDetailResponse } from '~/types/aeroguard'

const route = useRoute()
const router = useRouter()
const api = useAeroGuardApi()

const selectedEngineId = ref<number>(Number(route.query.id) || 1)
const selectedDataset = ref<'test' | 'train'>('test')
const selectedCutoff = ref<number>(31)
const isPredicting = ref<boolean>(false)
const predictionResult = ref<PredictionResponse | null>(null)
const predictionError = ref<string | null>(null)

// Load engine list
const { data: engineListData } = await useAsyncData<EngineListResponse>(
  'inference-engine-list',
  () => api.getEngines(selectedDataset.value)
)

const engines = computed(() => engineListData.value?.engines || [])

// Watch selected engine to load its lifecycle bounds
const { data: engineDetail } = await useAsyncData<EngineDetailResponse>(
  'inference-engine-detail',
  () => api.getEngineDetail(selectedEngineId.value, selectedDataset.value),
  {
    watch: [selectedEngineId, selectedDataset]
  }
)

const maxCycle = computed(() => engineDetail.value?.max_cycle || 100)
const minCycle = computed(() => engineDetail.value?.min_cycle || 1)

// Synchronize cutoff slider to the latest cycle when engine changes
watch(engineDetail, (newVal) => {
  if (newVal) {
    selectedCutoff.value = newVal.max_cycle
  }
}, { immediate: true })

const selectEngine = (id: number) => {
  selectedEngineId.value = id
  predictionResult.value = null
  predictionError.value = null
  router.replace({ query: { ...route.query, id } })
}

const resetCutoff = () => {
  selectedCutoff.value = maxCycle.value
}

const runInference = async () => {
  isPredicting.value = true
  predictionError.value = null

  try {
    const res = await api.postPredict({
      engine_id: selectedEngineId.value,
      cutoff_cycle: selectedCutoff.value,
      dataset: selectedDataset.value
    })
    predictionResult.value = res
  } catch (err: any) {
    predictionError.value = err?.data?.detail || err?.message || 'Inference execution failed'
  } finally {
    isPredicting.value = false
  }
}

// Auto-run inference initially
onMounted(() => {
  runInference()
})

const dynamicTitle = computed(() => {
  return `RUL Inference Lab — Unit #${selectedEngineId.value} at Cycle ${selectedCutoff.value} of ${maxCycle.value}`
})

const narrativeText = computed(() => {
  if (!predictionResult.value) return 'Configuring causal parameter space for offline simulation…'
  const res = predictionResult.value
  const rul = (res.predicted_rul ?? res.pred_rul).toFixed(1)
  const trueRulText = res.true_rul !== null && res.true_rul !== undefined
    ? `Ground truth target is ${res.true_rul.toFixed(1)} cycles (prediction delta: ${(res.prediction_error ?? 0) > 0 ? '+' : ''}${res.prediction_error}c).`
    : ''
  return `Causal inference result: Turbofan Unit #${res.engine_id} at cutoff cycle ${res.cutoff_cycle} has estimated remaining useful life of ${rul} cycles (${res.health_status} severity). ${trueRulText} Target clipping policy is ${res.target_clipped ? 'active (capped at 125c threshold)' : 'in linear wear regime'}.`
})

const narrativeTone = computed(() => {
  if (!predictionResult.value) return 'neutral'
  const st = (predictionResult.value.status || predictionResult.value.health_status || '').toLowerCase()
  if (st.includes('critical')) return 'critical'
  if (st.includes('warning') || st.includes('advisory')) return 'warning'
  return 'info'
})
</script>

<template>
  <UDashboardPanel id="inference-lab">
    <template #header>
      <UDashboardNavbar :title="dynamicTitle" :ui="{ right: 'gap-3' }">
        <template #leading>
          <UDashboardSidebarCollapse />
        </template>

        <template #right>
          <div class="flex items-center gap-2">
            <DataQualityModal />

            <UBadge color="teal" variant="subtle" class="font-mono text-xs hidden sm:inline-flex">
              HistGradientBoosting Regressor
            </UBadge>
          </div>
        </template>
      </UDashboardNavbar>

      <UDashboardToolbar>
        <template #left>
          <div class="flex flex-wrap items-center gap-3">
            <!-- Engine select -->
            <div class="flex items-center gap-2">
              <label for="inference-engine-select" class="text-xs font-medium text-slate-400">Target Engine:</label>
              <select
                id="inference-engine-select"
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
              <span class="text-xs text-slate-400">Dataset:</span>
              <UButton
                size="xs"
                :variant="selectedDataset === 'test' ? 'solid' : 'ghost'"
                :color="selectedDataset === 'test' ? 'primary' : 'neutral'"
                @click="() => { selectedDataset = 'test'; }"
              >
                Test Set
              </UButton>
              <UButton
                size="xs"
                :variant="selectedDataset === 'train' ? 'solid' : 'ghost'"
                :color="selectedDataset === 'train' ? 'primary' : 'neutral'"
                @click="() => { selectedDataset = 'train'; }"
              >
                Train Set
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
            Executes preprocessor.joblib + best_model.joblib on genuine feature pipeline
          </span>
        </template>
      </UDashboardToolbar>
    </template>

    <template #body>
      <div class="space-y-6 shrink-0">
        <!-- Simulation Controls & Trigger -->
      <UCard class="border border-slate-800 bg-slate-900/60 mb-6">
        <template #header>
          <div class="flex items-center justify-between">
            <h3 class="text-sm font-semibold text-slate-100 flex items-center gap-2">
              <UIcon name="i-lucide-play-circle" class="size-4 text-teal-400" />
              Causal Inference Parameter Configuration
            </h3>
            <span class="text-xs font-mono text-teal-400 tabular-nums">
              Cutoff Cycle: {{ selectedCutoff }} of {{ maxCycle }}
            </span>
          </div>
        </template>

        <div class="space-y-4 py-2">
          <div>
            <div class="flex justify-between text-xs text-slate-400 mb-1.5">
              <span>Observation Cutoff Boundary (Temporal Isolation):</span>
              <span class="font-mono text-slate-200 tabular-nums">Cycle {{ selectedCutoff }}</span>
            </div>
            <label for="inference-cutoff-range" class="sr-only">Cutoff Cycle</label>
            <input
              id="inference-cutoff-range"
              v-model.number="selectedCutoff"
              type="range"
              :min="minCycle"
              :max="maxCycle"
              class="w-full accent-teal-500 cursor-pointer bg-slate-800 rounded-lg h-2"
            />
            <p class="text-[11px] text-slate-500 mt-1">
              Strictly features up to Cycle {{ selectedCutoff }} will be computed using causal expanding rolling windows.
            </p>
          </div>

          <div class="flex items-center justify-between pt-2 border-t border-slate-800">
            <span class="text-xs text-slate-400">
              Inference Endpoint: <code class="text-teal-400 font-mono">POST /api/predict</code>
            </span>
            <UButton
              color="primary"
              size="sm"
              icon="i-lucide-zap"
              :loading="isPredicting"
              @click="runInference"
            >
              Execute Model Prediction
            </UButton>
          </div>
        </div>
      </UCard>

      <!-- Prediction Error Banner -->
      <UAlert
        v-if="predictionError"
        color="error"
        variant="subtle"
        title="Prediction Execution Rejected"
        :description="predictionError"
        class="mb-6"
      />

      <!-- Smart Decision Narrative -->
      <div v-if="predictionResult" class="mb-6">
        <SmartNarrative
          title="Predictive Inference Directive"
          :narrative="narrativeText"
          :action-hint="predictionResult.action_recommendation || predictionResult.action"
          :badge-text="`Unit #${selectedEngineId} @ Cycle ${selectedCutoff}`"
          :tone="narrativeTone"
        />
      </div>

      <!-- Prediction Output Cards (Yafa-UI Standard) -->
      <div v-if="predictionResult" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <YafaKpiCard
          title="Estimated Remaining Useful Life"
          tooltip="HistGradientBoosting regressor predicted remaining flight cycles until failure limit."
          :value="(predictionResult.predicted_rul ?? predictionResult.pred_rul).toFixed(1)"
          unit="cycles"
          :accent-color="(predictionResult.predicted_rul ?? predictionResult.pred_rul) < 20 ? '#ef4444' : (predictionResult.predicted_rul ?? predictionResult.pred_rul) < 45 ? '#f59e0b' : '#10b981'"
          :status-type="(predictionResult.predicted_rul ?? predictionResult.pred_rul) < 20 ? 'critical' : (predictionResult.predicted_rul ?? predictionResult.pred_rul) < 45 ? 'warning' : 'nominal'"
          :status-label="`${predictionResult.status || predictionResult.health_status}`"
          :comparison="`Observation cutoff: Cycle ${predictionResult.cutoff_cycle}`"
        />

        <YafaKpiCard
          title="Ground Truth Verification"
          tooltip="True remaining cycles for held-out evaluation from NASA C-MAPSS FD001 verification."
          :value="predictionResult.true_rul !== null && predictionResult.true_rul !== undefined ? predictionResult.true_rul.toFixed(1) : 'N/A'"
          unit="cycles"
          accent-color="#0ea5e9"
          :comparison="`Prediction error: ${predictionResult.prediction_error !== null && predictionResult.prediction_error !== undefined ? (predictionResult.prediction_error > 0 ? '+' : '') + predictionResult.prediction_error + 'c' : 'N/A'}`"
        />

        <YafaKpiCard
          title="Degradation Policy Envelope"
          tooltip="NASA standard piecewise-linear envelope: targets capped at 125 cycles constant buffer."
          :value="predictionResult.target_clipped ? '125c Upper Cap' : 'Linear Wear'"
          accent-color="#f59e0b"
          :comparison="`Model: ${predictionResult.model || predictionResult.model_name}`"
        />

        <YafaKpiCard
          title="Engineered Feature Dimension"
          tooltip="Scaled features computed using strictly causal expanding window statistics."
          :value="predictionResult.features_summary?.feature_count ?? 122"
          unit="Features"
          accent-color="#14b8a6"
          status-type="nominal"
          status-label="Zero Leakage"
          comparison="Strict forward windowing"
        />
      </div>

      <!-- Feature Vector Inspection -->
      <UCard v-if="predictionResult && predictionResult.features_summary" class="border border-slate-800 bg-slate-900/60 mb-6">
        <template #header>
          <div class="flex items-center justify-between">
            <h3 class="text-sm font-semibold text-slate-100 flex items-center gap-2">
              <UIcon name="i-lucide-binary" class="size-4 text-teal-400" />
              Engineered Feature Representation (Sample Telemetry at Cutoff)
            </h3>
            <span class="text-xs font-mono text-slate-400">Causal Rolling Window Averages & Delays</span>
          </div>
        </template>

        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3 py-2">
          <div
            v-for="(val, featName) in predictionResult.features_summary.top_features"
            :key="featName"
            class="p-2.5 rounded-lg bg-slate-950 border border-slate-800 flex flex-col justify-between"
          >
            <span class="text-[11px] font-mono text-slate-400 truncate">{{ featName }}</span>
            <span class="text-sm font-mono font-bold text-slate-200 mt-1 tabular-nums">
              {{ typeof val === 'number' ? val.toFixed(3) : val }}
            </span>
          </div>
        </div>
      </UCard>
    </div>
  </template>
</UDashboardPanel>
</template>
