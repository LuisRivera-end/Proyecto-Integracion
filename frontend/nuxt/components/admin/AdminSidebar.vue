<template>
  <aside
    id="sidebar"
    ref="sidebarEl"
    class="w-72 h-full flex flex-col bg-white border-r border-slate-200 shadow-xl z-50 transition-transform duration-300 fixed inset-y-0 left-0 transform -translate-x-full lg:translate-x-0 lg:relative lg:flex"
  >
    <!-- Header -->
    <div class="px-6 py-6 border-b border-slate-100 relative flex flex-col items-center bg-white">
      <button
        id="closeSidebar"
        class="lg:hidden text-slate-400 hover:text-slate-600 absolute right-4 top-4"
        @click="closeSidebar"
      >
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
      <div class="flex flex-col items-center gap-2 cursor-default hover:scale-105 transition-transform duration-300">
        <img src="/ual_no_fondo.png" alt="UAL" class="h-20 w-auto object-contain" />
        <p class="text-xs text-emerald-600 font-bold tracking-[0.2em] uppercase">
          {{ panelLabel }}
        </p>
      </div>
    </div>

  <!-- Navigation -->
  <nav class="flex-1 overflow-y-auto py-6 px-4 space-y-2 custom-scrollbar bg-white">
    <NuxtLink
      to="/dashboard"
      class="flex items-center gap-4 px-5 py-3.5 rounded-xl transition-all duration-200 group relative overflow-hidden"
      :class="activePage === 'dashboard'
        ? 'bg-emerald-50 text-emerald-800 shadow-sm border border-emerald-100'
        : 'text-slate-600 hover:text-emerald-700 hover:bg-emerald-50/80'"
    >
      <svg
        class="w-6 h-6 transition-colors duration-300"
        :class="activePage === 'dashboard' ? 'text-emerald-600' : 'text-slate-400 group-hover:text-emerald-500'"
        fill="none" stroke="currentColor" viewBox="0 0 24 24"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
      <span class="font-bold tracking-wide text-sm relative z-10">Dashboard</span>
      <div v-if="activePage === 'dashboard'" class="absolute right-4 top-1/2 -translate-y-1/2 w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></div>
    </NuxtLink>

    <NuxtLink
      to="/pantalla"
        class="flex items-center gap-4 px-5 py-3.5 rounded-xl transition-all duration-200 group relative overflow-hidden"
        :class="activePage === 'pantalla'
          ? 'bg-emerald-50 text-emerald-800 shadow-sm border border-emerald-100'
          : 'text-slate-600 hover:text-emerald-700 hover:bg-emerald-50/80'"
      >
        <svg
          class="w-6 h-6 transition-colors duration-300"
          :class="activePage === 'pantalla' ? 'text-emerald-600' : 'text-slate-400 group-hover:text-emerald-500'"
          fill="none" stroke="currentColor" viewBox="0 0 24 24"
        >
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
        </svg>
        <span class="font-bold tracking-wide text-sm relative z-10">Ver Pantalla</span>
        <div v-if="activePage === 'pantalla'" class="absolute right-4 top-1/2 -translate-y-1/2 w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></div>
      </NuxtLink>

      <NuxtLink
        :to="empleadosHref"
        class="flex items-center gap-4 px-5 py-3.5 rounded-xl transition-all duration-200 group relative overflow-hidden"
        :class="activePage === 'empleados' || activePage === 'subjefes'
          ? 'bg-emerald-50 text-emerald-800 shadow-sm border border-emerald-100'
          : 'text-slate-600 hover:text-emerald-700 hover:bg-emerald-50/80'"
      >
        <svg
          class="w-6 h-6 transition-colors duration-300"
          :class="(activePage === 'empleados' || activePage === 'subjefes') ? 'text-emerald-600 relative z-10' : 'text-slate-400 group-hover:text-emerald-500'"
          fill="none" stroke="currentColor" viewBox="0 0 24 24"
        >
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
        </svg>
        <span class="font-bold tracking-wide text-sm relative z-10">Empleados</span>
        <div v-if="activePage === 'empleados' || activePage === 'subjefes'" class="absolute right-4 top-1/2 -translate-y-1/2 w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></div>
      </NuxtLink>

      <NuxtLink
        to="/historial"
        class="flex items-center gap-4 px-5 py-3.5 rounded-xl transition-all duration-200 group relative overflow-hidden"
        :class="activePage === 'historial'
          ? 'bg-emerald-50 text-emerald-800 shadow-sm border border-emerald-100'
          : 'text-slate-600 hover:text-emerald-700 hover:bg-emerald-50/80'"
      >
        <svg
          class="w-6 h-6 transition-colors duration-300"
          :class="activePage === 'historial' ? 'text-emerald-600 relative z-10' : 'text-slate-400 group-hover:text-emerald-500'"
          fill="none" stroke="currentColor" viewBox="0 0 24 24"
        >
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M4 4h16v16H4V4zM4 9h16M4 15h16M9 4v16M15 4v16" />
        </svg>
        <span class="font-bold tracking-wide text-sm relative z-10">Historial de Tickets</span>
        <div v-if="activePage === 'historial'" class="absolute right-4 top-1/2 -translate-y-1/2 w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></div>
      </NuxtLink>

      <!-- Separator & Departamentos (hidden for subjefe) -->
      <template v-if="!isSubjefe">
        <div class="my-4 mx-5 border-t border-slate-100"></div>

        <NuxtLink
          to="/admin"
          class="flex items-center gap-4 px-5 py-3.5 rounded-xl transition-all duration-200 group relative overflow-hidden"
          :class="activePage === 'admin'
            ? 'bg-emerald-50 text-emerald-800 shadow-sm border border-emerald-100'
            : 'text-slate-600 hover:text-emerald-700 hover:bg-emerald-50/80'"
        >
          <svg
            class="w-6 h-6 transition-colors duration-300"
            :class="activePage === 'admin' ? 'text-emerald-600 relative z-10' : 'text-slate-400 group-hover:text-emerald-500'"
            fill="none" stroke="currentColor" viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
          <span class="font-bold tracking-wide text-sm relative z-10">Departamentos</span>
          <div v-if="activePage === 'admin'" class="absolute right-4 top-1/2 -translate-y-1/2 w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></div>
        </NuxtLink>
      </template>
    </nav>

    <!-- Footer: User Info + Cerrar Sesión -->
    <div class="border-t border-slate-200 bg-slate-50 flex-shrink-0 mt-auto">
      <div class="w-full px-8 py-4 flex items-center gap-4">
        <div
          class="w-10 h-10 rounded-full bg-emerald-100 border border-emerald-200 flex items-center justify-center text-emerald-700 text-sm font-bold shadow-sm"
        >
          {{ avatarLetter }}
        </div>
        <div class="flex-1 min-w-0">
          <p class="text-sm font-bold text-slate-800 truncate">{{ displayName }}</p>
          <p class="text-[11px] font-bold text-slate-400 uppercase tracking-wider truncate">
            {{ roleLabel }}
          </p>
        </div>
      </div>
      <div class="px-4 pb-4">
        <button
          @click="handleLogout"
          class="w-full px-5 py-2.5 rounded-xl bg-slate-100 hover:bg-red-50 text-slate-600 hover:text-red-600 font-bold text-xs uppercase tracking-wider transition-all hover:shadow-md flex items-center justify-center gap-2 group/btn"
        >
          <svg class="w-4 h-4 transition-transform group-hover/btn:-translate-x-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
          Cerrar Sesión
        </button>
      </div>
    </div>
  </aside>
</template>

<script setup>
const props = defineProps({
  activePage: { type: String, required: true },
})

const { logoutWithOverlay, getCurrentUser } = useAuth()

const currentUser = ref(null)

onMounted(() => {
  currentUser.value = getCurrentUser()
})

const isSubjefe = computed(() => currentUser.value?.rol === 6)

const panelLabel = computed(() => isSubjefe.value ? 'Panel Jefe' : 'Admin Panel')

const empleadosHref = computed(() => isSubjefe.value ? '/subjefes' : '/empleados')

const displayName = computed(() => {
  if (isSubjefe.value) {
    return currentUser.value?.username || 'Jefe'
  }
  return 'Admin User'
})

const avatarLetter = computed(() => {
  const name = displayName.value
  return name.charAt(0).toUpperCase()
})

const roleLabel = computed(() => {
  if (isSubjefe.value) {
    return currentUser.value?.sector || 'Sector'
  }
  return 'Sistema'
})

const sidebarEl = ref(null)

const openSidebar = () => {
  sidebarEl.value?.classList.remove('-translate-x-full')
}

const closeSidebar = () => {
  sidebarEl.value?.classList.add('-translate-x-full')
}

const handleLogout = () => {
  logoutWithOverlay()
}

defineExpose({ openSidebar, closeSidebar })
</script>
