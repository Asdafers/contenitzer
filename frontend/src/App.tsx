import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import WorkflowPage from './pages/WorkflowPage'
import { SessionProvider } from './contexts/SessionContext'

function App() {
  return (
    <SessionProvider>
      <Router>
        <div className="min-h-screen bg-gray-50">
          <Routes>
            <Route path="/" element={<WorkflowPage />} />
          </Routes>
        </div>
      </Router>
    </SessionProvider>
  )
}

export default App