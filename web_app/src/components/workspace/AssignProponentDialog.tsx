import { useState } from 'react'
import { UserPlus, Loader2, Mail } from 'lucide-react'
import { toast } from 'sonner'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useAuth } from '@/contexts/AuthContext'
import {
  setProjectAssignment,
  assignProjectToProponent,
  getProjectAssignment,
} from '@/lib/mockProponentData'

interface AssignProponentDialogProps {
  sessionId: string
  projectName: string
  onAssign?: (email: string) => void
}

export function AssignProponentDialog({
  sessionId,
  projectName,
  onAssign,
}: AssignProponentDialogProps) {
  const { user } = useAuth()
  const [open, setOpen] = useState(false)
  const [email, setEmail] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const existingAssignment = getProjectAssignment(sessionId)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email.trim() || !user?.email) return

    setIsSubmitting(true)

    // Simulate network delay
    await new Promise((resolve) => setTimeout(resolve, 500))

    // Store assignment
    setProjectAssignment(sessionId, email.trim(), user.email)
    assignProjectToProponent(sessionId, email.trim(), projectName)

    // Create notification for proponent (stored in localStorage)
    const notificationKey = `notifications:${email.trim()}`
    const existingNotifications = JSON.parse(
      localStorage.getItem(notificationKey) || '[]'
    )
    existingNotifications.unshift({
      id: `notif-${Date.now()}`,
      type: 'project_assigned',
      title: 'New Project Assignment',
      message: `You have been assigned to review "${projectName}"`,
      link: `/proponent/project/${sessionId}`,
      read: false,
      createdAt: new Date().toISOString(),
    })
    localStorage.setItem(notificationKey, JSON.stringify(existingNotifications))

    toast.success('Proponent Assigned', {
      description: `${email.trim()} will be notified of their assignment.`,
    })

    onAssign?.(email.trim())
    setIsSubmitting(false)
    setOpen(false)
    setEmail('')
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm">
          <UserPlus className="h-4 w-4 mr-2" />
          {existingAssignment ? 'Reassign' : 'Assign Proponent'}
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Assign Proponent</DialogTitle>
          <DialogDescription>
            Assign an external proponent to this review session. They&apos;ll receive
            notifications and can respond to revision requests.
          </DialogDescription>
        </DialogHeader>

        {existingAssignment && (
          <div className="rounded-lg bg-muted p-3">
            <p className="text-sm font-medium">Current Assignment</p>
            <div className="flex items-center gap-2 mt-1 text-sm text-muted-foreground">
              <Mail className="h-4 w-4" />
              {existingAssignment.email}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Assigned by {existingAssignment.assignedBy} on{' '}
              {new Date(existingAssignment.assignedAt).toLocaleDateString()}
            </p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="proponent-email">Proponent Email</Label>
            <Input
              id="proponent-email"
              type="email"
              placeholder="proponent@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={isSubmitting}
            />
            <p className="text-xs text-muted-foreground">
              Demo accounts: proponent@example.com or test@carbonproject.org (password: demo123)
            </p>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setOpen(false)}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={!email.trim() || isSubmitting}>
              {isSubmitting ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Assigning...
                </>
              ) : (
                'Assign'
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
