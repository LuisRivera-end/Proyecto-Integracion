// config.js
const Config = (() => {
  const host = window.location.hostname;

  const LOCAL_HOSTS = ["localhost", "127.0.0.1"];
  
  return {
    API_BASE_URL: LOCAL_HOSTS.includes(host)
      ? "https://localhost:4443"      // pruebas locales
      : `https://${host}:4443`,       // IP o DNS
  };
})();

export default Config;