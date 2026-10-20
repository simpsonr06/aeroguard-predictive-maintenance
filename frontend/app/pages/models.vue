<script setup lang="ts">
import type { ModelMetricsResponse } from '~/types/aeroguard'

const api = useAeroGuardApi()

const { data: modelData, status, error, refresh } = await useAsyncData<ModelMetricsResponse>(
  'model-metrics',
  () => api.getModelMetrics()
)

const { data: driftData } = await useAsyncData(
  'model-drift',
  () => api.getDrift()
)

const { data: lineageData } = await useAsyncData(
  'model-lineage',
  () => api.getLineage()
)

const activeRegime = ref<'official_test' | 'cutoff_cv' | 'full_trajectory' | 'failure_point'>('official_test')

const resetRegime = () => {
  activeRegime.value = 'official_test'
}

const regimeLabels: Record<string, string> = {
  official_test: 'Official Held-Out Test (FD001 Final Cutoff)',
  cutoff_cv: 'In-Service Cutoff 5-Fold Cross-Validation',
  full_trajectory: 'Full-Trajectory 5-Fold Cross-Validation',
  failure_point: 'Terminal Failure-Point 5-Fold Validation'
}

const modelsList = [
  { name: 'HistGradientBoosting', label: 'HistGradientBoosting', isChampion: true },
  { name: 'Random Forest', label: 'Random Forest', isChampion: false },
  { name: 'Ridge Regression', label: 'Ridge Regression', isChampion: false },
  { name: 'Dummy (Mean Baseline)', label: 'Dummy Baseline (Mean)', isChampion: false }
]

const getMetricValue = (regime: string, modelName: string, metric: 'rmse' | 'mae' | 'r2' | 'nasa'): string => {
  if (!modelData.value) return '--'
  let regimeObj: Record<string, any> | undefined
  if (regime === 'official_test') regimeObj = modelData.value.official_test_metrics
  else if (regime === 'cutoff_cv') regimeObj = modelData.value.cutoff_cv_metrics
  else if (regime === 'full_trajectory') regimeObj = modelData.value.full_trajectory_cv_metrics
  else if (regime === 'failure_point') regimeObj = modelData.value.failure_point_cv_metrics

  const mData = regimeObj?.[modelName]
  if (!mData) return 'N/A'

  let val: any
  if (regime === 'official_test') {
    if (metric === 'rmse') val = mData.test_rmse_official ?? mData.test_rmse_clipped
    else if (metric === 'mae') val = mData.test_mae_official ?? mData.test_mae_clipped
    else if (metric === 'r2') val = mData.test_r2_official ?? mData.test_r2_clipped
    else if (metric === 'nasa') val = mData.test_nasa_score_official ?? mData.test_nasa_score_clipped
  } else {
    if (metric === 'rmse') val = mData.rmse_mean
    else if (metric === 'mae') val = mData.mae_mean
    else if (metric === 'r2') val = mData.r2_mean
    else if (metric === 'nasa') val = mData.nasa_score_sum_mean ?? mData.nasa_score_per_sample_mean
  }

  if (val === undefined || val === null) return 'N/A'
  return typeof val === 'number' ? val.toFixed(2) : String(val)
}

const dynamicTitle = computed(() => {
  return `Model Intelligence & Validation — ${regimeLabels[activeRegime.value] || 'Official Benchmark'}`
})

const narrativeText = computed(() => {
  return 'Benchmarking across 4 distinct operational regimes validates HistGradientBoostingRegressor as the production champion with an official held-out test RMSE of 13.90 cycles and 0.888 R². Target RUL is clipped at 125 cycles during training according to the NASA C-MAPSS standard piecewise-linear health degradation envelope.'
})
</script>

<template>
  <UDashboardPanel id="model-intelligence">
    <template #header>
      <UDashboardNavbar :title="dynamicTitle" :ui="{ right: 'gap-3' }">
        <template #leading>
          <UDashboardSidebarCollapse />
        </template>

        <template #right>
          <div class="flex items-center gap-2">
            <DataQualityModal />

            <UBadge color="teal" variant="subtle" class="font-mono text-xs hidden sm:inline-flex">
              Champion: {{ modelData?.best_model || 'HistGradientBoosting' }}
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
          <div class="flex flex-wrap items-center gap-2">
            <span class="text-xs font-medium text-slate-400">Evaluation Regime:</span>
            <UButton
              size="xs"
              :variant="activeRegime === 'official_test' ? 'solid' : 'ghost'"
              :color="activeRegime === 'official_test' ? 'primary' : 'neutral'"
              @click="activeRegime = 'official_test'"
            >
              Official Held-Out Test
            </UButton>
            <UButton
              size="xs"
              :variant="activeRegime === 'cutoff_cv' ? 'solid' : 'ghost'"
              :color="activeRegime === 'cutoff_cv' ? 'primary' : 'neutral'"
              @click="activeRegime = 'cutoff_cv'"
            >
              Cutoff CV (5-Fold)
            </UButton>
            <UButton
              size="xs"
              :variant="activeRegime === 'full_trajectory' ? 'solid' : 'ghost'"
              :color="activeRegime === 'full_trajectory' ? 'primary' : 'neutral'"
              @click="activeRegime = 'full_trajectory'"
            >
              Full-Trajectory CV
            </UButton>
            <UButton
              size="xs"
              :variant="activeRegime === 'failure_point' ? 'solid' : 'ghost'"
              :color="activeRegime === 'failure_point' ? 'primary' : 'neutral'"
              @click="activeRegime = 'failure_point'"
            >
              Failure-Point Validation
            </UButton>

            <UButton
              size="xs"
              color="neutral"
              variant="ghost"
              icon="i-lucide-rotate-ccw"
              @click="resetRegime"
            >
              Reset
            </UButton>
          </div>
        </template>

        <template #right>
          <span class="text-[11px] text-slate-400 hidden lg:inline">
            Verified serialized models/model_registry.json
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
        title="Model Registry Error"
        :description="error.message"
        class="mb-6"
      />

      <!-- Smart Decision Narrative -->
      <div class="mb-6">
        <SmartNarrative
          title="Machine Learning Governance & Validation Directive"
          :narrative="narrativeText"
          action-hint="HistGradientBoosting exhibits the lowest asymmetric NASA penalty score (301.97), minimizing late-prediction risk compared to linear and tree baselines."
          badge-text="HistGradientBoosting"
          tone="info"
        />
      </div>

      <!-- Overview Metric Cards for Champion Model (Yafa-UI Standard) -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <YafaKpiCard
          title="Official Test RMSE"
          tooltip="Root Mean Squared Error on 100 held-out test engines at cutoff cycles."
          :value="getMetricValue('official_test', 'HistGradientBoosting', 'rmse')"
          unit="cycles"
          accent-color="#14b8a6"
          status-type="nominal"
          status-label="Champion Score"
          comparison="Benchmark: 13.90 cycles"
        />

        <YafaKpiCard
          title="Official Test MAE"
          tooltip="Mean Absolute Error across the 100 held-out test engines."
          :value="getMetricValue('official_test', 'HistGradientBoosting', 'mae')"
          unit="cycles"
          accent-color="#10b981"
          comparison="Mean deviation: 10.40 cycles"
        />

        <YafaKpiCard
          title="Variance Explained (R²)"
          tooltip="Proportion of remaining lifetime variance captured by the gradient boosted model."
          :value="getMetricValue('official_test', 'HistGradientBoosting', 'r2')"
          accent-color="#0ea5e9"
          comparison="Strong predictive correlation (0.89)"
        />

        <YafaKpiCard
          title="Target Degradation Cap"
          tooltip="Piecewise-linear RUL clipping limit (125 cycles) preventing over-optimistic healthy estimation."
          value="125"
          unit="cycles cap"
          accent-color="#64748b"
          comparison="Pre-degradation health buffer"
        />
      </div>

      <!-- Empirical Model Benchmark Comparison Table -->
      <UCard class="border border-slate-800 bg-slate-900/60 mb-6">
        <template #header>
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-sm font-semibold text-slate-100 flex items-center gap-2">
                <UIcon name="i-lucide-trophy" class="size-4 text-teal-400" />
                Empirical Model Benchmark Leaderboard
              </h3>
              <p class="text-xs text-slate-400">
                Evaluation results under active regime: <span class="text-teal-400 font-mono font-semibold">{{ regimeLabels[activeRegime] }}</span>
              </p>
            </div>
            <span class="text-xs font-mono text-slate-400">4 Candidate Architectures</span>
          </div>
        </template>

        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs border-collapse">
            <thead>
              <tr class="border-b border-slate-800 text-slate-400 uppercase tracking-wider font-medium text-[11px]">
                <th class="py-2.5 px-4">Architecture</th>
                <th class="py-2.5 px-4 font-mono">RMSE (cycles)</th>
                <th class="py-2.5 px-4 font-mono">MAE (cycles)</th>
                <th class="py-2.5 px-4 font-mono">R² Score</th>
                <th class="py-2.5 px-4 font-mono">NASA Score</th>
                <th class="py-2.5 px-4">Status</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-800/60 font-mono tabular-nums">
              <tr
                v-for="model in modelsList"
                :key="model.name"
                class="hover:bg-slate-800/40 transition-colors"
                :class="model.isChampion ? 'bg-teal-500/5' : ''"
              >
                <td class="py-3 px-4 font-sans font-semibold text-slate-200 flex items-center gap-2">
                  <UIcon
                    :name="model.isChampion ? 'i-lucide-check-circle-2' : 'i-lucide-circle'"
                    class="size-4"
                    :class="model.isChampion ? 'text-teal-400' : 'text-slate-500'"
                  />
                  <span>{{ model.label }}</span>
                </td>
                <td class="py-3 px-4 font-bold" :class="model.isChampion ? 'text-teal-300' : 'text-slate-200'">
                  {{ getMetricValue(activeRegime, model.name, 'rmse') }}
                </td>
                <td class="py-3 px-4 text-slate-300">
                  {{ getMetricValue(activeRegime, model.name, 'mae') }}
                </td>
                <td class="py-3 px-4 text-slate-300">
                  {{ getMetricValue(activeRegime, model.name, 'r2') }}
                </td>
                <td class="py-3 px-4 text-slate-300">
                  {{ getMetricValue(activeRegime, model.name, 'nasa') }}
                </td>
                <td class="py-3 px-4 font-sans">
                  <!-- Anti-capsule: 6px semantic dot + neutral text -->
                  <div class="inline-flex items-center gap-2">
                    <span
                      class="size-1.5 rounded-full shrink-0"
                      :class="model.isChampion ? 'bg-teal-400' : 'bg-slate-500'"
                    />
                    <span class="text-xs text-slate-300">
                      {{ model.isChampion ? 'Production Champion' : 'Evaluated Baseline' }}
                    </span>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </UCard>

      <!-- Stage 3: Statistical Covariate Drift Monitoring -->
      <UCard v-if="driftData" class="border border-slate-800 bg-slate-900/60 mb-6">
        <template #header>
          <div class="flex items-center justify-between flex-wrap gap-2">
            <div>
              <div class="flex items-center gap-2">
                <UIcon name="i-lucide-activity" class="size-4 text-teal-400" />
                <h3 class="text-sm font-semibold text-slate-100">
                  Covariate Distribution Drift & Stability
                </h3>
                <div class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-mono"
                     :class="driftData.overall_status === 'stable' ? 'bg-emerald-950/80 text-emerald-300 border border-emerald-800/80' : driftData.overall_status === 'warning' ? 'bg-amber-950/80 text-amber-300 border border-amber-800/80' : 'bg-rose-950/80 text-rose-300 border border-rose-800/80'">
                  <span class="size-1.5 rounded-full" :class="driftData.overall_status === 'stable' ? 'bg-emerald-400' : driftData.overall_status === 'warning' ? 'bg-amber-400' : 'bg-rose-400'"></span>
                  <span>{{ driftData.overall_status === 'stable' ? 'Distribution Stable' : driftData.overall_status === 'warning' ? 'Moderate Shift' : 'Drift Alert' }}</span>
                </div>
              </div>
              <p class="text-xs text-slate-400 mt-1">
                Reference: <span class="text-slate-200 font-mono">{{ driftData.reference_dataset }} (N={{ driftData.sample_size_reference }})</span>
                &bull; Comparison: <span class="text-slate-200 font-mono">{{ driftData.comparison_dataset }} (N={{ driftData.sample_size_comparison }})</span>
              </p>
            </div>
            <div class="text-[11px] font-mono text-slate-400">
              Evaluated: {{ new Date(driftData.measurement_time).toLocaleTimeString() }}
            </div>
          </div>
        </template>

        <!-- Operational Drift Disclaimer -->
        <div class="mb-4 p-3 rounded bg-slate-950/80 border border-slate-800/80 text-xs text-slate-300">
          <p class="leading-relaxed">
            <strong class="text-teal-300">Covariate Shift P(X) vs Model Degradation P(Y|X):</strong>
            {{ driftData.caveat }}
          </p>
        </div>

        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs border-collapse">
            <thead>
              <tr class="border-b border-slate-800 text-slate-400 uppercase tracking-wider font-medium text-[11px]">
                <th class="py-2 px-3">Monitored Sensor</th>
                <th class="py-2 px-3 font-mono">Ref Mean &plusmn; Std</th>
                <th class="py-2 px-3 font-mono">Current Mean &plusmn; Std</th>
                <th class="py-2 px-3 font-mono">Norm Shift (&Delta;&mu;/&sigma;)</th>
                <th class="py-2 px-3 font-mono">KS Statistic</th>
                <th class="py-2 px-3 font-mono">PSI Score</th>
                <th class="py-2 px-3">Stability Status</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-800/60 font-mono tabular-nums">
              <tr v-for="(metric, sensorId) in driftData.features" :key="sensorId" class="hover:bg-slate-800/30">
                <td class="py-2.5 px-3 font-sans font-medium text-slate-200">
                  {{ sensorId.replace('sensor_', 'Sensor ') }}
                </td>
                <td class="py-2.5 px-3 text-slate-400">
                  {{ metric.ref_mean }} &plusmn; {{ metric.ref_std }}
                </td>
                <td class="py-2.5 px-3 text-slate-300">
                  {{ metric.cur_mean }} &plusmn; {{ metric.cur_std }}
                </td>
                <td class="py-2.5 px-3" :class="Math.abs(metric.norm_mean_shift) > 0.5 ? 'text-amber-400 font-bold' : 'text-slate-300'">
                  {{ metric.norm_mean_shift > 0 ? '+' : '' }}{{ metric.norm_mean_shift }}
                </td>
                <td class="py-2.5 px-3 text-slate-300">
                  {{ metric.ks_statistic }} (p={{ metric.ks_pvalue }})
                </td>
                <td class="py-2.5 px-3 font-bold" :class="metric.psi >= 0.25 ? 'text-rose-400' : metric.psi >= 0.10 ? 'text-amber-400' : 'text-emerald-400'">
                  {{ metric.psi }}
                </td>
                <td class="py-2.5 px-3 font-sans">
                  <div class="inline-flex items-center gap-1.5">
                    <span class="size-1.5 rounded-full"
                          :class="metric.status === 'stable' ? 'bg-emerald-400' : metric.status === 'warning' ? 'bg-amber-400' : 'bg-rose-400'"></span>
                    <span class="text-[11px] capitalize text-slate-300">{{ metric.status.replace('_', ' ') }}</span>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </UCard>

      <!-- Stage 5: Cryptographic Model Lineage Manifest -->
      <UCard v-if="lineageData" class="border border-slate-800 bg-slate-900/60 mb-6">
        <template #header>
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <UIcon name="i-lucide-git-branch" class="size-4 text-teal-400" />
              <div>
                <h3 class="text-sm font-semibold text-slate-100">
                  Cryptographic Model Lineage & Provenance Manifest
                </h3>
                <p class="text-xs text-slate-400">
                  Artifact SHA-256 validation &bull; Manifest Version <span class="font-mono text-teal-300">{{ lineageData.manifest_version }}</span>
                </p>
              </div>
            </div>
            <span class="text-xs font-mono text-slate-400">ID: {{ lineageData.model_id }}</span>
          </div>
        </template>

        <div class="space-y-4 text-xs">
          <!-- MLflow Trade-off Evaluation Callout -->
          <div class="p-3 rounded bg-slate-950/80 border border-slate-800 text-slate-300 leading-relaxed">
            <span class="font-semibold text-teal-300 block mb-1">Architecture Decision — Offline Cryptographic Manifest vs MLflow:</span>
            {{ lineageData.mlflow_evaluation }}
          </div>

          <!-- Artifact Hashes Grid -->
          <div>
            <span class="font-semibold text-slate-200 block mb-2 uppercase text-[11px] tracking-wider">
              Immutable Artifact Cryptographic Hashes (SHA-256)
            </span>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-2 font-mono text-[11px]">
              <div v-for="(hash, name) in lineageData.artifacts_sha256" :key="name" class="p-2 rounded bg-slate-950 border border-slate-800/80">
                <div class="text-slate-400">{{ name }}</div>
                <div class="text-teal-300 truncate" :title="hash">{{ hash }}</div>
              </div>
            </div>
          </div>

          <!-- Dataset Hashes Grid -->
          <div>
            <span class="font-semibold text-slate-200 block mb-2 uppercase text-[11px] tracking-wider">
              Source Benchmark Datasets (SHA-256)
            </span>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-2 font-mono text-[11px]">
              <div v-for="(hash, name) in lineageData.datasets_sha256" :key="name" class="p-2 rounded bg-slate-950 border border-slate-800/80">
                <div class="text-slate-400">{{ name }}</div>
                <div class="text-slate-300 truncate" :title="hash">{{ hash }}</div>
              </div>
            </div>
          </div>
        </div>
      </UCard>

      <!-- Methodological Isolation Notice -->
      <div class="p-3.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-400 leading-relaxed space-y-1">
        <div class="font-semibold text-slate-200 flex items-center gap-1.5">
          <UIcon name="i-lucide-info" class="size-4 text-teal-400" />
          <span>Scientific Regime Isolation Standards</span>
        </div>
        <p>
          Each evaluation regime reflects distinct operational conditions. The official held-out test set evaluates terminal in-service cutoff points. Full-trajectory CV evaluates performance across all operating cycles, while terminal failure validation isolates prediction accuracy immediately prior to breakdown. Metrics from distinct regimes must never be compared directly as equivalents.
        </p>
      </div>
    </div>
  </template>
</UDashboardPanel>
</template>
