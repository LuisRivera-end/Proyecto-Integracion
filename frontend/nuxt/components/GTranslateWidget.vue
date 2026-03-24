<template>
  <div class="fixed bottom-6 right-6 z-50">
    <div class="gtranslate_wrapper" title="Cambiar idioma"></div>
  </div>
</template>

<script setup lang="ts">
/**
 * Componente GTranslateWidget
 * Configura y monta el widget flotante de Google Translate (GTranslate) en la parte inferior derecha.
 */
onMounted(() => {
  // Configure GTranslate
  ;(window as any).gtranslateSettings = {
    default_language: 'es',
    native_language_names: true,
    languages: ['es', 'en', 'fr', 'pt', 'it', 'de', 'ru', 'zh-CN', 'ar', 'vi'],
    wrapper_selector: '.gtranslate_wrapper',
    switcher_horizontal_position: 'right',
    switcher_vertical_position: 'bottom',
    float_switcher_open_direction: 'top',
    alt_flags: { es: 'mexico' },
  }

  // Load GTranslate script
  if (!document.querySelector('script[src*="gtranslate"]')) {
    const script = document.createElement('script')
    script.src = 'https://cdn.gtranslate.net/widgets/latest/float.js'
    script.defer = true
    document.body.appendChild(script)
  }
})
</script>
