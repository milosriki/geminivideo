import { useState } from 'react'
import './App.css'
import AssetsPanel from './components/AssetsPanel'
import RankedClipsPanel from './components/RankedClipsPanel'
import SemanticSearchPanel from './components/SemanticSearchPanel'
import AnalysisPanel from './components/AnalysisPanel'
import CompliancePanel from './components/CompliancePanel'
import DiversificationDashboard from './components/DiversificationDashboard'
import ReliabilityChart from './components/ReliabilityChart'
import RenderJobPanel from './components/RenderJobPanel'

function App() {
  const [activeTab, setActiveTab] = useState('assets')

  const tabs = [
    { id: 'assets', label: 'Assets & Ingest' },
    { id: 'clips', label: 'Ranked Clips' },
    { id: 'search', label: 'Semantic Search' },
    { id: 'analysis', label: 'Analysis' },
    { id: 'compliance', label: 'Compliance' },
    { id: 'diversification', label: 'Diversification' },
    { id: 'reliability', label: 'Reliability' },
    { id: 'render', label: 'Render Job' }
  ]

  return (
    <div className="app">
      <header className="header">
        <h1>🎬 Gemini Video - AI Ad Intelligence Suite</h1>
        <p>Scene enrichment, predictive scoring, and automated ad creation for fitness/personal training</p>
      </header>

      <nav className="tabs">
        {tabs.map(tab => (
          <button
            key={tab.id}
            className={`tab ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      <main className="container">
        {activeTab === 'assets' && <AssetsPanel />}
        {activeTab === 'clips' && <RankedClipsPanel />}
        {activeTab === 'search' && <SemanticSearchPanel />}
        {activeTab === 'analysis' && <AnalysisPanel />}
        {activeTab === 'compliance' && <CompliancePanel />}
        {activeTab === 'diversification' && <DiversificationDashboard />}
        {activeTab === 'reliability' && <ReliabilityChart />}
        {activeTab === 'render' && <RenderJobPanel />}
      </main>
    </div>
  )
}

export default App
