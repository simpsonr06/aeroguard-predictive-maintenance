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

const { getHealth, apiBase } = useAeroGuardApi()
const isConnected = ref<boolean | null>(null)
const isChecking = ref(false)

async function checkApiConnection() {
  isChecking.value = true
  try {
    const res = await getHealth()
    isConnected.value = res.status === 'healthy'
  } catch {
    isConnected.value = false
  } finally {
    isChecking.value = false
  }
}

let healthInterval: any = null

onMounted(() => {
  checkApiConnection()
  healthInterval = setInterval(checkApiConnection, 20000)
})

onUnmounted(() => {
  if (healthInterval) clearInterval(healthInterval)
})
</script>

<template>
  <div class="flex flex-col min-h-screen">
    <!-- Top Warning Banner when API is disconnected -->
    <div
      v-if="isConnected === false"
      class="bg-amber-950/90 border-b border-amber-800/80 px-4 py-2 flex items-center justify-between text-xs text-amber-200 z-50 shrink-0"
    >
      <div class="flex items-center gap-2">
        <span class="size-2 rounded-full bg-amber-400 animate-pulse"></span>
        <span>
          <strong>FastAPI Backend Disconnected:</strong> Cannot connect to
          <code class="bg-black/30 px-1 py-0.5 rounded text-amber-300 font-mono">{{ apiBase }}</code>.
          Prognostic inference and telemetry streams may be offline or serving stale cached observations.
        </span>
      </div>
      <UButton
        size="xs"
        color="neutral"
        variant="ghost"
        icon="i-lucide-refresh-cw"
        :loading="isChecking"
        @click="checkApiConnection"
      >
        Retry
      </UButton>
    </div>

    <UDashboardGroup unit="rem" class="flex-1">
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
                <span
                  class="size-1.5 rounded-full"
                  :class="isConnected === true ? 'bg-emerald-400' : isConnected === false ? 'bg-red-400' : 'bg-amber-400 animate-pulse'"
                ></span>
                <span
                  class="text-[10px] font-mono"
                  :class="isConnected === true ? 'text-teal-400' : isConnected === false ? 'text-red-400' : 'text-amber-400'"
                >
                  {{ isConnected === true ? 'FastAPI Connected' : isConnected === false ? 'FastAPI Offline' : 'Connecting...' }}
                </span>
              </div>
            </div>
            <UColorModeButton />
          </div>
        </template>
      </UDashboardSidebar>

      <UDashboardSearch :groups="groups" />

      <slot />
    </UDashboardGroup>
  </div>
</template>
