import { Component, type ReactNode } from 'react'
import { AlertTriangle, RefreshCw, Home } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

interface Props {
  children: ReactNode
  fallback?: ReactNode
  onReset?: () => void
  componentName?: string
}

interface State {
  hasError: boolean
  error: Error | null
  errorInfo: string | null
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null, errorInfo: null }
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo)
    this.setState({
      errorInfo: errorInfo.componentStack || null,
    })
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null })
    this.props.onReset?.()
  }

  handleGoHome = () => {
    window.location.href = '/'
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      const { componentName } = this.props
      const { error } = this.state

      return (
        <div className="flex items-center justify-center p-4 min-h-[200px]">
          <Card className="w-full max-w-md border-destructive/50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-destructive">
                <AlertTriangle className="h-5 w-5" />
                {componentName ? `Error in ${componentName}` : 'Something went wrong'}
              </CardTitle>
              <CardDescription>
                {error?.message || 'An unexpected error occurred while rendering this component.'}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground">
                You can try refreshing this component or return to the dashboard.
              </p>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={this.handleReset}>
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Try Again
                </Button>
                <Button variant="ghost" size="sm" onClick={this.handleGoHome}>
                  <Home className="h-4 w-4 mr-2" />
                  Dashboard
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )
    }

    return this.props.children
  }
}

interface MinimalErrorBoundaryProps {
  children: ReactNode
  message?: string
}

interface MinimalState {
  hasError: boolean
}

export class MinimalErrorBoundary extends Component<MinimalErrorBoundaryProps, MinimalState> {
  constructor(props: MinimalErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(): Partial<MinimalState> {
    return { hasError: true }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('MinimalErrorBoundary caught an error:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex items-center justify-center p-4 text-muted-foreground">
          <AlertTriangle className="h-4 w-4 mr-2" />
          <span className="text-sm">{this.props.message || 'Failed to load'}</span>
        </div>
      )
    }

    return this.props.children
  }
}
