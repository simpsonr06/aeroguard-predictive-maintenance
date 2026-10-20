<script setup lang="ts">
defineProps<{
  title?: string
  narrative: string
  actionHint?: string
  badgeText?: string
  tone?: 'neutral' | 'info' | 'warning' | 'critical'
}>()
</script>

<template>
  <div
    class="rounded-lg p-3.5 border text-xs leading-relaxed flex items-start gap-3 transition-colors"
    :class="[
      tone === 'warning' ? 'bg-amber-950/20 border-amber-900/40 text-amber-200/90' :
      tone === 'critical' ? 'bg-red-950/25 border-red-900/45 text-red-200/90' :
      tone === 'info' ? 'bg-teal-950/20 border-teal-900/40 text-teal-200/90' :
      'bg-slate-900/80 border-slate-800 text-slate-300'
    ]"
  >
    <div class="mt-0.5 shrink-0">
      <UIcon
        :name="
          tone === 'critical' ? 'i-lucide-alert-triangle' :
          tone === 'warning' ? 'i-lucide-alert-circle' :
          tone === 'info' ? 'i-lucide-compass' : 'i-lucide-sparkles'
        "
        class="size-4"
        :class="[
          tone === 'critical' ? 'text-red-400' :
          tone === 'warning' ? 'text-amber-400' :
          tone === 'info' ? 'text-teal-400' : 'text-slate-400'
        ]"
      />
    </div>

    <div class="flex-1 space-y-1">
      <div class="flex items-center gap-2">
        <span class="font-semibold text-slate-100 tracking-tight">{{ title || 'Operational Decision Narrative' }}</span>
        <span v-if="badgeText" class="text-[10px] uppercase font-mono px-1.5 py-0.2 rounded border border-slate-700 text-slate-400">
          {{ badgeText }}
        </span>
      </div>
      <p class="text-slate-300">
        {{ narrative }}
      </p>
      <div v-if="actionHint" class="pt-0.5 text-[11px] font-medium" :class="tone === 'critical' ? 'text-red-300' : tone === 'warning' ? 'text-amber-300' : 'text-teal-300'">
        ↳ Suggested Action: {{ actionHint }}
      </div>
    </div>
  </div>
</template>
