<template>
  <body
    class="bg-gradient-to-br from-slate-600 via-slate-500 to-emerald-300 min-h-screen text-slate-800 font-sans antialiased overflow-hidden"
  >
    <div class="flex h-screen w-full relative">
      <!-- Sidebar -->
      <AdminSidebar ref="sidebarRef" :active-page="activePage" />

      <!-- Mobile Backdrop -->
      <div
        id="mobileBackdrop"
        ref="backdropRef"
        class="fixed inset-0 bg-black/20 backdrop-blur-sm z-40 hidden lg:hidden transition-opacity duration-300 opacity-0"
        @click="closeSidebar"
      ></div>

      <!-- Main Content -->
      <main class="flex-1 h-full relative overflow-y-auto overflow-x-hidden scroll-smooth bg-transparent">
        <!-- Mobile Header -->
        <AdminMobileHeader :title="mobileTitle" @open-sidebar="openSidebar" />

        <!-- Page Content -->
        <slot />

        <!-- Floating Language Selector -->
        <ClientOnly>
          <GTranslateWidget />
        </ClientOnly>
      </main>
    </div>
  </body>
</template>

<script setup>
const route = useRoute()

const props = defineProps({
  mobileTitle: { type: String, default: 'UAL Admin' },
})

const activePage = computed(() => {
  const path = route.path.replace('/', '')
  return path || 'admin'
})

const sidebarRef = ref(null)
const backdropRef = ref(null)

const openSidebar = () => {
  sidebarRef.value?.openSidebar()
  if (backdropRef.value) {
    backdropRef.value.classList.remove('hidden')
    setTimeout(() => backdropRef.value?.classList.remove('opacity-0'), 10)
  }
}

const closeSidebar = () => {
  sidebarRef.value?.closeSidebar()
  if (backdropRef.value) {
    backdropRef.value.classList.add('opacity-0')
    setTimeout(() => backdropRef.value?.classList.add('hidden'), 300)
  }
}

provide('openSidebar', openSidebar)
provide('closeSidebar', closeSidebar)
</script>
