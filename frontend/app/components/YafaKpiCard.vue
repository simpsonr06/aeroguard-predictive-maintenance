<script setup lang="ts">
defineProps<{
  title: string
  tooltip?: string
  value: string | number
  unit?: string
  statusType?: 'critical' | 'warning' | 'nominal' | 'neutral'
  statusLabel?: string
  comparison?: string
  accentColor?: string // e.g. '#ef4444', '#f59e0b', '#10b981', '#14b8a6', '#64748b'
}>()
</script>

<template>
  <div
    class="relative rounded-lg bg-slate-900/90 border border-slate-800/90 p-4 transition-all duration-150 flex flex-col justify-between"
    :style="accentColor ? { borderTop: `3px solid ${accentColor}` } : {}"
  >
    <!-- Title + Description affordance -->
    <div class="flex items-center justify-between gap-2">
      <UTooltip v-if="tooltip" :text="tooltip">
        <span class="text-xs uppercase font-medium tracking-wider text-slate-400 border-b border-dotted border-slate-600 hover:border-slate-400 cursor-help transition-colors">
          {{ title }}
        </span>
      </UTooltip>
      <span v-else class="text-xs uppercase font-medium tracking-wider text-slate-400">
        {{ title }}
      </span>

      <!-- Semantic 6px dot status if provided -->
      <div v-if="statusType && statusLabel" class="inline-flex items-center gap-1.5">
        <span
          class="size-1.5 rounded-full shrink-0"
          :class="[
            statusType === 'critical' ? 'bg-red-400' :
            statusType === 'warning' ? 'bg-amber-400' :
            statusType === 'nominal' ? 'bg-emerald-400' : 'bg-slate-400'
          ]"
        />
        <span class="text-[11px] text-slate-300 font-medium">{{ statusLabel }}</span>
      </div>
    </div>

    <!-- Quiet subtle divider -->
    <div class="my-2 border-t border-slate-800/80"></div>

    <!-- Primary Metric Value -->
    <div class="flex items-baseline gap-2">
      <span class="text-3xl font-bold font-mono text-slate-100 tabular-nums">
        {{ value }}
      </span>
      <span v-if="unit" class="text-xs text-slate-400 font-sans">
        {{ unit }}
      </span>
    </div>

    <!-- Comparison / Context line -->
    <div v-if="comparison" class="mt-2 text-[11px] text-slate-400 font-sans flex items-center justify-between">
      <span>{{ comparison }}</span>
      <slot name="delta" />
    </div>
  </div>
</template>
