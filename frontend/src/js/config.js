// config.js
const Config = (() => {
  const host = window.location.hostname;

  return {
    // API base URL
    API_BASE_URL: (host === "localhost" || host === "127.0.0.1")
      ? "https://localhost:4443"        // pruebas locales
      : "https://192.168.17.1:4443",   // acceso desde LAN
  };
})();

export default Config;
