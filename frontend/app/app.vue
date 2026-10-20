<script setup lang="ts">
const colorMode = useColorMode()
colorMode.preference = 'dark'

const color = computed(() => '#080d1a')

useHead({
  meta: [
    { charset: 'utf-8' },
    { name: 'viewport', content: 'width=device-width, initial-scale=1' },
    { key: 'theme-color', name: 'theme-color', content: color }
  ],
  link: [
    { rel: 'icon', href: '/favicon.svg', type: 'image/svg+xml' }
  ],
  htmlAttrs: {
    lang: 'en',
    class: 'dark'
  }
})

const title = 'AeroGuard 2.0 — Predictive Maintenance Operations'
const description = 'Enterprise turbofan fleet predictive maintenance and causal Remaining Useful Life (RUL) analytics on NASA C-MAPSS FD001 benchmark data.'

useSeoMeta({
  title,
  description,
  ogTitle: title,
  ogDescription: description
})
</script>

<template>
  <UApp>
    <NuxtLoadingIndicator color="#14b8a6" />

    <NuxtLayout>
      <NuxtPage />
    </NuxtLayout>
  </UApp>
</template>
