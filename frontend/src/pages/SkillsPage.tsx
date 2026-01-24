
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Cpu, Zap, Brain, Shield, PenTool, Mic, Video, 
  BarChart3, Activity, Globe, Rocket, CheckCircle, 
  AlertTriangle, Power, Sparkles, Layers, RefreshCw
} from 'lucide-react';

// --- Types ---
interface AgentSkill {
  id: string;
  name: string;
  role: string;
  category: 'brain' | 'creative' | 'marketing' | 'infra';
  status: 'active' | 'sleeping' | 'error';
  description: string;
  stats?: { label: string; value: string }[];
}

// --- Mock Data (Based on Catalog) ---
const INITIAL_SKILLS: AgentSkill[] = [
  // THE BRAIN
  { id: 'agent-1', name: 'CEO Agent', role: 'Orchestrator', category: 'brain', status: 'sleeping', description: 'Master logic for business strategy.' },
  { id: 'agent-2', name: 'Director', role: 'Creative Lead', category: 'brain', status: 'active', description: 'Writes viral scripts with Hormozi rules.' },
  { id: 'agent-3', name: 'Critic', role: 'QA', category: 'brain', status: 'active', description: 'Ruthless ad reviewer (DeepCTR style).' },
  { id: 'agent-16', name: 'Oracle', role: 'ROAS Predictor', category: 'brain', status: 'active', description: 'Predicts ad performance before spend.', stats: [{ label: 'Accuracy', value: '94%' }] },
  
  // CREATIVE
  { id: 'agent-6', name: 'Video Editor', role: 'Renderer', category: 'creative', status: 'active', description: 'FFmpeg processing & composition.' },
  { id: 'agent-7', name: 'Voice Actor', role: 'TTS', category: 'creative', status: 'active', description: 'Hyper-realistic voice cloning.' },
  { id: 'agent-8', name: 'Designer', role: 'Visuals', category: 'creative', status: 'active', description: 'Thumbnail & asset generation.' },
  
  // MARKETERS
  { id: 'agent-11', name: 'Campaign Mgr', role: 'Publisher', category: 'marketing', status: 'active', description: 'Multi-platform ad launcher.' },
  { id: 'agent-12', name: 'Fatigue Doc', role: 'Optimizer', category: 'marketing', status: 'active', description: 'Detects and fixes ad fatigue.' },
  { id: 'agent-10', name: 'Trend Watcher', role: 'Analyst', category: 'marketing', status: 'sleeping', description: 'Scans real-time viral trends.' },
];

const CATEGORIES = [
  { id: 'all', label: 'All Skills' },
  { id: 'brain', label: 'The Brain', icon: Brain },
  { id: 'creative', label: 'Creative', icon: PenTool },
  { id: 'marketing', label: 'Growth', icon: BarChart3 },
  { id: 'infra', label: 'Infra', icon: Layers },
];

export default function SkillsPage() {
  const [activeCategory, setActiveCategory] = useState('all');
  const [skills, setSkills] = useState(INITIAL_SKILLS);
  const [selectedAgent, setSelectedAgent] = useState<AgentSkill | null>(null);

  const toggleAgent = (id: string) => {
    setSkills(prev => prev.map(agent => 
      agent.id === id 
        ? { ...agent, status: agent.status === 'active' ? 'sleeping' : 'active' } 
        : agent
    ));
  };

  const filteredSkills = activeCategory === 'all' 
    ? skills 
    : skills.filter(s => s.category === activeCategory);

  return (
    <div className="min-h-screen bg-slate-950 text-white p-8 overflow-hidden relative">
      {/* Background Gradients */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-purple-900/20 rounded-full blur-[120px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-blue-900/20 rounded-full blur-[120px]" />
      </div>

      <div className="max-w-7xl mx-auto relative z-10">
        {/* Header */}
        <header className="mb-12">
          <motion.div 
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center gap-3 mb-2"
          >
            <Sparkles className="w-6 h-6 text-purple-400" />
            <h1 className="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400">
              Antigravity Skills
            </h1>
          </motion.div>
          <motion.p 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1, transition: { delay: 0.1 } }}
            className="text-slate-400 text-lg max-w-2xl"
          >
            Manage your autonomous workforce. {skills.filter(s => s.status === 'active').length} agents active.
          </motion.p>
        </header>

        {/* Category Tabs */}
        <div className="flex gap-4 mb-8 overflow-x-auto pb-2">
          {CATEGORIES.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setActiveCategory(cat.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-full border transition-all ${
                activeCategory === cat.id 
                  ? 'bg-purple-500/20 border-purple-500/50 text-white shadow-[0_0_15px_rgba(168,85,247,0.3)]' 
                  : 'bg-slate-900/50 border-slate-800 text-slate-400 hover:border-slate-700'
              }`}
            >
              {cat.icon && <cat.icon className="w-4 h-4" />}
              {cat.label}
            </button>
          ))}
        </div>

        {/* Constellation Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          <AnimatePresence mode="popLayout">
            {filteredSkills.map((agent) => (
              <motion.div
                key={agent.id}
                layout
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                transition={{ duration: 0.2 }}
                onClick={() => setSelectedAgent(agent)}
                className={`
                  group relative p-6 rounded-2xl border backdrop-blur-xl cursor-pointer transition-all duration-300
                  ${agent.status === 'active' 
                    ? 'bg-slate-900/60 border-purple-500/30 shadow-[0_0_30px_-5px_rgba(168,85,247,0.15)] hover:border-purple-500/50' 
                    : 'bg-slate-900/40 border-slate-800 hover:border-slate-700 grayscale'}
                `}
              >
                {/* Status Dot */}
                <div className="absolute top-4 right-4 flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${
                    agent.status === 'active' ? 'bg-green-400 shadow-[0_0_8px_#4ade80]' : 'bg-slate-600'
                  }`} />
                  <span className="text-xs text-slate-500 font-mono uppercase">{agent.status}</span>
                </div>

                {/* Icon */}
                <div className={`
                  w-12 h-12 rounded-xl flex items-center justify-center mb-4 transition-colors
                  ${agent.status === 'active' ? 'bg-purple-500/20 text-purple-400' : 'bg-slate-800 text-slate-600'}
                `}>
                  {getIconForRole(agent.role)}
                </div>

                <h3 className="text-xl font-bold mb-1">{agent.name}</h3>
                <p className="text-slate-400 text-sm mb-4 line-clamp-2">{agent.description}</p>

                {/* Quick Stats */}
                {agent.stats && (
                  <div className="flex gap-3 mt-auto pt-4 border-t border-slate-800/50">
                    {agent.stats.map(stat => (
                      <div key={stat.label} className="text-xs">
                        <span className="text-slate-500 block">{stat.label}</span>
                        <span className="font-mono text-purple-300">{stat.value}</span>
                      </div>
                    ))}
                  </div>
                )}
                
                {/* Active Glow Effect */}
                {agent.status === 'active' && (
                  <div className="absolute inset-0 rounded-2xl bg-gradient-to-tr from-purple-500/5 to-blue-500/5 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
                )}
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      </div>

      {/* Detail Modal (Simplified) */}
      <AnimatePresence>
        {selectedAgent && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm"
            onClick={() => setSelectedAgent(null)}
          >
            <motion.div
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              onClick={e => e.stopPropagation()}
              className="bg-slate-900 border border-slate-700 w-full max-w-lg rounded-3xl p-8 shadow-2xl relative overflow-hidden"
            >
              <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-purple-500 to-blue-500" />
              
              <div className="flex justify-between items-start mb-6">
                <div>
                  <h2 className="text-3xl font-bold">{selectedAgent.name}</h2>
                  <p className="text-purple-400">{selectedAgent.role}</p>
                </div>
                <button 
                  onClick={() => toggleAgent(selectedAgent.id)}
                  className={`px-4 py-2 rounded-lg font-medium flex items-center gap-2 transition-all ${
                    selectedAgent.status === 'active'
                    ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30'
                    : 'bg-green-500/20 text-green-400 hover:bg-green-500/30'
                  }`}
                >
                  <Power className="w-4 h-4" />
                  {selectedAgent.status === 'active' ? 'Deactivate' : 'Activate'}
                </button>
              </div>

              <div className="space-y-6">
                <div className="bg-slate-950/50 p-4 rounded-xl border border-slate-800">
                  <h4 className="text-sm text-slate-500 uppercase mb-2">Capabilities</h4>
                  <p className="text-slate-300">{selectedAgent.description}</p>
                </div>

                {selectedAgent.category === 'brain' && (
                  <div className="grid grid-cols-2 gap-4">
                     <div className="bg-slate-800/30 p-3 rounded-lg">
                        <div className="text-xs text-slate-500">IQ / Model</div>
                        <div className="font-mono">GEMINI 2.0</div>
                     </div>
                     <div className="bg-slate-800/30 p-3 rounded-lg">
                        <div className="text-xs text-slate-500">Last Active</div>
                        <div className="font-mono">Just now</div>
                     </div>
                  </div>
                )}
              </div>

              <button 
                className="mt-8 w-full py-3 rounded-xl bg-slate-800 hover:bg-slate-700 transition-colors text-slate-400"
                onClick={() => setSelectedAgent(null)}
              >
                Close Panel
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function getIconForRole(role: string) {
  if (role.includes('Orchestrator')) return <Cpu />;
  if (role.includes('Creative')) return <Zap />;
  if (role.includes('Predictor')) return <Activity />;
  if (role.includes('Renderer')) return <Video />;
  if (role.includes('TTS')) return <Mic />;
  if (role.includes('Visuals')) return <PenTool />;
  if (role.includes('Publisher')) return <Globe />;
  return <Brain />; // Default
}
