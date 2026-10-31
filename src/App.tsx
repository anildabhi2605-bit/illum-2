import React, { useState } from 'react';
import { 
  ShieldCheck, 
  FileText, 
  CheckCircle2, 
  Database, 
  History, 
  Layers, 
  FolderLock, 
  Terminal, 
  AlertTriangle,
  FileCode2,
  Sliders,
  Sparkles
} from 'lucide-react';

export function App() {
  const [activeTab, setActiveTab] = useState<'overview' | 'decisions' | 'rules' | 'tests'>('overview');

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Header */}
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur sticky top-0 z-50 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-lg bg-indigo-600 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/20">
            IL
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight text-white flex items-center gap-2">
              ILLUM AI STUDIO
              <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-medium">
                Governance Mode
              </span>
            </h1>
            <p className="text-xs text-slate-400">Master Governance, Decision Control & Architecture Specification</p>
          </div>
        </div>

        <nav className="flex items-center space-x-1 bg-slate-800/60 p-1 rounded-lg border border-slate-700/50">
          <button
            onClick={() => setActiveTab('overview')}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition ${
              activeTab === 'overview' ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Overview & Status
          </button>
          <button
            onClick={() => setActiveTab('decisions')}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition ${
              activeTab === 'decisions' ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Decisions (DEC-018 & 019)
          </button>
          <button
            onClick={() => setActiveTab('rules')}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition ${
              activeTab === 'rules' ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Product Invariants
          </button>
          <button
            onClick={() => setActiveTab('tests')}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition ${
              activeTab === 'tests' ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Acceptance Matrix
          </button>
        </nav>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 space-y-6">
        {/* Banner Alert for Ratified Decisions */}
        <div className="bg-gradient-to-r from-indigo-950/80 via-slate-900 to-slate-900 border border-indigo-500/30 rounded-xl p-5 shadow-sm">
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 text-xs font-semibold uppercase bg-indigo-500/20 text-indigo-300 rounded border border-indigo-500/40">
                  Approved Baseline Amendment
                </span>
                <span className="text-xs text-slate-400 font-mono">Ratified: 2026-10-30</span>
              </div>
              <h2 className="text-base font-semibold text-white">
                DEC-018: Execution History Retention & Metadata Policy Ratified
              </h2>
              <p className="text-sm text-slate-300 leading-relaxed max-w-4xl">
                Retain only latest 100 execution history records per project (FIFO pruning). Store metadata only (timestamps, latency, token usage, model, provider, status, sanitized error); strictly no raw prompts, raw source text, or raw LLM request/response payloads. Delete project-specific history on project deletion. Never delete or modify the shared <code className="bg-slate-800 text-indigo-300 px-1.5 py-0.5 rounded text-xs">.env</code> file.
              </p>
            </div>
            <div className="hidden sm:flex items-center space-x-2">
              <span className="flex items-center text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-1 rounded-full font-medium">
                <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> All Specs Synchronized
              </span>
            </div>
          </div>
        </div>

        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Metric Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-4">
                <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
                  <span>Max Saved Projects</span>
                  <FolderLock className="w-4 h-4 text-amber-400" />
                </div>
                <div className="text-2xl font-bold text-white">4 Active</div>
                <div className="text-xs text-slate-400 mt-1">DEC-019 ratified cap</div>
              </div>

              <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-4">
                <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
                  <span>History Cap / Project</span>
                  <History className="w-4 h-4 text-indigo-400" />
                </div>
                <div className="text-2xl font-bold text-white">100 Records</div>
                <div className="text-xs text-slate-400 mt-1">DEC-018 FIFO pruning</div>
              </div>

              <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-4">
                <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
                  <span>Acceptance Tests</span>
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                </div>
                <div className="text-2xl font-bold text-white">53 Tests</div>
                <div className="text-xs text-slate-400 mt-1">52 Baseline + 1 Proposed</div>
              </div>

              <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-4">
                <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
                  <span>Current Task Gate</span>
                  <Terminal className="w-4 h-4 text-cyan-400" />
                </div>
                <div className="text-2xl font-bold text-white">P00-T04</div>
                <div className="text-xs text-slate-400 mt-1">Ready for boundary freeze</div>
              </div>
            </div>

            {/* Core Invariants Breakdown */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 space-y-3">
                <div className="flex items-center space-x-2 text-indigo-400">
                  <Database className="w-4 h-4" />
                  <h3 className="font-semibold text-sm text-white">DEC-018 Core Invariants</h3>
                </div>
                <ul className="text-xs text-slate-300 space-y-2">
                  <li className="flex items-start gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 mt-1.5 shrink-0" />
                    <span><strong>100-Record Retention Cap:</strong> Only the latest 100 execution history records per project are retained via FIFO pruning upon insertion of record 101.</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 mt-1.5 shrink-0" />
                    <span><strong>Metadata Only:</strong> Persists timestamps, latency, status, attempt, token counts, model, provider, sanitized error; strictly zero raw prompts, source text, or LLM request/response payloads.</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 mt-1.5 shrink-0" />
                    <span><strong>Project Deletion Cascade:</strong> Deleting a project cascades to clean up its linked execution history records.</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 mt-1.5 shrink-0" />
                    <span><strong>Environment Safety:</strong> History cleanup and project deletion must NEVER delete or modify the shared <code className="text-indigo-300 font-mono">.env</code> file.</span>
                  </li>
                </ul>
              </div>

              <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 space-y-3">
                <div className="flex items-center space-x-2 text-amber-400">
                  <FolderLock className="w-4 h-4" />
                  <h3 className="font-semibold text-sm text-white">DEC-019 Core Invariants</h3>
                </div>
                <ul className="text-xs text-slate-300 space-y-2">
                  <li className="flex items-start gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-400 mt-1.5 shrink-0" />
                    <span><strong>4-Project Maximum:</strong> Active saved projects strictly capped at 4.</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-400 mt-1.5 shrink-0" />
                    <span><strong>5th Project Confirmation Dialog:</strong> Exact prompt: <em>"You already have 4 projects. Do you want to delete the oldest project and create this new project?"</em> identifying the oldest project.</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-400 mt-1.5 shrink-0" />
                    <span><strong>Cancellation Safety:</strong> Selecting NO or Cancel aborts creation and leaves all 4 projects untouched.</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-400 mt-1.5 shrink-0" />
                    <span><strong>Atomic Transaction:</strong> Replacement happens only on explicit YES in a transaction; automatic deletion is prohibited.</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'decisions' && (
          <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 space-y-4">
            <h3 className="text-base font-semibold text-white flex items-center gap-2">
              <Layers className="w-4 h-4 text-indigo-400" />
              Authoritative Decision Register Highlights
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 font-semibold">
                    <th className="py-2.5 px-3">ID</th>
                    <th className="py-2.5 px-3">Decision</th>
                    <th className="py-2.5 px-3">Status</th>
                    <th className="py-2.5 px-3">Resolution Summary</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300">
                  <tr className="bg-indigo-950/20">
                    <td className="py-3 px-3 font-mono font-bold text-indigo-400">DEC-018</td>
                    <td className="py-3 px-3 font-medium text-white">Execution history retention</td>
                    <td className="py-3 px-3">
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                        APPROVED BASELINE AMENDMENT
                      </span>
                    </td>
                    <td className="py-3 px-3">
                      Retain latest 100 records/project (FIFO); metadata only; strictly no raw prompts, sources, or request/response payloads; cascade delete history on project delete; never delete or modify .env.
                    </td>
                  </tr>
                  <tr className="bg-amber-950/20">
                    <td className="py-3 px-3 font-mono font-bold text-amber-400">DEC-019</td>
                    <td className="py-3 px-3 font-medium text-white">Active project limit reduction to 4</td>
                    <td className="py-3 px-3">
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                        APPROVED BASELINE AMENDMENT
                      </span>
                    </td>
                    <td className="py-3 px-3">
                      Max 4 active saved projects. 5th project triggers prompt naming oldest project; NO/Cancel keeps all 4 projects; explicit YES executes atomic replacement; zero automatic deletion.
                    </td>
                  </tr>
                  <tr>
                    <td className="py-3 px-3 font-mono font-bold text-slate-400">DEC-001</td>
                    <td className="py-3 px-3 font-medium text-white">Source of truth</td>
                    <td className="py-3 px-3">
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-indigo-500/10 text-indigo-300 border border-indigo-500/30">
                        APPROVED
                      </span>
                    </td>
                    <td className="py-3 px-3">
                      Original 01_MASTER_PLAN_APPROVED_ORIGINAL.md; frozen verbatim; zero silent changes.
                    </td>
                  </tr>
                  <tr>
                    <td className="py-3 px-3 font-mono font-bold text-slate-400">DEC-007</td>
                    <td className="py-3 px-3 font-medium text-white">First real provider adapter</td>
                    <td className="py-3 px-3">
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30">
                        OPEN
                      </span>
                    </td>
                    <td className="py-3 px-3">
                      Select only after checking user access, model capability and structured-output needs. Gemini selected as candidate, not yet marked supported.
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === 'rules' && (
          <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 space-y-4">
            <h3 className="text-base font-semibold text-white flex items-center gap-2">
              <Sliders className="w-4 h-4 text-emerald-400" />
              Key Product Rules & Non-Negotiables
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs text-slate-300">
              <div className="border border-slate-800 p-3.5 rounded-lg bg-slate-950/40 space-y-1.5">
                <div className="font-semibold text-white">1. Strict No-Silent-Switch Rule</div>
                <p className="text-slate-400">Preferred provider/model failures must be surfaced to the user. Switching to an alternative provider requires explicit user permission.</p>
              </div>
              <div className="border border-slate-800 p-3.5 rounded-lg bg-slate-950/40 space-y-1.5">
                <div className="font-semibold text-white">2. Secret Safety & Plaintext .env</div>
                <p className="text-slate-400">Never expose API keys in UI, client bundles, URLs, error logs, or export ZIPs. The .env file is git-ignored and never deleted by app cleanups.</p>
              </div>
              <div className="border border-slate-800 p-3.5 rounded-lg bg-slate-950/40 space-y-1.5">
                <div className="font-semibold text-white">3. Script Protection & Latest-Only</div>
                <p className="text-slate-400">One active script per project. When generating new candidates, existing saved script stays intact until new output passes schema validation.</p>
              </div>
              <div className="border border-slate-800 p-3.5 rounded-lg bg-slate-950/40 space-y-1.5">
                <div className="font-semibold text-white">4. Data-Only Export</div>
                <p className="text-slate-400">Export ZIP contains scripts, video prompts, thumbnail prompts, SEO packages, and JSON metadata. Zero secrets or database files included.</p>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'tests' && (
          <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 space-y-4">
            <h3 className="text-base font-semibold text-white flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-cyan-400" />
              Acceptance Matrix Synchronization (DEC-018 Tests)
            </h3>
            <div className="space-y-3">
              <div className="p-3 bg-slate-950/50 border border-slate-800 rounded-lg text-xs space-y-1">
                <div className="flex items-center justify-between font-mono font-bold text-indigo-400">
                  <span>ACC-030A — 100-Record Retention & FIFO Pruning</span>
                  <span className="text-[10px] text-slate-500">P06-T04</span>
                </div>
                <p className="text-slate-300">
                  <strong>Condition:</strong> Project contains 100 execution records. Executing 101st job prunes oldest execution record via FIFO. Total history count remains exactly 100.
                </p>
              </div>

              <div className="p-3 bg-slate-950/50 border border-slate-800 rounded-lg text-xs space-y-1">
                <div className="flex items-center justify-between font-mono font-bold text-indigo-400">
                  <span>ACC-030B — Metadata Only & Zero Raw Payload</span>
                  <span className="text-[10px] text-slate-500">P06-T04</span>
                </div>
                <p className="text-slate-300">
                  <strong>Condition:</strong> History table schema and records persist metadata only (timestamps, latency, token metrics, model, provider, status, sanitized error). Asserts strictly 0 raw prompts, raw source text, or raw LLM request/response bodies in database.
                </p>
              </div>

              <div className="p-3 bg-slate-950/50 border border-slate-800 rounded-lg text-xs space-y-1">
                <div className="flex items-center justify-between font-mono font-bold text-indigo-400">
                  <span>ACC-032 — Project Deletion Cleanup & Shared .env Preservation</span>
                  <span className="text-[10px] text-slate-500">P03-T04</span>
                </div>
                <p className="text-slate-300">
                  <strong>Condition:</strong> Deleting a project cascades to delete project DB row, project-specific execution history records, and linked files, while preserving the shared <code className="text-indigo-300 font-mono">.env</code> file untouched.
                </p>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 bg-slate-950 px-6 py-4 text-center text-xs text-slate-500">
        ILLUM AI STUDIO — Authoritative Governance Baseline • Python / FastAPI / SQLite Backend Architecture • All Amendments Traceable
      </footer>
    </div>
  );
}
export default App;
