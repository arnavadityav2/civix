import React from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Folder, 
  Network, 
  MapPin, 
  Camera, 
  Navigation, 
  Box, 
  Bell, 
  FileText, 
  Zap, 
  ArrowRight, 
  LayoutGrid, 
  AlertTriangle, 
  Info, 
  Video, 
  Search, 
  Upload, 
  Plus,
  Radio,
  Fingerprint
} from 'lucide-react';

export const CommandCenterPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="space-y-4 select-none font-sans">

      {/* ── 1. GREETING HERO BANNER (Full min-h-[140px] Height) ─────────────────── */}
      <div className="relative rounded-xl border border-[#1E2430] overflow-hidden bg-[#090C12] min-h-[140px] flex items-center justify-between px-6 py-5 shadow-2xl">
        {/* Crisp India Gate photograph background — vibrant & clearly visible */}
        <div 
          className="absolute inset-0 bg-cover bg-center opacity-90"
          style={{ backgroundImage: 'url(/assets/hero_india_gate_clean.jpg)' }}
        />
        {/* Smooth gradient overlay on left for crisp text contrast, clear on right */}
        <div className="absolute inset-0 bg-gradient-to-r from-[#07090E]/90 via-[#07090E]/60 to-transparent" />

        {/* Left Hero Context */}
        <div className="relative z-10">
          <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight leading-tight drop-shadow-[0_2px_4px_rgba(0,0,0,0.9)]">
            Good morning, Investigator.
          </h1>
          <div className="text-sm font-bold text-slate-200 mt-1 font-sans drop-shadow-[0_1px_2px_rgba(0,0,0,0.9)]">
            Justice is a safer Delhi.
          </div>
          <div className="flex items-center space-x-2 mt-3 text-xs font-extrabold text-[#E6B325] bg-black/70 backdrop-blur-md px-3 py-1.5 rounded-lg border border-[#E6B325]/40 w-fit shadow-md">
            <MapPin className="w-4 h-4 text-[#E6B325]" />
            <span className="tracking-wide">Delhi NCR Investigation Workspace</span>
          </div>
        </div>

        {/* Right Hero Date/Time & Motto Overlay */}
        <div className="relative z-10 hidden sm:flex flex-col items-end text-right bg-black/60 backdrop-blur-md px-4 py-2.5 rounded-xl border border-white/10 shadow-lg">
          <div className="flex items-center space-x-2">
            <span className="text-xs font-extrabold text-[#E6B325] tracking-widest uppercase">SAFE DELHI</span>
            <span className="text-xs font-extrabold text-white tracking-widest uppercase">STRONGER INDIA</span>
          </div>
          <div className="text-xs text-slate-200 font-mono mt-1 font-semibold">
            Tuesday, 02 September 2026
          </div>
          <div className="text-2xl font-black text-white font-mono leading-none mt-1">
            13:42 <span className="text-xs font-bold text-[#E6B325]">IST</span>
          </div>
          <div className="text-[11px] text-slate-300 italic mt-1 font-mono">
            "Vigilance Today · Safer Tomorrow"
          </div>
        </div>
      </div>

      {/* ── 2. INVESTIGATIVE CAPABILITIES (4x2 GRID - FULL h-40 HEIGHT RESTORED) ── */}
      <div>
        {/* Section Header */}
        <div className="flex items-center justify-between mb-3 px-1">
          <div>
            <h2 className="text-sm font-black text-white uppercase tracking-wider">
              INVESTIGATIVE CAPABILITIES
            </h2>
            <p className="text-[11px] text-[#E6B325] font-semibold">
              Select a specialized subsystem to launch investigation
            </p>
          </div>
          <button 
            onClick={() => navigate('/cases')}
            className="flex items-center space-x-1.5 text-xs font-bold text-slate-300 hover:text-white bg-[#11141C] border border-[#1E2430] hover:border-slate-600 px-3 py-1.5 rounded-md transition-colors"
          >
            <LayoutGrid className="w-3.5 h-3.5 text-slate-400" />
            <span>View All Capabilities</span>
            <ArrowRight className="w-3.5 h-3.5 ml-1" />
          </button>
        </div>

        {/* 4x2 Capability Grid with Full h-40 Height & Original Aspect Ratio */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">

          {/* Tile 1: Cases */}
          <div 
            onClick={() => navigate('/cases')}
            className="group relative h-40 rounded-xl border border-[#1E2430] hover:border-red-500/80 overflow-hidden p-4 flex flex-col justify-between cursor-pointer transition-all hover:scale-[1.01] shadow-xl bg-[#090C12]"
          >
            {/* Real Background Image — Bright & Vivid */}
            <div 
              className="absolute inset-0 bg-cover bg-center opacity-90 transition-all duration-500 group-hover:scale-105 group-hover:opacity-100"
              style={{ backgroundImage: 'url(/assets/tile_cases_bg.jpg)' }}
            />
            {/* Minimal bottom gradient for text contrast */}
            <div className="absolute inset-0 bg-gradient-to-t from-[#07090E]/95 via-[#07090E]/40 to-transparent pointer-events-none" />

            <div className="relative z-10 flex items-start justify-between">
              <div className="p-2.5 bg-red-600/40 border border-red-500/60 backdrop-blur-md rounded-lg text-white shadow-lg">
                <Folder className="w-5 h-5 fill-red-500/40" />
              </div>
              <span className="bg-red-600 text-white font-mono text-[10px] font-bold px-2 py-0.5 rounded shadow-lg border border-red-400/40">
                12 Active
              </span>
            </div>

            <div className="relative z-10 flex items-end justify-between">
              <div className="bg-black/50 backdrop-blur-sm px-2.5 py-1 rounded-lg border border-white/10">
                <h3 className="text-base font-extrabold text-white group-hover:text-red-400 transition-colors drop-shadow-[0_2px_4px_rgba(0,0,0,1)]">Cases</h3>
                <p className="text-xs text-slate-200 font-medium mt-0.5 drop-shadow-[0_1px_2px_rgba(0,0,0,1)]">Investigate, connect and resolve.</p>
              </div>
              <div className="w-8 h-8 rounded-full bg-black/70 border border-white/30 backdrop-blur-md group-hover:border-red-500 group-hover:bg-red-600 group-hover:text-white flex items-center justify-center text-white transition-all shadow-lg">
                <ArrowRight className="w-4 h-4" />
              </div>
            </div>
          </div>

          {/* Tile 2: CDR & Tower Dump Analysis */}
          <div 
            onClick={() => navigate('/telecom')}
            className="group relative h-40 rounded-xl border border-[#1E2430] hover:border-blue-500/80 overflow-hidden p-4 flex flex-col justify-between cursor-pointer transition-all hover:scale-[1.01] shadow-xl bg-[#090C12]"
          >
            {/* Real Background Image — Bright & Vivid */}
            <div 
              className="absolute inset-0 bg-cover bg-center opacity-90 transition-all duration-500 group-hover:scale-105 group-hover:opacity-100"
              style={{ backgroundImage: 'url(/assets/tile_entities_bg.jpg)' }}
            />
            {/* Minimal bottom gradient for text contrast */}
            <div className="absolute inset-0 bg-gradient-to-t from-[#07090E]/95 via-[#07090E]/40 to-transparent pointer-events-none" />

            <div className="relative z-10 flex items-start justify-between">
              <div className="p-2.5 bg-blue-600/40 border border-blue-500/60 backdrop-blur-md rounded-lg text-white shadow-lg">
                <Radio className="w-5 h-5" />
              </div>
              <span className="bg-blue-600 text-white font-mono text-[10px] font-bold px-2 py-0.5 rounded shadow-lg border border-blue-400/40">
                1.2M Pings
              </span>
            </div>

            <div className="relative z-10 flex items-end justify-between">
              <div className="bg-black/50 backdrop-blur-sm px-2.5 py-1 rounded-lg border border-white/10">
                <h3 className="text-base font-extrabold text-white group-hover:text-blue-400 transition-colors drop-shadow-[0_2px_4px_rgba(0,0,0,1)]">CDR & Tower Dump</h3>
                <p className="text-xs text-slate-200 font-medium mt-0.5 drop-shadow-[0_1px_2px_rgba(0,0,0,1)]">Cell pings, SIM swaps & tower co-location.</p>
              </div>
              <div className="w-8 h-8 rounded-full bg-black/70 border border-white/30 backdrop-blur-md group-hover:border-blue-500 group-hover:bg-blue-600 group-hover:text-white flex items-center justify-center text-white transition-all shadow-lg">
                <ArrowRight className="w-4 h-4" />
              </div>
            </div>
          </div>

          {/* Tile 3: Investigative Graph */}
          <div 
            onClick={() => navigate('/cases')}
            className="group relative h-40 rounded-xl border border-[#1E2430] hover:border-cyan-500/80 overflow-hidden p-4 flex flex-col justify-between cursor-pointer transition-all hover:scale-[1.01] shadow-xl bg-[#090C12]"
          >
            {/* Real Background Image — Bright & Vivid */}
            <div 
              className="absolute inset-0 bg-cover bg-center opacity-90 transition-all duration-500 group-hover:scale-105 group-hover:opacity-100"
              style={{ backgroundImage: 'url(/assets/tile_graph_bg.jpg)' }}
            />
            {/* Minimal bottom gradient for text contrast */}
            <div className="absolute inset-0 bg-gradient-to-t from-[#07090E]/95 via-[#07090E]/40 to-transparent pointer-events-none" />

            <div className="relative z-10 flex items-start justify-between">
              <div className="p-2.5 bg-cyan-600/40 border border-cyan-500/60 backdrop-blur-md rounded-lg text-cyan-300 shadow-lg">
                <Network className="w-5 h-5" />
              </div>
            </div>

            <div className="relative z-10 flex items-end justify-between">
              <div className="bg-black/50 backdrop-blur-sm px-2.5 py-1 rounded-lg border border-white/10">
                <h3 className="text-base font-extrabold text-white group-hover:text-cyan-400 transition-colors drop-shadow-[0_2px_4px_rgba(0,0,0,1)]">Investigative Graph</h3>
                <p className="text-xs text-slate-200 font-medium mt-0.5 drop-shadow-[0_1px_2px_rgba(0,0,0,1)]">Uncover hidden connections across data.</p>
              </div>
              <div className="w-8 h-8 rounded-full bg-black/70 border border-white/30 backdrop-blur-md group-hover:border-cyan-500 group-hover:bg-cyan-600 group-hover:text-white flex items-center justify-center text-white transition-all shadow-lg">
                <ArrowRight className="w-4 h-4" />
              </div>
            </div>
          </div>

          {/* Tile 4: Biometric & Facial Intelligence */}
          <div 
            onClick={() => navigate('/cctv')}
            className="group relative h-40 rounded-xl border border-[#1E2430] hover:border-[#E6B325]/80 overflow-hidden p-4 flex flex-col justify-between cursor-pointer transition-all hover:scale-[1.01] shadow-xl bg-[#090C12]"
          >
            {/* Real Background Image — Bright & Vivid */}
            <div 
              className="absolute inset-0 bg-cover bg-center opacity-90 transition-all duration-500 group-hover:scale-105 group-hover:opacity-100"
              style={{ backgroundImage: 'url(/assets/tile_leads_bg.jpg)' }}
            />
            {/* Minimal bottom gradient for text contrast */}
            <div className="absolute inset-0 bg-gradient-to-t from-[#07090E]/95 via-[#07090E]/40 to-transparent pointer-events-none" />

            <div className="relative z-10 flex items-start justify-between">
              <div className="p-2.5 bg-[#E6B325]/40 border border-[#E6B325]/60 backdrop-blur-md rounded-lg text-[#E6B325] shadow-lg">
                <Fingerprint className="w-5 h-5" />
              </div>
              <span className="bg-[#E6B325] text-black font-mono text-[10px] font-extrabold px-2 py-0.5 rounded shadow-lg border border-yellow-300/50">
                CCTNS Live
              </span>
            </div>

            <div className="relative z-10 flex items-end justify-between">
              <div className="bg-black/50 backdrop-blur-sm px-2.5 py-1 rounded-lg border border-white/10">
                <h3 className="text-base font-extrabold text-white group-hover:text-[#E6B325] transition-colors drop-shadow-[0_2px_4px_rgba(0,0,0,1)]">Biometric & Facial</h3>
                <p className="text-xs text-slate-200 font-medium mt-0.5 drop-shadow-[0_1px_2px_rgba(0,0,0,1)]">FRT facial matching, mugshots & voiceprints.</p>
              </div>
              <div className="w-8 h-8 rounded-full bg-black/70 border border-white/30 backdrop-blur-md group-hover:border-[#E6B325] group-hover:bg-[#E6B325] group-hover:text-black flex items-center justify-center text-white transition-all shadow-lg">
                <ArrowRight className="w-4 h-4" />
              </div>
            </div>
          </div>

          {/* Tile 5: Spatial Analysis */}
          <div 
            onClick={() => navigate('/spatial')}
            className="group relative h-40 rounded-xl border border-[#1E2430] hover:border-blue-500/80 overflow-hidden p-4 flex flex-col justify-between cursor-pointer transition-all hover:scale-[1.01] shadow-xl bg-[#090C12]"
          >
            {/* Real Background Image — Bright & Vivid */}
            <div 
              className="absolute inset-0 bg-cover bg-center opacity-90 transition-all duration-500 group-hover:scale-105 group-hover:opacity-100"
              style={{ backgroundImage: 'url(/assets/tile_spatial_bg.jpg)' }}
            />
            {/* Minimal bottom gradient for text contrast */}
            <div className="absolute inset-0 bg-gradient-to-t from-[#07090E]/95 via-[#07090E]/40 to-transparent pointer-events-none" />

            <div className="relative z-10 flex items-start justify-between">
              <div className="p-2.5 bg-blue-600/40 border border-blue-500/60 backdrop-blur-md rounded-lg text-white shadow-lg">
                <MapPin className="w-5 h-5" />
              </div>
              <span className="bg-black/80 border border-slate-600 text-slate-200 font-mono text-[10px] font-bold px-2 py-0.5 rounded backdrop-blur-md shadow-md">
                Delhi NCR
              </span>
            </div>

            <div className="relative z-10 flex items-end justify-between">
              <div className="bg-black/50 backdrop-blur-sm px-2.5 py-1 rounded-lg border border-white/10">
                <h3 className="text-base font-extrabold text-white group-hover:text-blue-400 transition-colors drop-shadow-[0_2px_4px_rgba(0,0,0,1)]">Spatial Analysis</h3>
                <p className="text-xs text-slate-200 font-medium mt-0.5 drop-shadow-[0_1px_2px_rgba(0,0,0,1)]">Maps, movement and geographic intelligence.</p>
              </div>
              <div className="w-8 h-8 rounded-full bg-black/70 border border-white/30 backdrop-blur-md group-hover:border-blue-500 group-hover:bg-blue-600 group-hover:text-white flex items-center justify-center text-white transition-all shadow-lg">
                <ArrowRight className="w-4 h-4" />
              </div>
            </div>
          </div>

          {/* Tile 6: CCTV Analysis */}
          <div 
            onClick={() => navigate('/cctv')}
            className="group relative h-40 rounded-xl border border-[#1E2430] hover:border-red-500/80 overflow-hidden p-4 flex flex-col justify-between cursor-pointer transition-all hover:scale-[1.01] shadow-xl bg-[#090C12]"
          >
            {/* Real Background Image — Bright & Vivid */}
            <div 
              className="absolute inset-0 bg-cover bg-center opacity-90 transition-all duration-500 group-hover:scale-105 group-hover:opacity-100"
              style={{ backgroundImage: 'url(/assets/tile_cctv_bg.jpg)' }}
            />
            {/* Minimal bottom gradient for text contrast */}
            <div className="absolute inset-0 bg-gradient-to-t from-[#07090E]/95 via-[#07090E]/40 to-transparent pointer-events-none" />

            <div className="relative z-10 flex items-start justify-between">
              <div className="p-2.5 bg-red-600/40 border border-red-500/60 backdrop-blur-md rounded-lg text-white shadow-lg">
                <Camera className="w-5 h-5" />
              </div>
            </div>

            <div className="relative z-10 flex items-end justify-between">
              <div className="bg-black/50 backdrop-blur-sm px-2.5 py-1 rounded-lg border border-white/10">
                <h3 className="text-base font-extrabold text-white group-hover:text-red-400 transition-colors drop-shadow-[0_2px_4px_rgba(0,0,0,1)]">CCTV Analysis</h3>
                <p className="text-xs text-slate-200 font-medium mt-0.5 drop-shadow-[0_1px_2px_rgba(0,0,0,1)]">Video intelligence, identify and correlate.</p>
              </div>
              <div className="w-8 h-8 rounded-full bg-black/70 border border-white/30 backdrop-blur-md group-hover:border-red-500 group-hover:bg-red-600 group-hover:text-white flex items-center justify-center text-white transition-all shadow-lg">
                <ArrowRight className="w-4 h-4" />
              </div>
            </div>
          </div>

          {/* Tile 7: Movement Analysis */}
          <div 
            onClick={() => navigate('/spatial')}
            className="group relative h-40 rounded-xl border border-[#1E2430] hover:border-emerald-500/80 overflow-hidden p-4 flex flex-col justify-between cursor-pointer transition-all hover:scale-[1.01] shadow-xl bg-[#090C12]"
          >
            {/* Real Background Image — Bright & Vivid */}
            <div 
              className="absolute inset-0 bg-cover bg-center opacity-90 transition-all duration-500 group-hover:scale-105 group-hover:opacity-100"
              style={{ backgroundImage: 'url(/assets/tile_movement_bg.jpg)' }}
            />
            {/* Minimal bottom gradient for text contrast */}
            <div className="absolute inset-0 bg-gradient-to-t from-[#07090E]/95 via-[#07090E]/40 to-transparent pointer-events-none" />

            <div className="relative z-10 flex items-start justify-between">
              <div className="p-2.5 bg-emerald-600/40 border border-emerald-500/60 backdrop-blur-md rounded-lg text-emerald-300 shadow-lg">
                <Navigation className="w-5 h-5" />
              </div>
            </div>

            <div className="relative z-10 flex items-end justify-between">
              <div className="bg-black/50 backdrop-blur-sm px-2.5 py-1 rounded-lg border border-white/10">
                <h3 className="text-base font-extrabold text-white group-hover:text-emerald-400 transition-colors drop-shadow-[0_2px_4px_rgba(0,0,0,1)]">Movement Analysis</h3>
                <p className="text-xs text-slate-200 font-medium mt-0.5 drop-shadow-[0_1px_2px_rgba(0,0,0,1)]">Track. Trace. Reconstruct movement patterns.</p>
              </div>
              <div className="w-8 h-8 rounded-full bg-black/70 border border-white/30 backdrop-blur-md group-hover:border-emerald-500 group-hover:bg-emerald-600 group-hover:text-white flex items-center justify-center text-white transition-all shadow-lg">
                <ArrowRight className="w-4 h-4" />
              </div>
            </div>
          </div>

          {/* Tile 8: 3D Forensics */}
          <div 
            onClick={() => navigate('/entities')}
            className="group relative h-40 rounded-xl border border-[#1E2430] hover:border-[#E6B325]/80 overflow-hidden p-4 flex flex-col justify-between cursor-pointer transition-all hover:scale-[1.01] shadow-xl bg-[#090C12]"
          >
            {/* Real Background Image — Bright & Vivid */}
            <div 
              className="absolute inset-0 bg-cover bg-center opacity-90 transition-all duration-500 group-hover:scale-105 group-hover:opacity-100"
              style={{ backgroundImage: 'url(/assets/tile_3d_bg.jpg)' }}
            />
            {/* Minimal bottom gradient for text contrast */}
            <div className="absolute inset-0 bg-gradient-to-t from-[#07090E]/95 via-[#07090E]/40 to-transparent pointer-events-none" />

            <div className="relative z-10 flex items-start justify-between">
              <div className="p-2.5 bg-blue-600/40 border border-blue-500/60 backdrop-blur-md rounded-lg text-white shadow-lg">
                <Box className="w-5 h-5" />
              </div>
              <span className="bg-[#E6B325]/30 text-[#E6B325] border border-[#E6B325]/60 backdrop-blur-md font-mono text-[9px] font-extrabold px-1.5 py-0.5 rounded uppercase shadow-lg">
                BETA
              </span>
            </div>

            <div className="relative z-10 flex items-end justify-between">
              <div className="bg-black/50 backdrop-blur-sm px-2.5 py-1 rounded-lg border border-white/10">
                <h3 className="text-base font-extrabold text-white group-hover:text-blue-400 transition-colors drop-shadow-[0_2px_4px_rgba(0,0,0,1)]">3D Forensics</h3>
                <p className="text-xs text-slate-200 font-medium mt-0.5 drop-shadow-[0_1px_2px_rgba(0,0,0,1)]">Reconstruct. Analyse. Validate.</p>
              </div>
              <div className="w-8 h-8 rounded-full bg-black/70 border border-white/30 backdrop-blur-md group-hover:border-blue-500 group-hover:bg-blue-600 group-hover:text-white flex items-center justify-center text-white transition-all shadow-lg">
                <ArrowRight className="w-4 h-4" />
              </div>
            </div>
          </div>

        </div>
      </div>

      {/* ── 3. BOTTOM OPERATIONAL GRID (3 COLUMNS, 1:1:1 SPLIT) ───────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 pt-1">

        {/* Column 1: Priority Signals */}
        <div className="bg-[#11141C] border border-[#1E2430] rounded-xl p-4 flex flex-col justify-between shadow-md">
          <div>
            {/* Header */}
            <div className="flex items-center justify-between border-b border-[#1E2430] pb-2.5 mb-3">
              <div className="flex items-center space-x-2">
                <Bell className="w-4 h-4 text-red-500" />
                <h3 className="text-xs font-bold text-white uppercase tracking-wider">Priority Signals</h3>
                <span className="bg-red-600 text-white font-mono text-[9px] font-bold px-1.5 py-0.2 rounded-full">3</span>
              </div>
              <button onClick={() => navigate('/cases')} className="text-[10px] text-blue-400 hover:underline font-semibold">View All →</button>
            </div>

            {/* List */}
            <div className="space-y-2.5">
              {/* Item 1 */}
              <div onClick={() => navigate('/cases')} className="p-2.5 rounded-lg bg-[#161922] border border-[#1E2430] hover:border-slate-600 cursor-pointer transition-colors flex items-start justify-between gap-2">
                <div className="flex items-start space-x-2.5">
                  <div className="p-1.5 bg-red-600/20 text-red-400 rounded mt-0.5">
                    <AlertTriangle className="w-3.5 h-3.5" />
                  </div>
                  <div>
                    <div className="text-xs font-bold text-white leading-tight">IMEI reuse across multiple cases</div>
                    <div className="text-[10px] text-slate-400 mt-0.5">Linked to 3 investigations including 2012 cash van robbery.</div>
                  </div>
                </div>
                <div className="text-[9px] font-mono text-slate-400 whitespace-nowrap">14 Aug 2026</div>
              </div>

              {/* Item 2 */}
              <div onClick={() => navigate('/cases')} className="p-2.5 rounded-lg bg-[#161922] border border-[#1E2430] hover:border-slate-600 cursor-pointer transition-colors flex items-start justify-between gap-2">
                <div className="flex items-start space-x-2.5">
                  <div className="p-1.5 bg-amber-500/20 text-amber-400 rounded mt-0.5">
                    <AlertTriangle className="w-3.5 h-3.5" />
                  </div>
                  <div>
                    <div className="text-xs font-bold text-white leading-tight">Financial transaction flagged</div>
                    <div className="text-[10px] text-slate-400 mt-0.5">Unusual fund flow detected.</div>
                  </div>
                </div>
                <div className="text-[9px] font-mono text-slate-400 whitespace-nowrap">13 Aug 2026</div>
              </div>

              {/* Item 3 */}
              <div onClick={() => navigate('/cases')} className="p-2.5 rounded-lg bg-[#161922] border border-[#1E2430] hover:border-slate-600 cursor-pointer transition-colors flex items-start justify-between gap-2">
                <div className="flex items-start space-x-2.5">
                  <div className="p-1.5 bg-blue-500/20 text-blue-400 rounded mt-0.5">
                    <Info className="w-3.5 h-3.5" />
                  </div>
                  <div>
                    <div className="text-xs font-bold text-white leading-tight">New entity match</div>
                    <div className="text-[10px] text-slate-400 mt-0.5">Possible link to Najafgarh robbery case.</div>
                  </div>
                </div>
                <div className="text-[9px] font-mono text-slate-400 whitespace-nowrap">12 Aug 2026</div>
              </div>
            </div>
          </div>
        </div>

        {/* Column 2: Recent Activity */}
        <div className="bg-[#11141C] border border-[#1E2430] rounded-xl p-4 flex flex-col justify-between shadow-md">
          <div>
            {/* Header */}
            <div className="flex items-center justify-between border-b border-[#1E2430] pb-2.5 mb-3">
              <div className="flex items-center space-x-2">
                <FileText className="w-4 h-4 text-blue-400" />
                <h3 className="text-xs font-bold text-white uppercase tracking-wider">Recent Activity</h3>
              </div>
              <button onClick={() => navigate('/evidence')} className="text-[10px] text-blue-400 hover:underline font-semibold">View All →</button>
            </div>

            {/* Timeline Feed */}
            <div className="space-y-2 text-xs">
              <div className="flex items-center justify-between p-2 rounded bg-[#161922]">
                <div className="flex items-center space-x-2">
                  <FileText className="w-3.5 h-3.5 text-blue-400" />
                  <span className="font-semibold text-white">New evidence uploaded</span>
                </div>
                <span className="text-[10px] font-mono text-slate-400">5 min ago</span>
              </div>

              <div className="flex items-center justify-between p-2 rounded bg-[#161922]">
                <div className="flex items-center space-x-2">
                  <Radio className="w-3.5 h-3.5 text-blue-400" />
                  <span className="font-semibold text-white">CDR Tower Dump correlation complete</span>
                </div>
                <span className="text-[10px] font-mono text-slate-400">28 min ago</span>
              </div>

              <div className="flex items-center justify-between p-2 rounded bg-[#161922]">
                <div className="flex items-center space-x-2">
                  <Fingerprint className="w-3.5 h-3.5 text-amber-400" />
                  <span className="font-semibold text-white">FRT Match Identified (Suresh Valmiki)</span>
                </div>
                <span className="text-[10px] font-mono text-slate-400">1 hour ago</span>
              </div>

              <div className="flex items-center justify-between p-2 rounded bg-[#161922]">
                <div className="flex items-center space-x-2">
                  <Video className="w-3.5 h-3.5 text-red-400" />
                  <span className="font-semibold text-white">CCTV footage linked</span>
                </div>
                <span className="text-[10px] font-mono text-slate-400">2 hours ago</span>
              </div>

              <div className="flex items-center justify-between p-2 rounded bg-[#161922]">
                <div className="flex items-center space-x-2">
                  <Folder className="w-3.5 h-3.5 text-blue-400" />
                  <span className="font-semibold text-white">Case status updated</span>
                </div>
                <span className="text-[10px] font-mono text-slate-400">3 hours ago</span>
              </div>
            </div>
          </div>
        </div>

        {/* Column 3: Quick Actions (2x2 Grid) */}
        <div className="bg-[#11141C] border border-[#1E2430] rounded-xl p-4 flex flex-col justify-between shadow-md">
          <div>
            {/* Header */}
            <div className="flex items-center justify-between border-b border-[#1E2430] pb-2.5 mb-3">
              <div className="flex items-center space-x-2">
                <Zap className="w-4 h-4 text-amber-400" />
                <h3 className="text-xs font-bold text-white uppercase tracking-wider">Quick Actions</h3>
              </div>
            </div>

            {/* 2x2 Sub-grid */}
            <div className="grid grid-cols-2 gap-2.5">
              {/* Action 1: New Case (Red background) */}
              <div 
                onClick={() => navigate('/cases')}
                className="bg-[#DC2626] hover:bg-red-700 p-3 rounded-lg cursor-pointer transition-colors flex flex-col justify-between h-24 text-white shadow"
              >
                <Plus className="w-5 h-5" />
                <div>
                  <div className="font-extrabold text-xs">New Case</div>
                  <div className="text-[9px] text-white/80 leading-none mt-0.5">Create a new investigation</div>
                </div>
              </div>

              {/* Action 2: Global Search */}
              <div 
                onClick={() => navigate('/search')}
                className="bg-[#161922] border border-[#1E2430] hover:border-slate-500 p-3 rounded-lg cursor-pointer transition-colors flex flex-col justify-between h-24 text-slate-200"
              >
                <Search className="w-5 h-5 text-blue-400" />
                <div>
                  <div className="font-extrabold text-xs text-white">Global Search</div>
                  <div className="text-[9px] text-slate-400 leading-none mt-0.5">Search across all data</div>
                </div>
              </div>

              {/* Action 3: Upload Evidence */}
              <div 
                onClick={() => navigate('/evidence')}
                className="bg-[#161922] border border-[#1E2430] hover:border-slate-500 p-3 rounded-lg cursor-pointer transition-colors flex flex-col justify-between h-24 text-slate-200"
              >
                <Upload className="w-5 h-5 text-amber-400" />
                <div>
                  <div className="font-extrabold text-xs text-white">Upload Evidence</div>
                  <div className="text-[9px] text-slate-400 leading-none mt-0.5">Add and process evidence</div>
                </div>
              </div>

              {/* Action 4: Generate Report */}
              <div 
                onClick={() => navigate('/cases')}
                className="bg-[#161922] border border-[#1E2430] hover:border-slate-500 p-3 rounded-lg cursor-pointer transition-colors flex flex-col justify-between h-24 text-slate-200"
              >
                <FileText className="w-5 h-5 text-emerald-400" />
                <div>
                  <div className="font-extrabold text-xs text-white">Generate Report</div>
                  <div className="text-[9px] text-slate-400 leading-none mt-0.5">Create investigation report</div>
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>

    </div>
  );
};
