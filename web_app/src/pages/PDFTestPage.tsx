import { useState, lazy, Suspense } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { FileText, Check, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'

const LazyPDFViewer = lazy(() => import('@/components/PDFViewer').then(m => ({ default: m.PDFViewer })))

// Test PDFs available in the examples directory
const TEST_PDFS = [
  {
    id: 'project-plan',
    name: 'Public Project Plan',
    path: '/pdfs/4997Botany22_Public_Project_Plan.pdf',
    description: 'Botany Farm 2022 Project Plan - 45 pages',
  },
  {
    id: 'baseline-report',
    name: 'Baseline Report 2022',
    path: '/pdfs/4997Botany22_Soil_Organic_Carbon_Project_Public_Baseline_Report_2022.pdf',
    description: 'Soil Organic Carbon Project Baseline Report',
  },
  {
    id: 'monitoring-report',
    name: 'Monitoring Report 2023',
    path: '/pdfs/4998Botany23_Soil_Organic_Carbon_Project_Public_Monitoring_Report_2023.pdf',
    description: 'Soil Organic Carbon Project Monitoring Report',
  },
  {
    id: 'ghg-emissions',
    name: 'GHG Emissions 2023',
    path: '/pdfs/4998Botany23_GHG_Emissions_30_Sep_2023.pdf',
    description: 'GHG Emissions Report September 2023',
  },
]

export function PDFTestPage() {
  const [selectedPDF, setSelectedPDF] = useState(TEST_PDFS[0])

  return (
    <div className="flex h-[calc(100vh-8rem)]">
      {/* Sidebar - Document Selection */}
      <div className="w-80 border-r bg-muted/30 p-4 overflow-y-auto">
        <h2 className="text-lg font-semibold mb-4">Test Documents</h2>
        <p className="text-sm text-muted-foreground mb-4">
          Select a PDF to test highlighting and text selection.
        </p>

        <div className="space-y-2">
          {TEST_PDFS.map((pdf) => (
            <Card
              key={pdf.id}
              className={cn(
                'cursor-pointer transition-colors hover:bg-accent/50',
                selectedPDF.id === pdf.id && 'ring-2 ring-primary bg-accent/30'
              )}
              onClick={() => setSelectedPDF(pdf)}
            >
              <CardHeader className="p-3">
                <div className="flex items-start gap-2">
                  <FileText className="h-5 w-5 text-primary mt-0.5" />
                  <div className="flex-1 min-w-0">
                    <CardTitle className="text-sm font-medium truncate">
                      {pdf.name}
                    </CardTitle>
                    <CardDescription className="text-xs mt-1">
                      {pdf.description}
                    </CardDescription>
                  </div>
                  {selectedPDF.id === pdf.id && (
                    <Check className="h-4 w-4 text-primary" />
                  )}
                </div>
              </CardHeader>
            </Card>
          ))}
        </div>

        {/* Instructions */}
        <Card className="mt-6">
          <CardHeader className="p-3">
            <CardTitle className="text-sm">How to Test</CardTitle>
          </CardHeader>
          <CardContent className="p-3 pt-0">
            <ol className="text-xs text-muted-foreground space-y-2 list-decimal list-inside">
              <li>Select text in the PDF viewer</li>
              <li>Click "Add highlight" in the popup</li>
              <li>Optionally add a comment</li>
              <li>Click "Save" to confirm</li>
              <li>Reload the page to verify persistence</li>
              <li>Hold Alt + drag to select an area</li>
            </ol>
          </CardContent>
        </Card>

        {/* Exit Criteria */}
        <Card className="mt-4">
          <CardHeader className="p-3">
            <CardTitle className="text-sm">Exit Criteria</CardTitle>
          </CardHeader>
          <CardContent className="p-3 pt-0">
            <ul className="text-xs text-muted-foreground space-y-1">
              <li className="flex items-center gap-2">
                <div className="h-2 w-2 rounded-full bg-green-500" />
                PDFs render correctly
              </li>
              <li className="flex items-center gap-2">
                <div className="h-2 w-2 rounded-full bg-green-500" />
                Text is selectable
              </li>
              <li className="flex items-center gap-2">
                <div className="h-2 w-2 rounded-full bg-green-500" />
                Highlights persist across reload
              </li>
              <li className="flex items-center gap-2">
                <div className="h-2 w-2 rounded-full bg-green-500" />
                Scanned PDFs show warning
              </li>
              <li className="flex items-center gap-2">
                <div className="h-2 w-2 rounded-full bg-yellow-500" />
                No memory issues with 50+ page PDF
              </li>
            </ul>
          </CardContent>
        </Card>
      </div>

      {/* Main Content - PDF Viewer */}
      <div className="flex-1 flex flex-col">
        <div className="p-4 border-b bg-card">
          <h1 className="text-xl font-semibold">{selectedPDF.name}</h1>
          <p className="text-sm text-muted-foreground">
            {selectedPDF.description}
          </p>
        </div>

        <div className="flex-1 overflow-hidden">
          <Suspense fallback={
            <div className="h-full flex items-center justify-center">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          }>
            <LazyPDFViewer
              key={selectedPDF.id}
              url={selectedPDF.path}
              documentId={selectedPDF.id}
            />
          </Suspense>
        </div>
      </div>
    </div>
  )
}
