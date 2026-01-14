import { useAuth } from '@/contexts/AuthContext'
import { useAssignedProjects } from '@/hooks/useProponentData'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { ProjectCard } from '@/components/proponent/ProjectCard'
import { NotificationBell } from '@/components/NotificationBell'
import { LogOut, Briefcase, FolderOpen, RefreshCw } from 'lucide-react'

export function ProponentDashboard() {
  const { user, signOut } = useAuth()
  const { projects, isLoading, refetch } = useAssignedProjects()

  const pendingCount = projects.filter((p) => p.pending_revisions > 0).length
  const underReviewCount = projects.filter((p) => p.status === 'under_review').length
  const approvedCount = projects.filter((p) => p.status === 'approved').length

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b bg-card sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Briefcase className="h-6 w-6 text-primary" />
            <h1 className="text-xl font-semibold">Proponent Portal</h1>
          </div>
          <div className="flex items-center gap-2">
            <NotificationBell />
            <span className="text-sm text-muted-foreground hidden sm:inline">{user?.email}</span>
            <Button variant="ghost" size="sm" onClick={signOut}>
              <LogOut className="h-4 w-4 mr-2" />
              Sign Out
            </Button>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-semibold">Welcome, {user?.name}</h2>
            <p className="text-muted-foreground mt-1">
              View your assigned projects and respond to revision requests.
            </p>
          </div>
          <Button variant="outline" size="sm" onClick={refetch}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>

        {/* Stats Summary */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <StatCard
            label="Under Review"
            value={underReviewCount}
            description="Projects being reviewed"
            className="border-blue-200 bg-blue-50/50"
          />
          <StatCard
            label="Revisions Pending"
            value={pendingCount}
            description="Projects needing your response"
            className="border-amber-200 bg-amber-50/50"
          />
          <StatCard
            label="Approved"
            value={approvedCount}
            description="Projects completed"
            className="border-green-200 bg-green-50/50"
          />
        </div>

        {/* Projects List */}
        <div className="space-y-4">
          <h3 className="text-lg font-medium">Your Projects</h3>

          {isLoading ? (
            <div className="space-y-4">
              <Skeleton className="h-32 w-full" />
              <Skeleton className="h-32 w-full" />
              <Skeleton className="h-32 w-full" />
            </div>
          ) : projects.length === 0 ? (
            <div className="text-center py-12 border rounded-lg bg-muted/20">
              <FolderOpen className="h-16 w-16 mx-auto text-muted-foreground/30 mb-4" />
              <p className="text-muted-foreground">No projects assigned yet.</p>
              <p className="text-sm text-muted-foreground mt-1">
                When a reviewer assigns you to a project, it will appear here.
              </p>
            </div>
          ) : (
            <div className="grid gap-4">
              {projects.map((project) => (
                <ProjectCard key={project.session_id} project={project} />
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

function StatCard({
  label,
  value,
  description,
  className,
}: {
  label: string
  value: number
  description: string
  className?: string
}) {
  return (
    <div className={`rounded-lg border p-4 ${className ?? ''}`}>
      <p className="text-sm font-medium text-muted-foreground">{label}</p>
      <p className="text-3xl font-bold mt-1">{value}</p>
      <p className="text-xs text-muted-foreground mt-1">{description}</p>
    </div>
  )
}
