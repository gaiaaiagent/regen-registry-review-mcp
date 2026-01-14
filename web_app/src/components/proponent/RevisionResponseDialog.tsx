import { useState } from 'react'
import { Upload, Loader2 } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import type { RevisionRequest } from '@/lib/mockProponentData'

interface RevisionResponseDialogProps {
  revision: RevisionRequest | null
  open: boolean
  onOpenChange: (open: boolean) => void
  onSubmit: (response: { comment: string; documentId?: string }) => Promise<void>
  isSubmitting: boolean
}

export function RevisionResponseDialog({
  revision,
  open,
  onOpenChange,
  onSubmit,
  isSubmitting,
}: RevisionResponseDialogProps) {
  const [comment, setComment] = useState('')
  const [fileName, setFileName] = useState<string | null>(null)

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setFileName(file.name)
    }
  }

  const handleSubmit = async () => {
    if (!comment.trim()) return

    await onSubmit({
      comment: comment.trim(),
      documentId: fileName ? `doc-${Date.now()}` : undefined,
    })

    // Reset form
    setComment('')
    setFileName(null)
  }

  const handleClose = () => {
    if (!isSubmitting) {
      setComment('')
      setFileName(null)
      onOpenChange(false)
    }
  }

  if (!revision) return null

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Respond to Revision Request</DialogTitle>
          <DialogDescription>
            Provide your response and optionally upload supporting documents.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="rounded-lg bg-muted/50 p-3">
            <div className="flex items-center gap-2 mb-2">
              <Badge variant="outline" className="text-xs font-mono">
                {revision.requirement_id}
              </Badge>
              <span className="font-medium text-sm">{revision.title}</span>
            </div>
            <p className="text-sm text-muted-foreground">{revision.description}</p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="comment">Your Response</Label>
            <Textarea
              id="comment"
              placeholder="Explain how you've addressed this revision request..."
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              className="min-h-[100px]"
              disabled={isSubmitting}
            />
          </div>

          <div className="space-y-2">
            <Label>Supporting Document (Optional)</Label>
            <div className="border-2 border-dashed rounded-lg p-4 text-center">
              {fileName ? (
                <div className="flex items-center justify-between">
                  <span className="text-sm">{fileName}</span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setFileName(null)}
                    disabled={isSubmitting}
                  >
                    Remove
                  </Button>
                </div>
              ) : (
                <label className="cursor-pointer block">
                  <input
                    type="file"
                    accept=".pdf"
                    onChange={handleFileSelect}
                    className="hidden"
                    disabled={isSubmitting}
                  />
                  <div className="flex flex-col items-center gap-2 text-muted-foreground">
                    <Upload className="h-8 w-8" />
                    <span className="text-sm">Click to upload PDF</span>
                    <span className="text-xs">or drag and drop</span>
                  </div>
                </label>
              )}
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleClose} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={!comment.trim() || isSubmitting}
          >
            {isSubmitting ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Submitting...
              </>
            ) : (
              'Submit Response'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
