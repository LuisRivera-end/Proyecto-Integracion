import { io, type Socket } from 'socket.io-client'

let socketInstance: Socket | null = null

export const useSocket = () => {
  if (socketInstance) return socketInstance

  const { API_BASE_URL } = useConfig()

  socketInstance = io(API_BASE_URL, {
    transports: ['websocket', 'polling'],
    withCredentials: true,
    rejectUnauthorized: false,
  })

  return socketInstance
}
