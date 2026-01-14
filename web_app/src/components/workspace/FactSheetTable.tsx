import { AlertTriangle, CheckCircle2, XCircle, ExternalLink, FileText, ThumbsUp, ThumbsDown } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import type { ValidationStatus, ValidationIssue, FactSheetRowBase } from '@/hooks/useValidation'

interface Column<T> {
  key: keyof T | string
  header: string
  render?: (value: unknown, row: T) => React.ReactNode
  className?: string
}

interface FactSheetTableProps<T extends FactSheetRowBase> {
  title: string
  description?: string
  status: ValidationStatus
  rows: T[]
  columns: Column<T>[]
  issues: ValidationIssue[]
  onIssueClick?: (requirementId: string) => void
  onShowSource?: (documentId: string, pageNumber: number) => void
  onReviewStatusChange?: (rowIndex: number, status: 'approved' | 'rejected') => void
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

export function FactSheetTable<T extends FactSheetRowBase>({
  title,
  description,
  status,
  rows,
  columns,
  issues,
  onIssueClick,
  onShowSource,
  onReviewStatusChange,
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
                {(onShowSource || onReviewStatusChange) && (
                  <th className="px-3 py-2 text-right font-medium text-muted-foreground w-32">
                    Actions
                  </th>
                )}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, rowIndex) => (
                <tr
                  key={rowIndex}
                  className={cn(
                    'border-b last:border-0 group',
                    rowIndex % 2 === 0 ? 'bg-background' : 'bg-muted/10',
                    row.review_status === 'approved' && 'bg-green-50 dark:bg-green-950/20',
                    row.review_status === 'rejected' && 'bg-red-50 dark:bg-red-950/20'
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
                  {(onShowSource || onReviewStatusChange) && (
                    <td className="px-3 py-2 text-right">
                      <div className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        {onShowSource && row.document_id && row.page_number && (
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-7 px-2 text-xs"
                            onClick={() => onShowSource(row.document_id!, row.page_number!)}
                            title="Show source in document"
                          >
                            <FileText className="h-3 w-3 mr-1" />
                            Source
                          </Button>
                        )}
                        {onReviewStatusChange && (
                          <>
                            <Button
                              variant={row.review_status === 'approved' ? 'default' : 'ghost'}
                              size="sm"
                              className={cn(
                                'h-7 w-7 p-0',
                                row.review_status === 'approved' && 'bg-green-600 hover:bg-green-700'
                              )}
                              onClick={() => onReviewStatusChange(rowIndex, 'approved')}
                              title="Approve"
                            >
                              <ThumbsUp className="h-3 w-3" />
                            </Button>
                            <Button
                              variant={row.review_status === 'rejected' ? 'default' : 'ghost'}
                              size="sm"
                              className={cn(
                                'h-7 w-7 p-0',
                                row.review_status === 'rejected' && 'bg-red-600 hover:bg-red-700'
                              )}
                              onClick={() => onReviewStatusChange(rowIndex, 'rejected')}
                              title="Reject"
                            >
                              <ThumbsDown className="h-3 w-3" />
                            </Button>
                          </>
                        )}
                      </div>
                    </td>
                  )}
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
                className="flex items-start gap-2 text-sm group/issue"
              >
                {issue.severity === 'error' ? (
                  <XCircle className="h-4 w-4 text-red-500 shrink-0 mt-0.5" />
                ) : (
                  <AlertTriangle className="h-4 w-4 text-yellow-500 shrink-0 mt-0.5" />
                )}
                <span
                  className={cn(
                    'flex-1',
                    onIssueClick && issue.requirement_id && 'cursor-pointer hover:underline'
                  )}
                  onClick={() => {
                    if (onIssueClick && issue.requirement_id) {
                      onIssueClick(issue.requirement_id)
                    }
                  }}
                >
                  {issue.message}
                </span>
                <div className="flex items-center gap-1 shrink-0">
                  {issue.source && onShowSource && (
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-6 px-2 text-xs opacity-0 group-hover/issue:opacity-100 transition-opacity"
                      onClick={(e) => {
                        e.stopPropagation()
                        onShowSource(issue.source!.document_id, issue.source!.page_number)
                      }}
                      title={`View in ${issue.source.document_name}, page ${issue.source.page_number}`}
                    >
                      <FileText className="h-3 w-3 mr-1" />
                      Source
                    </Button>
                  )}
                  {issue.requirement_id && onIssueClick && (
                    <ExternalLink
                      className="h-3 w-3 text-muted-foreground cursor-pointer hover:text-foreground"
                      onClick={(e) => {
                        e.stopPropagation()
                        onIssueClick(issue.requirement_id)
                      }}
                    />
                  )}
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
