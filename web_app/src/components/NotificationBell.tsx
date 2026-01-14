import { useNavigate } from 'react-router-dom'
import {
  Bell,
  Check,
  AlertCircle,
  CheckCircle,
  UserPlus,
  MessageSquare,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useNotifications, type NotificationType } from '@/contexts/NotificationContext'
import { cn } from '@/lib/utils'

function getNotificationIcon(type: NotificationType) {
  switch (type) {
    case 'revision_requested':
      return AlertCircle
    case 'revision_responded':
      return MessageSquare
    case 'review_completed':
      return CheckCircle
    case 'project_assigned':
      return UserPlus
  }
}

function getNotificationColor(type: NotificationType) {
  switch (type) {
    case 'revision_requested':
      return 'text-amber-500'
    case 'revision_responded':
      return 'text-blue-500'
    case 'review_completed':
      return 'text-green-500'
    case 'project_assigned':
      return 'text-purple-500'
  }
}

function formatTimeAgo(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / (1000 * 60))
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffMins < 1) return 'just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`

  return date.toLocaleDateString('en-AU', { day: 'numeric', month: 'short' })
}

export function NotificationBell() {
  const navigate = useNavigate()
  const { notifications, unreadCount, markAsRead, markAllAsRead } = useNotifications()

  const handleNotificationClick = (notification: (typeof notifications)[0]) => {
    markAsRead(notification.id)
    if (notification.link) {
      navigate(notification.link)
    }
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="h-5 w-5" />
          {unreadCount > 0 && (
            <span className="absolute -top-0.5 -right-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-destructive text-[10px] font-medium text-destructive-foreground">
              {unreadCount > 9 ? '9+' : unreadCount}
            </span>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-80">
        <DropdownMenuLabel className="flex items-center justify-between">
          <span>Notifications</span>
          {unreadCount > 0 && (
            <Button
              variant="ghost"
              size="sm"
              className="h-auto py-1 px-2 text-xs"
              onClick={(e) => {
                e.preventDefault()
                markAllAsRead()
              }}
            >
              <Check className="h-3 w-3 mr-1" />
              Mark all read
            </Button>
          )}
        </DropdownMenuLabel>
        <DropdownMenuSeparator />

        {notifications.length === 0 ? (
          <div className="py-8 text-center text-sm text-muted-foreground">
            <Bell className="h-8 w-8 mx-auto mb-2 opacity-30" />
            No notifications
          </div>
        ) : (
          <ScrollArea className="h-[300px]">
            {notifications.map((notification) => {
              const Icon = getNotificationIcon(notification.type)
              const iconColor = getNotificationColor(notification.type)

              return (
                <DropdownMenuItem
                  key={notification.id}
                  className={cn(
                    'flex items-start gap-3 p-3 cursor-pointer',
                    !notification.read && 'bg-muted/50'
                  )}
                  onClick={() => handleNotificationClick(notification)}
                >
                  <Icon className={cn('h-5 w-5 mt-0.5 shrink-0', iconColor)} />
                  <div className="flex-1 space-y-1">
                    <p className={cn('text-sm', !notification.read && 'font-medium')}>
                      {notification.title}
                    </p>
                    <p className="text-xs text-muted-foreground line-clamp-2">
                      {notification.message}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {formatTimeAgo(notification.createdAt)}
                    </p>
                  </div>
                  {!notification.read && (
                    <div className="h-2 w-2 rounded-full bg-primary shrink-0 mt-1.5" />
                  )}
                </DropdownMenuItem>
              )
            })}
          </ScrollArea>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
