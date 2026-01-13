/**
 * Highlight types for the PDF viewer.
 * Re-export types from react-pdf-highlighter and add custom fields.
 */

export type {
  IHighlight,
  NewHighlight,
  Content,
  ScaledPosition,
  Position,
  Comment,
} from 'react-pdf-highlighter'

// Extended highlight with our custom fields
export interface ExtendedHighlight {
  id: string
  position: {
    boundingRect: {
      x1: number
      y1: number
      x2: number
      y2: number
      width: number
      height: number
      pageNumber?: number
    }
    rects: Array<{
      x1: number
      y1: number
      x2: number
      y2: number
      width: number
      height: number
      pageNumber?: number
    }>
    pageNumber: number
    usePdfCoordinates?: boolean
  }
  content: {
    text?: string
    image?: string
  }
  comment?: {
    text?: string
    emoji?: string
  }
  // Custom fields for evidence linking
  documentId?: string
  requirementId?: string
  createdAt: string
  updatedAt?: string
}

// For creating new highlights
export interface NewExtendedHighlight {
  position: ExtendedHighlight['position']
  content: ExtendedHighlight['content']
  comment?: ExtendedHighlight['comment']
}

// Test PDF info for the proof-of-concept
export interface TestPDF {
  name: string
  path: string
  description: string
  pageCount?: number
  hasText: boolean
}

export const TEST_PDFS: TestPDF[] = [
  {
    name: "Public Project Plan",
    path: "/pdfs/4997Botany22_Public_Project_Plan.pdf",
    description: "Botany Farm 2022 Project Plan",
    hasText: true,
  },
  {
    name: "Baseline Report 2022",
    path: "/pdfs/4997Botany22_Soil_Organic_Carbon_Project_Public_Baseline_Report_2022.pdf",
    description: "Soil Organic Carbon Project Baseline Report",
    hasText: true,
  },
  {
    name: "Monitoring Report 2023",
    path: "/pdfs/4998Botany23_Soil_Organic_Carbon_Project_Public_Monitoring_Report_2023.pdf",
    description: "Soil Organic Carbon Project Monitoring Report",
    hasText: true,
  },
  {
    name: "GHG Emissions 2023",
    path: "/pdfs/4998Botany23_GHG_Emissions_30_Sep_2023.pdf",
    description: "GHG Emissions Report September 2023",
    hasText: true,
  },
]
