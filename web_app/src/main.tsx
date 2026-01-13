import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
// Import react-pdf-highlighter styles
import 'react-pdf-highlighter/dist/style.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
