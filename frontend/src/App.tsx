import { useState } from 'react'
import { AssetsPanel } from './components/AssetsPanel'
import { RankedClipsPanel } from './components/RankedClipsPanel'
import { SearchPanel } from './components/SearchPanel'
import { AnalysisPanel } from './components/AnalysisPanel'
import { CompliancePanel } from './components/CompliancePanel'
import { DiversificationDashboard } from './components/DiversificationDashboard'
import { ReliabilityChart } from './components/ReliabilityChart'

function App() {
  const [selectedAssetId, setSelectedAssetId] = useState<string | null>(null)
  const [selectedClips, setSelectedClips] = useState<any[]>([])

  return (
    <div>
      <div className="header">
        <div className="container">
          <h1>🎬 AI Ad Intelligence & Creation Suite</h1>
        </div>
      </div>

      <div className="container">
        <div className="dashboard">
          <AssetsPanel
            onSelectAsset={setSelectedAssetId}
            selectedAssetId={selectedAssetId}
          />
          
          <RankedClipsPanel
            assetId={selectedAssetId}
            onSelectClips={setSelectedClips}
          />
          
          <SearchPanel />
        </div>

        <div className="dashboard">
          <AnalysisPanel clips={selectedClips} />
          
          <CompliancePanel clips={selectedClips} />
          
          <DiversificationDashboard />
        </div>

        <div className="dashboard">
          <ReliabilityChart />
        </div>
      </div>
    </div>
  )
}

export default App
