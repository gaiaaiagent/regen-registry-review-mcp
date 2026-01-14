import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8003'

// ============================================================================
// Types for existing Google Drive integration
// ============================================================================

export interface GDriveFile {
  id: string
  name: string
  mime_type: string
  size: number | null
  modified_time: string | null
}

export interface GDriveFolder {
  id: string
  name: string
}

export interface GDriveFoldersResponse {
  folders: GDriveFolder[]
  count: number
}

export interface GDriveFolderContentsResponse {
  folder_id: string
  files: GDriveFile[]
  subfolders: GDriveFolder[]
  file_count: number
  subfolder_count: number
}

export interface GDriveImportResult {
  success: boolean
  session_id: string
  imported: Array<{
    filename: string
    size_bytes: number
    gdrive_id: string
  }>
  imported_count: number
  failed: Array<{
    file_id: string
    error: string
  }>
  failed_count: number
  discovery: {
    documents_found: number
    classification_summary: Record<string, number>
  }
}

async function fetchWithAuth(url: string, options?: RequestInit) {
  const token = localStorage.getItem('auth_token')
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  const response = await fetch(url, { ...options, headers })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

/**
 * Fetch list of accessible Google Drive folders.
 */
export function useGDriveFolders() {
  return useQuery({
    queryKey: ['gdrive', 'folders'],
    queryFn: async (): Promise<GDriveFoldersResponse> => {
      return fetchWithAuth(`${API_URL}/gdrive/folders`)
    },
    staleTime: 1000 * 60 * 5, // 5 minutes
  })
}

/**
 * Fetch contents of a specific Google Drive folder.
 */
export function useGDriveFolderContents(folderId: string | null) {
  return useQuery({
    queryKey: ['gdrive', 'folder', folderId],
    queryFn: async (): Promise<GDriveFolderContentsResponse> => {
      if (!folderId) throw new Error('Folder ID required')
      return fetchWithAuth(`${API_URL}/gdrive/folders/${folderId}/files`)
    },
    enabled: !!folderId,
    staleTime: 1000 * 60 * 2, // 2 minutes
  })
}

/**
 * Import files from Google Drive to a session.
 */
export function useGDriveImport(sessionId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({
      folderId,
      fileIds,
    }: {
      folderId: string
      fileIds: string[]
    }): Promise<GDriveImportResult> => {
      return fetchWithAuth(`${API_URL}/sessions/${sessionId}/import/gdrive`, {
        method: 'POST',
        body: JSON.stringify({ folder_id: folderId, file_ids: fileIds }),
      })
    },
    onSuccess: () => {
      // Invalidate session data to refresh document list
      queryClient.invalidateQueries({ queryKey: ['session', sessionId] })
    },
  })
}

/**
 * Format file size for display.
 */
export function formatFileSize(bytes: number | null): string {
  if (bytes === null) return ''
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

/**
 * Format date for display.
 */
export function formatModifiedTime(isoString: string | null): string {
  if (!isoString) return ''
  const date = new Date(isoString)
  return date.toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

// ============================================================================
// Types for Project Discovery (Phase 10)
// ============================================================================

export interface ProjectManifest {
  project_name: string
  methodology: string
  project_id: string | null
  proponent: {
    name: string
    email: string
  } | null
  submitted_at: string | null
}

export interface DiscoveredProject {
  folder_id: string
  folder_name: string
  manifest: ProjectManifest
  pdf_count: number
  existing_session_id: string | null
}

export interface GDriveProjectsResponse {
  projects: DiscoveredProject[]
  count: number
  parent_folder_id: string
}

export interface CreateSessionFromProjectResponse {
  success: boolean
  session_id: string
  project_name: string
  methodology: string
  imported_count: number
  discovery_summary: {
    documents_found: number
    classification_summary: Record<string, number>
  }
}

// ============================================================================
// Hooks for Project Discovery
// ============================================================================

/**
 * Fetch discovered projects from Google Drive parent folder.
 * Projects are subfolders containing project_manifest.json.
 */
export function useGDriveProjects(parentFolderId?: string) {
  return useQuery({
    queryKey: ['gdrive', 'projects', parentFolderId],
    queryFn: async (): Promise<GDriveProjectsResponse> => {
      const url = parentFolderId
        ? `${API_URL}/gdrive/projects?parent_folder_id=${encodeURIComponent(parentFolderId)}`
        : `${API_URL}/gdrive/projects`
      return fetchWithAuth(url)
    },
    staleTime: 1000 * 60 * 2, // 2 minutes
    retry: 1,
  })
}

/**
 * Create a review session from a discovered Google Drive project.
 * One-click import: creates session, imports all PDFs, runs discovery.
 */
export function useCreateSessionFromProject() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()

  return useMutation({
    mutationFn: async (folderId: string): Promise<CreateSessionFromProjectResponse> => {
      return fetchWithAuth(`${API_URL}/gdrive/projects/${folderId}/create-session`, {
        method: 'POST',
      })
    },
    onSuccess: (data) => {
      // Invalidate projects list and sessions list
      queryClient.invalidateQueries({ queryKey: ['gdrive', 'projects'] })
      queryClient.invalidateQueries({ queryKey: ['sessions'] })
      // Navigate to the new workspace
      navigate(`/workspace/${data.session_id}`)
    },
  })
}

/**
 * Format submission date for display.
 */
export function formatSubmittedDate(isoString: string | null | undefined): string {
  if (!isoString) return 'Unknown'
  const date = new Date(isoString)
  return date.toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}
