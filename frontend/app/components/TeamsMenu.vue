<script setup lang="ts">
defineProps<{
  collapsed?: boolean
}>()
</script>

<template>
  <div class="flex items-center gap-2.5 px-1 py-1.5 overflow-hidden">
    <div class="flex items-center justify-center size-9 rounded-lg bg-teal-500/15 border border-teal-500/30 text-teal-400 shrink-0 shadow-xs">
      <UIcon name="i-lucide-plane-takeoff" class="size-5" />
    </div>

    <div v-if="!collapsed" class="flex flex-col min-w-0 text-left leading-tight">
      <div class="flex items-center gap-1.5">
        <span class="text-sm font-semibold text-slate-100 tracking-tight truncate">AeroGuard 2.0</span>
        <UBadge color="teal" variant="subtle" size="xs" class="font-mono text-[10px] px-1 py-0">FD001</UBadge>
      </div>
      <span class="text-[11px] text-slate-400 truncate">Predictive Operations</span>
    </div>
  </div>
</template>
