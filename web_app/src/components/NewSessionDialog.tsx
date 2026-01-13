import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Plus, AlertCircle } from 'lucide-react'
import { useCreateSession, METHODOLOGIES, type MethodologyId } from '@/hooks/useSessions'

interface NewSessionDialogProps {
  onSuccess?: (sessionId: string) => void
}

export function NewSessionDialog({ onSuccess }: NewSessionDialogProps) {
  const [open, setOpen] = useState(false)
  const [projectName, setProjectName] = useState('')
  const [methodology, setMethodology] = useState<MethodologyId>('soil-carbon-v1.2.2')
  const [projectId, setProjectId] = useState('')

  const createSession = useCreateSession()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!projectName.trim()) return

    try {
      const result = await createSession.mutateAsync({
        project_name: projectName.trim(),
        methodology,
        project_id: projectId.trim() || undefined,
      })

      // Reset form
      setProjectName('')
      setProjectId('')
      setMethodology('soil-carbon-v1.2.2')
      setOpen(false)

      // Call success callback
      onSuccess?.(result.session_id)
    } catch {
      // Error is handled by mutation state
    }
  }

  const handleOpenChange = (newOpen: boolean) => {
    if (!newOpen) {
      // Reset form when closing
      setProjectName('')
      setProjectId('')
      setMethodology('soil-carbon-v1.2.2')
      createSession.reset()
    }
    setOpen(newOpen)
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="h-4 w-4 mr-2" />
          New Review
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[480px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Start New Review</DialogTitle>
            <DialogDescription>
              Create a new registry review session. You can upload documents after creating the session.
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            {/* Project Name */}
            <div className="grid gap-2">
              <Label htmlFor="project-name">
                Project Name <span className="text-destructive">*</span>
              </Label>
              <Input
                id="project-name"
                placeholder="e.g., Wilmot Cattle Company 22-23"
                value={projectName}
                onChange={(e) => setProjectName(e.target.value)}
                disabled={createSession.isPending}
                required
              />
            </div>

            {/* Methodology */}
            <div className="grid gap-2">
              <Label htmlFor="methodology">
                Methodology <span className="text-destructive">*</span>
              </Label>
              <Select
                value={methodology}
                onValueChange={(value) => setMethodology(value as MethodologyId)}
                disabled={createSession.isPending}
              >
                <SelectTrigger id="methodology">
                  <SelectValue placeholder="Select methodology" />
                </SelectTrigger>
                <SelectContent>
                  {METHODOLOGIES.map((m) => (
                    <SelectItem key={m.id} value={m.id}>
                      <div className="flex flex-col items-start">
                        <span>{m.name}</span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">
                {METHODOLOGIES.find(m => m.id === methodology)?.description}
              </p>
            </div>

            {/* Project ID (optional) */}
            <div className="grid gap-2">
              <Label htmlFor="project-id">
                Project ID <span className="text-muted-foreground">(optional)</span>
              </Label>
              <Input
                id="project-id"
                placeholder="e.g., C06-4997"
                value={projectId}
                onChange={(e) => setProjectId(e.target.value)}
                disabled={createSession.isPending}
              />
              <p className="text-xs text-muted-foreground">
                The registry project ID if known
              </p>
            </div>

            {/* Error display */}
            {createSession.isError && (
              <div className="flex items-center gap-2 p-3 text-sm text-destructive bg-destructive/10 rounded-md">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>
                  {createSession.error instanceof Error
                    ? createSession.error.message
                    : 'Failed to create session'}
                </span>
              </div>
            )}
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => handleOpenChange(false)}
              disabled={createSession.isPending}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={createSession.isPending || !projectName.trim()}
            >
              {createSession.isPending ? 'Creating...' : 'Create Session'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
