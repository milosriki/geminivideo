import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Assets from './pages/Assets';
import RankedClips from './pages/RankedClips';
import RenderJob from './pages/RenderJob';
import './App.css';

function App() {
  return (
    <Router>
      <div className="app">
        <nav className="navbar">
          <h1>AI Ad Intelligence Suite</h1>
          <ul>
            <li><Link to="/">Assets</Link></li>
            <li><Link to="/render">Render</Link></li>
          </ul>
        </nav>
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Assets />} />
            <Route path="/clips/:assetId" element={<RankedClips />} />
            <Route path="/render" element={<RenderJob />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
