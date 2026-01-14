import { Outlet, Link, useLocation } from 'react-router-dom'
import { FileText, Home, LogOut, User } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAuth } from '@/contexts/AuthContext'
import { NotificationBell } from '@/components/NotificationBell'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

export function Layout() {
  const location = useLocation()
  const { user, signOut } = useAuth()

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="border-b bg-card">
        <div className="flex h-14 items-center px-4 gap-4">
          <Link to="/" className="flex items-center gap-2 font-semibold text-lg">
            <FileText className="h-6 w-6 text-primary" />
            <span>Registry Review</span>
          </Link>

          <nav className="flex items-center gap-4 ml-8">
            <Link
              to="/"
              className={cn(
                "flex items-center gap-2 text-sm font-medium transition-colors hover:text-primary",
                location.pathname === "/" ? "text-primary" : "text-muted-foreground"
              )}
            >
              <Home className="h-4 w-4" />
              Dashboard
            </Link>
            <Link
              to="/pdf-test"
              className={cn(
                "flex items-center gap-2 text-sm font-medium transition-colors hover:text-primary",
                location.pathname === "/pdf-test" ? "text-primary" : "text-muted-foreground"
              )}
            >
              <FileText className="h-4 w-4" />
              PDF Viewer Test
            </Link>
          </nav>

          {/* User Menu */}
          <div className="ml-auto flex items-center gap-2">
            <NotificationBell />
            {user && (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <button className="flex items-center gap-2 rounded-md px-2 py-1.5 text-sm hover:bg-accent transition-colors">
                    {user.picture ? (
                      <img
                        src={user.picture}
                        alt={user.name}
                        className="h-6 w-6 rounded-full"
                      />
                    ) : (
                      <div className="h-6 w-6 rounded-full bg-primary/10 flex items-center justify-center">
                        <User className="h-3.5 w-3.5 text-primary" />
                      </div>
                    )}
                    <span className="hidden sm:inline text-muted-foreground">
                      {user.email}
                    </span>
                  </button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56">
                  <DropdownMenuLabel>
                    <div className="flex flex-col space-y-1">
                      <p className="text-sm font-medium">{user.name}</p>
                      <p className="text-xs text-muted-foreground">{user.email}</p>
                    </div>
                  </DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={signOut} className="text-destructive cursor-pointer">
                    <LogOut className="mr-2 h-4 w-4" />
                    Sign out
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="border-t py-4 px-4 text-center text-sm text-muted-foreground">
        Registry Review Web Application - Carbon Credit Project Verification
      </footer>
    </div>
  )
}
