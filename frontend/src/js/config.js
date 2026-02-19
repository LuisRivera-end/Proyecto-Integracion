// config.js
const Config = (() => {
  const host = window.location.hostname;

  const LOCAL_HOSTS = ["localhost", "127.0.0.1"];
  
  return {
    API_BASE_URL: LOCAL_HOSTS.includes(host)
      ? "http://localhost:8081"     // pruebas locales
      : `http://${host}:8081`,       // IP o DNS
  };
})();

export default Config;