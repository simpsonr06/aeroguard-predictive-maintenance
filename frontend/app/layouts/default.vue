<script setup lang="ts">
import type { NavigationMenuItem } from '@nuxt/ui'

const open = ref(false)

const links = computed(() => [[
  {
    label: 'Fleet Command',
    icon: 'i-lucide-layout-dashboard',
    to: '/',
    onSelect: () => { open.value = false }
  },
  {
    label: 'Engine Digital Twin',
    icon: 'i-lucide-activity',
    to: '/engines',
    onSelect: () => { open.value = false }
  },
  {
    label: 'Sensor Intelligence',
    icon: 'i-lucide-gauge',
    to: '/sensors',
    onSelect: () => { open.value = false }
  },
  {
    label: 'Model Intelligence',
    icon: 'i-lucide-brain-circuit',
    to: '/models',
    onSelect: () => { open.value = false }
  },
  {
    label: 'Maintenance Ops',
    icon: 'i-lucide-wrench',
    to: '/maintenance',
    onSelect: () => { open.value = false }
  },
  {
    label: 'Inference Lab',
    icon: 'i-lucide-flask-conical',
    to: '/inference',
    onSelect: () => { open.value = false }
  }
], [
  {
    label: 'FastAPI Swagger',
    icon: 'i-lucide-terminal',
    to: 'http://localhost:8000/docs',
    target: '_blank'
  },
  {
    label: 'Streamlit App',
    icon: 'i-lucide-external-link',
    to: 'http://localhost:8501',
    target: '_blank'
  }
]] satisfies NavigationMenuItem[][])

const groups = computed(() => [{
  id: 'links',
  label: 'AeroGuard Navigation',
  items: links.value.flat()
}])
</script>

<template>
  <UDashboardGroup unit="rem">
    <UDashboardSidebar
      id="default"
      v-model:open="open"
      collapsible
      resizable
      class="bg-slate-950 border-r border-slate-800"
      :ui="{ footer: 'lg:border-t lg:border-slate-800' }"
    >
      <template #header="{ collapsed }">
        <TeamsMenu :collapsed="collapsed" />
      </template>

      <template #default="{ collapsed }">
        <UDashboardSearchButton :collapsed="collapsed" class="bg-slate-900/60 ring-1 ring-slate-800 hover:ring-teal-500/50" />

        <UNavigationMenu
          :collapsed="collapsed"
          :items="links[0]"
          orientation="vertical"
          tooltip
          popover
          class="mt-2 text-slate-300"
        />

        <div class="mt-auto pt-4 border-t border-slate-800/80">
          <UNavigationMenu
            :collapsed="collapsed"
            :items="links[1]"
            orientation="vertical"
            tooltip
            class="text-slate-400"
          />
        </div>
      </template>

      <template #footer="{ collapsed }">
        <div class="flex items-center justify-between w-full px-2 py-1.5">
          <div v-if="!collapsed" class="flex flex-col text-xs text-slate-400">
            <span class="font-medium text-slate-200">Ops Lead</span>
            <div class="flex items-center gap-1.5 mt-0.5">
              <span class="size-1.5 rounded-full bg-emerald-400"></span>
              <span class="text-[10px] text-teal-400 font-mono">FastAPI Connected</span>
            </div>
          </div>
          <UColorModeButton />
        </div>
      </template>
    </UDashboardSidebar>

    <UDashboardSearch :groups="groups" />

    <slot />
  </UDashboardGroup>
</template>
