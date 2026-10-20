<script setup lang="ts">
const isOpen = ref(false)
</script>

<template>
  <div>
    <button
      type="button"
      class="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium text-slate-300 bg-slate-900/80 hover:bg-slate-800 border border-slate-700/80 rounded-md transition-colors focus-visible:ring-2 focus-visible:ring-teal-500"
      @click="isOpen = true"
    >
      <span class="size-2 rounded-full bg-emerald-400"></span>
      <span class="font-mono text-slate-200">Data Quality: 100%</span>
      <UIcon name="i-lucide-info" class="size-3.5 text-slate-400 ml-0.5" />
    </button>

    <UModal v-model:open="isOpen" title="Dataset Integrity & Provenance Audit" :ui="{ content: 'max-w-xl bg-slate-900 border border-slate-800' }">
      <template #header>
        <div class="flex items-center justify-between w-full">
          <div class="flex items-center gap-2">
            <UIcon name="i-lucide-shield-check" class="size-5 text-teal-400" />
            <h3 class="text-sm font-semibold text-slate-100">Dataset Provenance & Quality Audit</h3>
          </div>
          <UButton
            icon="i-lucide-x"
            color="neutral"
            variant="ghost"
            size="xs"
            @click="isOpen = false"
          />
        </div>
      </template>

      <template #body>
        <div class="space-y-4 text-xs text-slate-300">
          <div class="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-slate-400 font-medium">Underlying Data Source:</span>
              <span class="font-mono font-semibold text-slate-200">NASA C-MAPSS FD001</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-slate-400 font-medium">Operating Context:</span>
              <span class="font-mono text-slate-200">Sea-Level Single Flight Condition</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-slate-400 font-medium">Degradation Mechanism:</span>
              <span class="font-mono text-slate-200">High-Pressure Compressor (HPC) Wear</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-slate-400 font-medium">Fleet Volumes:</span>
              <span class="font-mono text-slate-200">100 Train (Run-to-Failure), 100 Test Units</span>
            </div>
          </div>

          <div class="grid grid-cols-3 gap-3 text-center">
            <div class="p-2.5 rounded-lg bg-slate-950/80 border border-slate-800">
              <div class="text-[10px] text-slate-400 uppercase font-medium">Completeness</div>
              <div class="text-base font-bold font-mono text-emerald-400 mt-0.5">100%</div>
              <div class="text-[10px] text-slate-500 mt-0.5">0 missing values</div>
            </div>
            <div class="p-2.5 rounded-lg bg-slate-950/80 border border-slate-800">
              <div class="text-[10px] text-slate-400 uppercase font-medium">Causal Isolation</div>
              <div class="text-base font-bold font-mono text-emerald-400 mt-0.5">100%</div>
              <div class="text-[10px] text-slate-500 mt-0.5">Zero future leakage</div>
            </div>
            <div class="p-2.5 rounded-lg bg-slate-950/80 border border-slate-800">
              <div class="text-[10px] text-slate-400 uppercase font-medium">Variance Pruning</div>
              <div class="text-base font-bold font-mono text-teal-400 mt-0.5">7 / 21</div>
              <div class="text-[10px] text-slate-500 mt-0.5">Invariant pruned</div>
            </div>
          </div>

          <div class="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-200/90 text-[11px] leading-relaxed">
            <div class="font-semibold text-amber-300 flex items-center gap-1.5 mb-1">
              <UIcon name="i-lucide-alert-triangle" class="size-3.5 text-amber-400" />
              <span>Historical Benchmark & Model-Generated Estimates Notice</span>
            </div>
            This application ingests historical run-to-failure simulation records from NASA’s Commercial Modular Aero-Propulsion System Simulation (C-MAPSS) archive. Remaining Useful Life metrics are model-generated statistical predictions, not live physical telemetry feeds from in-flight airframes.
          </div>
        </div>
      </template>
    </UModal>
  </div>
</template>
