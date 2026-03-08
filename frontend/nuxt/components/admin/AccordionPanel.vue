<template>
  <div class="rounded-xl border border-slate-200 overflow-hidden shadow-sm">
    <button
      :id="`header-${id}`"
      class="accordion-header w-full flex items-center justify-between px-6 py-4 bg-slate-50 hover:bg-slate-100 transition-colors cursor-pointer text-left"
      :class="{ open: isOpen }"
      @click="toggle"
    >
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 rounded-lg flex items-center justify-center" :class="iconBgClass">
          <slot name="icon"></slot>
        </div>
        <span class="font-bold text-slate-800">{{ title }}</span>
      </div>
      <svg
        class="accordion-arrow w-5 h-5 text-slate-400"
        :class="{ 'rotate-180': isOpen }"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
      </svg>
    </button>
    <div :id="`content-${id}`" class="accordion-content" :class="{ open: isOpen }">
      <slot></slot>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  id: { type: String, required: true },
  title: { type: String, required: true },
  iconBgClass: { type: String, default: 'bg-emerald-100' },
  defaultOpen: { type: Boolean, default: false },
})

const isOpen = ref(props.defaultOpen)

const toggle = () => {
  isOpen.value = !isOpen.value
}

defineExpose({ isOpen, open: () => { isOpen.value = true }, close: () => { isOpen.value = false } })
</script>

<style scoped>
.accordion-content {
  max-height: 0;
  overflow: hidden;
  transition: max-height 0.35s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.3s ease;
  opacity: 0;
}

.accordion-content.open {
  max-height: 9999px;
  opacity: 1;
}

.accordion-arrow {
  transition: transform 0.3s ease;
}
</style>
