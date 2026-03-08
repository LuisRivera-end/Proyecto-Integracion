export const useConfig = () => {
  const host = import.meta.client ? window.location.hostname : 'localhost'
  const LOCAL_HOSTS = ['localhost', '127.0.0.1']

  return {
    API_BASE_URL: LOCAL_HOSTS.includes(host)
      ? 'https://localhost:4443'
      : `https://${host}:4443`,
  }
}
