import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from 'react'
import { useAuth } from './AuthContext'

export type NotificationType =
  | 'revision_requested'
  | 'revision_responded'
  | 'review_completed'
  | 'project_assigned'

export interface Notification {
  id: string
  type: NotificationType
  title: string
  message: string
  link?: string
  read: boolean
  createdAt: string
}

interface NotificationContextValue {
  notifications: Notification[]
  unreadCount: number
  markAsRead: (id: string) => void
  markAllAsRead: () => void
  addNotification: (notification: Omit<Notification, 'id' | 'read' | 'createdAt'>) => void
  clearNotifications: () => void
}

const NotificationContext = createContext<NotificationContextValue | null>(null)

const STORAGE_KEY_PREFIX = 'notifications:'

function getStorageKey(userEmail: string): string {
  return `${STORAGE_KEY_PREFIX}${userEmail}`
}

function loadNotifications(userEmail: string): Notification[] {
  try {
    const stored = localStorage.getItem(getStorageKey(userEmail))
    return stored ? JSON.parse(stored) : []
  } catch {
    return []
  }
}

function saveNotifications(userEmail: string, notifications: Notification[]): void {
  localStorage.setItem(getStorageKey(userEmail), JSON.stringify(notifications))
}

export function NotificationProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth()
  const [notifications, setNotifications] = useState<Notification[]>([])

  // Load notifications when user changes
  useEffect(() => {
    if (user?.email) {
      const loaded = loadNotifications(user.email)
      setNotifications(loaded)

      // Generate demo notifications for proponents on first load
      if (user.role === 'proponent' && loaded.length === 0) {
        const demoNotifications: Notification[] = [
          {
            id: 'notif-demo-1',
            type: 'revision_requested',
            title: 'Revision Requested',
            message: 'A reviewer has requested changes to your Botany Farm Carbon Project.',
            link: '/proponent/project/proj-001-botany',
            read: false,
            createdAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), // 2 hours ago
          },
          {
            id: 'notif-demo-2',
            type: 'review_completed',
            title: 'Review Completed',
            message: 'Queensland Regenerative Grazing has been approved!',
            link: '/proponent/project/proj-002-queensland',
            read: true,
            createdAt: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(), // 7 days ago
          },
        ]
        setNotifications(demoNotifications)
        saveNotifications(user.email, demoNotifications)
      }
    } else {
      setNotifications([])
    }
  }, [user?.email, user?.role])

  const markAsRead = useCallback(
    (id: string) => {
      if (!user?.email) return

      setNotifications((prev) => {
        const updated = prev.map((n) => (n.id === id ? { ...n, read: true } : n))
        saveNotifications(user.email, updated)
        return updated
      })
    },
    [user?.email]
  )

  const markAllAsRead = useCallback(() => {
    if (!user?.email) return

    setNotifications((prev) => {
      const updated = prev.map((n) => ({ ...n, read: true }))
      saveNotifications(user.email, updated)
      return updated
    })
  }, [user?.email])

  const addNotification = useCallback(
    (notification: Omit<Notification, 'id' | 'read' | 'createdAt'>) => {
      if (!user?.email) return

      const newNotification: Notification = {
        ...notification,
        id: `notif-${Date.now()}`,
        read: false,
        createdAt: new Date().toISOString(),
      }

      setNotifications((prev) => {
        const updated = [newNotification, ...prev]
        saveNotifications(user.email, updated)
        return updated
      })
    },
    [user?.email]
  )

  const clearNotifications = useCallback(() => {
    if (!user?.email) return

    setNotifications([])
    localStorage.removeItem(getStorageKey(user.email))
  }, [user?.email])

  const unreadCount = notifications.filter((n) => !n.read).length

  return (
    <NotificationContext.Provider
      value={{
        notifications,
        unreadCount,
        markAsRead,
        markAllAsRead,
        addNotification,
        clearNotifications,
      }}
    >
      {children}
    </NotificationContext.Provider>
  )
}

export function useNotifications(): NotificationContextValue {
  const context = useContext(NotificationContext)
  if (!context) {
    throw new Error('useNotifications must be used within a NotificationProvider')
  }
  return context
}
