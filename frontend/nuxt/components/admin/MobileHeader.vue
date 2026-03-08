<template>
  <div
    class="lg:hidden flex items-center justify-between p-4 bg-white/10 backdrop-blur-md shadow-sm border-b border-white/10 sticky top-0 z-30"
  >
    <button
      id="openSidebar"
      class="text-slate-800 p-2 rounded-lg hover:bg-white/20 transition-colors"
      @click="$emit('openSidebar')"
    >
      <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
      </svg>
    </button>
    <h1 class="text-xl font-bold text-slate-800 tracking-tight">{{ title }}</h1>
    <div class="w-8"></div>
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
})
defineEmits(['openSidebar'])
</script>
