import { useState, useCallback, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Skeleton } from '@/components/ui/skeleton'
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
  HardDrive,
  Folder,
  FileText,
  ChevronRight,
  ChevronLeft,
  AlertCircle,
  Loader2,
  Check,
} from 'lucide-react'
import {
  useGDriveFolders,
  useGDriveFolderContents,
  useGDriveImport,
  formatFileSize,
  formatModifiedTime,
  type GDriveFile,
  type GDriveFolder,
} from '@/hooks/useGoogleDrive'
import { cn } from '@/lib/utils'

interface GDriveImportDialogProps {
  sessionId: string
  existingFilenames?: Set<string>
  onImportComplete?: (importedCount: number) => void
  trigger?: React.ReactNode
}

interface BreadcrumbItem {
  id: string
  name: string
}

function normalizeFilename(filename: string): string {
  return filename
    .toLowerCase()
    .trim()
    .replace(/\s+/g, '_')
    .replace(/_+/g, '_') // Replace multiple underscores with one
}

export function GDriveImportDialog({
  sessionId,
  existingFilenames = new Set(),
  onImportComplete,
  trigger,
}: GDriveImportDialogProps) {
  const [open, setOpen] = useState(false)
  const [currentFolderId, setCurrentFolderId] = useState<string | null>(null)
  const [breadcrumbs, setBreadcrumbs] = useState<BreadcrumbItem[]>([])
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set())

  const normalizedExisting = new Set(Array.from(existingFilenames).map(normalizeFilename))

  const { data: foldersData, isLoading: foldersLoading, error: foldersError } = useGDriveFolders()
  const {
    data: folderContents,
    isLoading: contentsLoading,
    error: contentsError,
  } = useGDriveFolderContents(currentFolderId)

  const importMutation = useGDriveImport(sessionId)

  const handleOpenChange = (newOpen: boolean) => {
    if (!newOpen) {
      setCurrentFolderId(null)
      setBreadcrumbs([])
      setSelectedFiles(new Set())
      importMutation.reset()
    }
    setOpen(newOpen)
  }

  const navigateToFolder = useCallback((folder: GDriveFolder) => {
    setBreadcrumbs((prev) => [...prev, { id: folder.id, name: folder.name }])
    setCurrentFolderId(folder.id)
    setSelectedFiles(new Set())
  }, [])

  const navigateBack = useCallback(() => {
    if (breadcrumbs.length === 0) {
      setCurrentFolderId(null)
      return
    }
    const newBreadcrumbs = [...breadcrumbs]
    newBreadcrumbs.pop()
    setBreadcrumbs(newBreadcrumbs)
    setCurrentFolderId(newBreadcrumbs.length > 0 ? newBreadcrumbs[newBreadcrumbs.length - 1].id : null)
    setSelectedFiles(new Set())
  }, [breadcrumbs])

  const navigateToBreadcrumb = useCallback((index: number) => {
    if (index === -1) {
      setCurrentFolderId(null)
      setBreadcrumbs([])
      setSelectedFiles(new Set())
      return
    }
    const newBreadcrumbs = breadcrumbs.slice(0, index + 1)
    setBreadcrumbs(newBreadcrumbs)
    setCurrentFolderId(newBreadcrumbs[index].id)
    setSelectedFiles(new Set())
  }, [breadcrumbs])

  const toggleFileSelection = useCallback((fileId: string) => {
    setSelectedFiles((prev) => {
      const newSet = new Set(prev)
      if (newSet.has(fileId)) {
        newSet.delete(fileId)
      } else {
        newSet.add(fileId)
      }
      return newSet
    })
  }, [])

  const selectAllFiles = useCallback(() => {
    if (!folderContents?.files) return
    const allIds = folderContents.files
      .filter(f => !normalizedExisting.has(normalizeFilename(f.name)))
      .map((f) => f.id)
    setSelectedFiles(new Set(allIds))
  }, [folderContents, normalizedExisting])

  const deselectAllFiles = useCallback(() => {
    setSelectedFiles(new Set())
  }, [])

  const handleImport = async () => {
    if (!currentFolderId || selectedFiles.size === 0) return

    try {
      const result = await importMutation.mutateAsync({
        folderId: currentFolderId,
        fileIds: Array.from(selectedFiles),
      })
      onImportComplete?.(result.imported_count)
      handleOpenChange(false)
    } catch {
      // Error is handled by mutation state
    }
  }

  const isLoading = foldersLoading || contentsLoading
  const error = foldersError || contentsError

  const folders = currentFolderId === null ? foldersData?.folders : folderContents?.subfolders
  const files = folderContents?.files

  const selectableFiles = files?.filter(f => !normalizedExisting.has(normalizeFilename(f.name))) || []
  const allFilesSelected = selectableFiles.length > 0 && selectedFiles.size === selectableFiles.length

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        {trigger || (
          <Button variant="outline" size="sm">
            <HardDrive className="h-4 w-4 mr-2" />
            Import from Drive
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="sm:max-w-[600px] max-h-[80vh] flex flex-col bg-background">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <HardDrive className="h-5 w-5" />
            Import from Google Drive
          </DialogTitle>
          <DialogDescription>
            Browse folders and select PDF files to import into this session.
          </DialogDescription>
        </DialogHeader>

        {/* Breadcrumb navigation */}
        <div className="flex items-center gap-1 text-sm text-muted-foreground px-1 py-2 bg-muted/30 rounded-md overflow-x-auto">
          <button
            onClick={() => navigateToBreadcrumb(-1)}
            className={cn(
              'hover:text-foreground transition-colors shrink-0',
              currentFolderId === null && 'text-foreground font-medium'
            )}
          >
            Shared Folders
          </button>
          {breadcrumbs.map((crumb, index) => (
            <span key={crumb.id} className="flex items-center gap-1 shrink-0">
              <ChevronRight className="h-4 w-4 shrink-0" />
              <button
                onClick={() => navigateToBreadcrumb(index)}
                className={cn(
                  'hover:text-foreground transition-colors truncate max-w-[150px]',
                  index === breadcrumbs.length - 1 && 'text-foreground font-medium'
                )}
              >
                {crumb.name}
              </button>
            </span>
          ))}
        </div>

        {/* Content area */}
        <div className="flex-1 min-h-0">
          {error && (
            <div className="flex items-center gap-2 p-4 text-sm text-destructive bg-destructive/10 rounded-md">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>
                {error instanceof Error ? error.message : 'Failed to load Google Drive contents'}
              </span>
            </div>
          )}

          {isLoading && (
            <div className="space-y-2 p-2">
              {[1, 2, 3, 4].map((i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          )}

          {!isLoading && !error && (
            <ScrollArea className="h-[300px] pr-4">
              {/* Folders */}
              {folders && folders.length > 0 && (
                <div className="mb-4">
                  {currentFolderId !== null && (
                    <div className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2 px-1">
                      Folders
                    </div>
                  )}
                  <div className="space-y-1">
                    {folders.map((folder) => (
                      <button
                        key={folder.id}
                        onClick={() => navigateToFolder(folder)}
                        className="w-full flex items-center gap-3 px-3 py-2 text-left rounded-md hover:bg-accent transition-colors"
                      >
                        <Folder className="h-5 w-5 text-blue-500 shrink-0" />
                        <span className="flex-1 truncate">{folder.name}</span>
                        <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0" />
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Files */}
              {files && files.length > 0 && (
                <div>
                  <div className="flex items-center justify-between mb-2 px-1">
                    <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                      PDF Files ({files.length})
                    </span>
                    <button
                      onClick={allFilesSelected ? deselectAllFiles : selectAllFiles}
                      className="text-xs text-primary hover:underline"
                      disabled={selectableFiles.length === 0}
                    >
                      {allFilesSelected ? 'Deselect all' : 'Select all new'}
                    </button>
                  </div>
                  <div className="space-y-1">
                    {files.map((file) => (
                      <FileRow
                        key={file.id}
                        file={file}
                        isExisting={normalizedExisting.has(normalizeFilename(file.name))}
                        selected={selectedFiles.has(file.id)}
                        onToggle={() => toggleFileSelection(file.id)}
                      />
                    ))}
                  </div>
                </div>
              )}

              {/* Empty state */}
              {currentFolderId === null && (!folders || folders.length === 0) && (
                <div className="flex flex-col items-center justify-center py-8 text-center text-muted-foreground">
                  <Folder className="h-12 w-12 mb-3 opacity-30" />
                  <p className="font-medium">No shared folders found</p>
                  <p className="text-sm mt-1">
                    Share a folder with the service account to see it here.
                  </p>
                </div>
              )}

              {currentFolderId !== null && (!folders || folders.length === 0) && (!files || files.length === 0) && (
                <div className="flex flex-col items-center justify-center py-8 text-center text-muted-foreground">
                  <FileText className="h-12 w-12 mb-3 opacity-30" />
                  <p className="font-medium">This folder is empty</p>
                  <p className="text-sm mt-1">No PDF files or subfolders found.</p>
                </div>
              )}
            </ScrollArea>
          )}
        </div>

        {/* Import error */}
        {importMutation.isError && (
          <div className="flex items-center gap-2 p-3 text-sm text-destructive bg-destructive/10 rounded-md">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>
              {importMutation.error instanceof Error
                ? importMutation.error.message
                : 'Failed to import files'}
            </span>
          </div>
        )}

        {/* Import success */}
        {importMutation.isSuccess && (
          <div className="flex items-center gap-2 p-3 text-sm text-green-600 bg-green-50 dark:bg-green-900/20 rounded-md">
            <Check className="h-4 w-4 shrink-0" />
            <span>Successfully imported {importMutation.data?.imported_count} files</span>
          </div>
        )}

        <DialogFooter>
          {currentFolderId !== null && (
            <Button variant="outline" onClick={navigateBack} disabled={importMutation.isPending}>
              <ChevronLeft className="h-4 w-4 mr-1" />
              Back
            </Button>
          )}
          <div className="flex-1" />
          <Button
            variant="outline"
            onClick={() => handleOpenChange(false)}
            disabled={importMutation.isPending}
          >
            Cancel
          </Button>
          <Button
            onClick={handleImport}
            disabled={selectedFiles.size === 0 || importMutation.isPending}
          >
            {importMutation.isPending ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Importing...
              </>
            ) : (
              <>
                Import {selectedFiles.size > 0 ? `(${selectedFiles.size})` : ''}
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

interface FileRowProps {
  file: GDriveFile
  isExisting: boolean
  selected: boolean
  onToggle: () => void
}

function FileRow({ file, isExisting, selected, onToggle }: FileRowProps) {
  if (isExisting) {
    return (
      <div className="flex items-center gap-3 px-3 py-2 rounded-md bg-muted/30 opacity-60 cursor-not-allowed">
        <Checkbox checked={true} disabled />
        <FileText className="h-5 w-5 text-muted-foreground shrink-0" />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium truncate text-muted-foreground">{file.name}</p>
          <p className="text-xs text-muted-foreground">
            Already imported
          </p>
        </div>
      </div>
    )
  }

  return (
    <label
      className={cn(
        'flex items-center gap-3 px-3 py-2 rounded-md cursor-pointer transition-colors',
        selected ? 'bg-primary/10' : 'hover:bg-accent'
      )}
    >
      <Checkbox checked={selected} onCheckedChange={onToggle} />
      <FileText className="h-5 w-5 text-red-500 shrink-0" />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium truncate">{file.name}</p>
        <p className="text-xs text-muted-foreground">
          {formatFileSize(file.size)}
          {file.modified_time && ` - ${formatModifiedTime(file.modified_time)}`}
        </p>
      </div>
    </label>
  )
}
