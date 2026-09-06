import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Folder, 
  Network, 
  MapPin, 
  Camera, 
  Box, 
  ArrowRight, 
  LayoutGrid, 
  Plus,
  Radio,
  Fingerprint
} from 'lucide-react';
import { FieldOperationsMap } from '../components/dashboard/FieldOperationsMap';
import { NewCaseIntakeModal } from '../components/dashboard/NewCaseIntakeModal';

export const CommandCenterPage: React.FC = () => {
  const navigate = useNavigate();
  const [isNewCaseModalOpen, setIsNewCaseModalOpen] = useState(false);

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

        {/* 3x2 Capability Grid with Full h-40 Height & Original Aspect Ratio */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">

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
            onClick={() => navigate('/biometric')}
            className="group relative h-40 rounded-xl border border-[#1E2430] hover:border-[#E6B325]/80 overflow-hidden p-4 flex flex-col justify-between cursor-pointer transition-all hover:scale-[1.01] shadow-xl bg-[#090C12]"
          >
            {/* Real Background Image — Bright & Vivid */}
            <div 
              className="absolute inset-0 bg-cover bg-center opacity-90 transition-all duration-500 group-hover:scale-105 group-hover:opacity-100"
              style={{ backgroundImage: 'url(/assets/biometric_intel_bg.png)' }}
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

        </div>
      </div>

      {/* ── 3. BOTTOM OPERATIONAL GRID (3 COLUMNS, 1:1:1 SPLIT) ───────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 pt-1">

        {/* Field Operations Map (Spans 2 columns on lg screens) */}
        <div className="lg:col-span-2 min-h-[440px] flex flex-col">
          <FieldOperationsMap />
        </div>

        {/* Column 3: Actions & Secondary Modules */}
        <div className="flex flex-col space-y-4">
          
          {/* New Case Button */}
          <div 
            onClick={() => setIsNewCaseModalOpen(true)}
            className="bg-[#DC2626] border border-red-500 hover:bg-red-700 hover:border-red-400 p-6 rounded-xl cursor-pointer transition-all flex items-center justify-between shadow-lg group"
          >
            <div>
              <div className="text-xl font-black text-white uppercase tracking-widest drop-shadow-md">New Case</div>
              <div className="text-xs font-semibold text-white/90 mt-1">Start a new investigation</div>
            </div>
            <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center group-hover:bg-white/30 transition-colors">
              <Plus className="w-6 h-6 text-white" />
            </div>
          </div>

          {/* 3D Forensics Card */}
          <div 
            onClick={() => navigate('/entities')}
            className="group relative h-40 rounded-xl border border-[#1E2430] hover:border-[#E6B325]/80 overflow-hidden p-4 flex flex-col justify-between cursor-pointer transition-all hover:scale-[1.01] shadow-xl bg-[#090C12] flex-1"
          >
            <div 
              className="absolute inset-0 bg-cover bg-center opacity-90 transition-all duration-500 group-hover:scale-105 group-hover:opacity-100"
              style={{ backgroundImage: 'url(/assets/tile_3d_bg.jpg)' }}
            />
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

      <NewCaseIntakeModal 
        isOpen={isNewCaseModalOpen} 
        onClose={() => setIsNewCaseModalOpen(false)} 
      />

    </div>
  );
};
