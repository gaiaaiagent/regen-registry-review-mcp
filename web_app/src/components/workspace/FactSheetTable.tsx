import { AlertTriangle, CheckCircle2, XCircle, ExternalLink } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import type { ValidationStatus, ValidationIssue } from '@/hooks/useValidation'

interface Column<T> {
  key: keyof T | string
  header: string
  render?: (value: unknown, row: T) => React.ReactNode
  className?: string
}

interface FactSheetTableProps<T> {
  title: string
  description?: string
  status: ValidationStatus
  rows: T[]
  columns: Column<T>[]
  issues: ValidationIssue[]
  onIssueClick?: (requirementId: string) => void
  emptyMessage?: string
}

function StatusIcon({ status }: { status: ValidationStatus }) {
  switch (status) {
    case 'pass':
      return <CheckCircle2 className="h-4 w-4 text-green-500" />
    case 'warning':
      return <AlertTriangle className="h-4 w-4 text-yellow-500" />
    case 'error':
      return <XCircle className="h-4 w-4 text-red-500" />
  }
}

function StatusBadge({ status }: { status: ValidationStatus }) {
  const variants: Record<ValidationStatus, 'success' | 'warning' | 'destructive'> = {
    pass: 'success',
    warning: 'warning',
    error: 'destructive',
  }

  const labels: Record<ValidationStatus, string> = {
    pass: 'Passed',
    warning: 'Warning',
    error: 'Error',
  }

  return <Badge variant={variants[status]}>{labels[status]}</Badge>
}

function formatCellValue(value: unknown): string {
  if (value === null || value === undefined) return '-'
  if (typeof value === 'number') {
    return value.toLocaleString()
  }
  return String(value)
}

export function FactSheetTable<T extends object>({
  title,
  description,
  status,
  rows,
  columns,
  issues,
  onIssueClick,
  emptyMessage = 'No data available',
}: FactSheetTableProps<T>) {
  return (
    <div className="border rounded-lg overflow-hidden bg-card">
      <div className="px-4 py-3 border-b bg-muted/30">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <StatusIcon status={status} />
            <h3 className="font-medium text-sm">{title}</h3>
          </div>
          <StatusBadge status={status} />
        </div>
        {description && (
          <p className="text-xs text-muted-foreground mt-1">{description}</p>
        )}
      </div>

      {rows.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/20">
                {columns.map((col) => (
                  <th
                    key={String(col.key)}
                    className={cn(
                      'px-3 py-2 text-left font-medium text-muted-foreground',
                      col.className
                    )}
                  >
                    {col.header}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, rowIndex) => (
                <tr
                  key={rowIndex}
                  className={cn(
                    'border-b last:border-0',
                    rowIndex % 2 === 0 ? 'bg-background' : 'bg-muted/10'
                  )}
                >
                  {columns.map((col) => {
                    const value = row[col.key as keyof T]
                    return (
                      <td
                        key={String(col.key)}
                        className={cn('px-3 py-2', col.className)}
                      >
                        {col.render
                          ? col.render(value, row)
                          : formatCellValue(value)}
                      </td>
                    )
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="px-4 py-6 text-center text-sm text-muted-foreground">
          {emptyMessage}
        </div>
      )}

      {issues.length > 0 && (
        <div className="border-t bg-muted/10 px-4 py-3">
          <h4 className="text-xs font-medium text-muted-foreground mb-2">
            Issues ({issues.length})
          </h4>
          <ul className="space-y-2">
            {issues.map((issue, index) => (
              <li
                key={index}
                className={cn(
                  'flex items-start gap-2 text-sm',
                  onIssueClick && issue.requirement_id && 'cursor-pointer hover:bg-muted/50 -mx-2 px-2 py-1 rounded'
                )}
                onClick={() => {
                  if (onIssueClick && issue.requirement_id) {
                    onIssueClick(issue.requirement_id)
                  }
                }}
              >
                {issue.severity === 'error' ? (
                  <XCircle className="h-4 w-4 text-red-500 shrink-0 mt-0.5" />
                ) : (
                  <AlertTriangle className="h-4 w-4 text-yellow-500 shrink-0 mt-0.5" />
                )}
                <span className="flex-1">{issue.message}</span>
                {issue.requirement_id && onIssueClick && (
                  <ExternalLink className="h-3 w-3 text-muted-foreground shrink-0 mt-1" />
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
