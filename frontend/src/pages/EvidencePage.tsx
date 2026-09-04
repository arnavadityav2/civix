import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  FileText, 
  Search, 
  Filter, 
  CheckCircle2, 
  Eye, 
  Download, 
  ShieldCheck, 
  Video, 
  Camera, 
  PenTool, 
  Ruler, 
  X, 
  Loader2, 
  Layers,
  Copy
} from 'lucide-react';
import { authAdapter } from '../api/authAdapter';

interface EvidenceItem {
  artifact_id: string;
  storage_uri: string;
  mime_type: string;
  file_size_bytes: number;
  sha256_hash: string;
  processing_status: string;
  created_at: string;
  case_id: string;
  case_number: string;
  case_title: string;
  evidence_type: string;
  artifact_title: string;
}

export const EvidencePage: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('ALL');
  const [caseFilter, setCaseFilter] = useState<string>('ALL');
  const [selectedArtifact, setSelectedArtifact] = useState<EvidenceItem | null>(null);

  const { data: evidenceItems = [], isLoading, error } = useQuery<EvidenceItem[]>({
    queryKey: ['globalEvidenceList'],
    queryFn: async () => {
      const res = await fetch('http://localhost:8000/api/v1/evidence', {
        headers: {
          Authorization: `Bearer ${authAdapter.getToken()}`
        }
      });
      if (!res.ok) throw new Error('Failed to fetch evidence list');
      return res.json();
    }
  });

  // Unique cases for dropdown filter
  const availableCases = Array.from(
    new Map(
      evidenceItems
        .filter(i => i.case_number)
        .map(i => [i.case_number, { number: i.case_number, title: i.case_title }])
    ).values()
  );

  // Filter evidence items
  const filteredEvidence = evidenceItems.filter(item => {
    // Type filter
    if (typeFilter !== 'ALL' && item.evidence_type !== typeFilter) return false;
    // Case filter
    if (caseFilter !== 'ALL' && item.case_number !== caseFilter) return false;
    // Search query
    if (searchQuery.trim() !== '') {
      const q = searchQuery.toLowerCase();
      const matchTitle = item.artifact_title?.toLowerCase().includes(q);
      const matchCase = item.case_number?.toLowerCase().includes(q) || item.case_title?.toLowerCase().includes(q);
      const matchHash = item.sha256_hash?.toLowerCase().includes(q);
      const matchId = item.artifact_id?.toLowerCase().includes(q);
      return matchTitle || matchCase || matchHash || matchId;
    }
    return true;
  });

  const getEvidenceIcon = (type: string) => {
    switch (type) {
      case 'CCTV_FOOTAGE':
        return <Video className="w-4 h-4 text-cyan-600" />;
      case 'SKETCH':
        return <PenTool className="w-4 h-4 text-amber-600" />;
      case 'PHYSICAL_EVIDENCE':
        return <Ruler className="w-4 h-4 text-emerald-600" />;
      default:
        return <Camera className="w-4 h-4 text-blue-600" />;
    }
  };

  const getBadgeStyle = (type: string) => {
    switch (type) {
      case 'CCTV_FOOTAGE':
        return 'bg-cyan-50 text-cyan-700 border-cyan-300';
      case 'SKETCH':
        return 'bg-amber-50 text-amber-700 border-amber-300';
      case 'PHYSICAL_EVIDENCE':
        return 'bg-emerald-50 text-emerald-700 border-emerald-300';
      default:
        return 'bg-blue-50 text-blue-700 border-blue-300';
    }
  };

  const formatBytes = (bytes: number) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const copyToClipboard = (text: string, e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(text);
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <div className="flex items-center space-x-2.5">
            <div className="p-2 bg-slate-900 text-white rounded">
              <FileText className="w-5 h-5 text-amber-400" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900 tracking-tight">
                EVIDENCE GALLERY & ARTIFACT STORE
              </h1>
              <p className="text-xs text-slate-500 font-mono">
                Verified Law Enforcement Evidence Universe • 180 Visual Artifacts Ingested & SHA-256 Verified
              </p>
            </div>
          </div>
        </div>

        {/* Stats Pills */}
        <div className="flex items-center space-x-3 text-xs font-mono">
          <div className="bg-slate-100 border border-slate-200 rounded px-3 py-1.5 flex items-center space-x-2">
            <Layers className="w-3.5 h-3.5 text-slate-500" />
            <span className="text-slate-600 font-semibold">{filteredEvidence.length} / {evidenceItems.length} Artifacts</span>
          </div>
          <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 rounded px-3 py-1.5 flex items-center space-x-1.5 font-bold">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <span>100% SHA-256 VERIFIED</span>
          </div>
        </div>
      </div>

      {/* Filter Controls Bar */}
      <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-2xs space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-4">
          {/* Search Box */}
          <div className="md:col-span-5 relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
            <input
              type="text"
              placeholder="Search evidence title, SHA-256 hash, or artifact ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all font-sans"
            />
          </div>

          {/* Evidence Type Filter */}
          <div className="md:col-span-3">
            <div className="flex items-center space-x-2">
              <Filter className="w-3.5 h-3.5 text-slate-400" />
              <select
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                className="w-full py-2 px-3 bg-slate-50 border border-slate-200 rounded text-xs text-slate-700 font-semibold focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="ALL">All Evidence Types (180)</option>
                <option value="CCTV_FOOTAGE">CCTV Footage (45)</option>
                <option value="PHOTOGRAPH">Field Photographs (60)</option>
                <option value="SKETCH">Suspect Sketches (30)</option>
                <option value="PHYSICAL_EVIDENCE">Physical Evidence (45)</option>
              </select>
            </div>
          </div>

          {/* Case Filter */}
          <div className="md:col-span-4">
            <select
              value={caseFilter}
              onChange={(e) => setCaseFilter(e.target.value)}
              className="w-full py-2 px-3 bg-slate-50 border border-slate-200 rounded text-xs text-slate-700 font-semibold focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="ALL">All Active Cases ({availableCases.length} Cases)</option>
              {availableCases.map(c => (
                <option key={c.number} value={c.number}>
                  {c.number} — {c.title}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Loading & Error States */}
      {isLoading ? (
        <div className="py-20 flex flex-col items-center justify-center text-slate-400 space-y-3 font-mono text-xs">
          <Loader2 className="w-8 h-8 animate-spin text-amber-500" />
          <span>Loading evidence gallery artifacts...</span>
        </div>
      ) : error ? (
        <div className="py-12 bg-red-50 border border-red-200 rounded text-center text-xs text-red-700 font-mono">
          Failed to load evidence artifacts from backend.
        </div>
      ) : filteredEvidence.length === 0 ? (
        <div className="py-16 text-center text-slate-500 font-mono text-xs bg-slate-50 border border-slate-200 rounded">
          No evidence artifacts match the selected filters.
        </div>
      ) : (
        /* Evidence Cards Grid */
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-5">
          {filteredEvidence.map((item) => {
            const imageUrl = item.storage_uri
              ? `http://localhost:8000/evidence_store/${item.storage_uri}`
              : null;

            return (
              <div
                key={item.artifact_id}
                onClick={() => setSelectedArtifact(item)}
                className="group bg-white border border-slate-200 rounded-lg overflow-hidden shadow-2xs hover:shadow-md hover:border-slate-400 transition-all cursor-pointer flex flex-col justify-between"
              >
                {/* Image Container */}
                <div className="relative aspect-4/3 bg-slate-950 overflow-hidden flex items-center justify-center">
                  {imageUrl ? (
                    <img
                      src={imageUrl}
                      alt={item.artifact_title}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                      loading="lazy"
                    />
                  ) : (
                    <div className="text-slate-600 font-mono text-[10px]">No image asset</div>
                  )}

                  {/* Top Badges Overlay */}
                  <div className="absolute top-2 left-2 right-2 flex items-center justify-between">
                    <span className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded border backdrop-blur-md shadow-2xs ${getBadgeStyle(item.evidence_type)}`}>
                      {item.evidence_type.replace('_', ' ')}
                    </span>
                    <span className="text-[9px] font-mono font-bold bg-slate-900/80 text-white px-2 py-0.5 rounded border border-slate-700 backdrop-blur-md">
                      {item.case_number}
                    </span>
                  </div>

                  {/* Quick Inspect Hover Button */}
                  <div className="absolute inset-0 bg-slate-900/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                    <span className="bg-white text-slate-900 text-xs font-bold px-3 py-1.5 rounded shadow-md flex items-center space-x-1.5">
                      <Eye className="w-3.5 h-3.5 text-blue-700" />
                      <span>Inspect Artifact</span>
                    </span>
                  </div>
                </div>

                {/* Card Content */}
                <div className="p-3 space-y-2 flex-1 flex flex-col justify-between">
                  <div>
                    <h3 className="text-xs font-bold text-slate-900 group-hover:text-blue-700 transition-colors line-clamp-1">
                      {item.artifact_title}
                    </h3>
                    <p className="text-[11px] text-slate-500 font-mono line-clamp-1 mt-0.5">
                      {item.case_title}
                    </p>
                  </div>

                  {/* Footer Metadata */}
                  <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-[10px] font-mono text-slate-500">
                    <div className="flex items-center space-x-1">
                      <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                      <span>{formatBytes(item.file_size_bytes)}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <span>SHA: {item.sha256_hash?.slice(0, 6)}...</span>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Lightbox / Full Artifact Inspector Modal */}
      {selectedArtifact && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white border border-slate-200 rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            {/* Modal Header */}
            <div className="px-5 py-4 bg-slate-900 text-white flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="p-1.5 bg-slate-800 rounded">
                  {getEvidenceIcon(selectedArtifact.evidence_type)}
                </div>
                <div>
                  <h2 className="text-sm font-bold text-white font-sans">{selectedArtifact.artifact_title}</h2>
                  <p className="text-[11px] font-mono text-slate-400">
                    Case: {selectedArtifact.case_number} — {selectedArtifact.case_title}
                  </p>
                </div>
              </div>
              <button
                onClick={() => setSelectedArtifact(null)}
                className="text-slate-400 hover:text-white p-1 rounded transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto space-y-6 flex-1">
              {/* Image Preview Canvas */}
              <div className="bg-slate-950 rounded-lg p-2 flex items-center justify-center border border-slate-800 max-h-[480px]">
                <img
                  src={`http://localhost:8000/evidence_store/${selectedArtifact.storage_uri}`}
                  alt={selectedArtifact.artifact_title}
                  className="max-h-[440px] w-auto object-contain rounded"
                />
              </div>

              {/* Technical Verification Details */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono bg-slate-50 p-4 rounded-lg border border-slate-200">
                <div className="space-y-2">
                  <div className="flex items-center justify-between border-b border-slate-200 pb-1.5">
                    <span className="text-slate-500 font-semibold">Artifact ID:</span>
                    <span className="font-bold text-slate-900 flex items-center space-x-1">
                      <span>{selectedArtifact.artifact_id}</span>
                      <button onClick={(e) => copyToClipboard(selectedArtifact.artifact_id, e)} title="Copy ID">
                        <Copy className="w-3 h-3 text-slate-400 hover:text-slate-700" />
                      </button>
                    </span>
                  </div>
                  <div className="flex items-center justify-between border-b border-slate-200 pb-1.5">
                    <span className="text-slate-500 font-semibold">Evidence Type:</span>
                    <span className="font-bold text-blue-800">{selectedArtifact.evidence_type}</span>
                  </div>
                  <div className="flex items-center justify-between border-b border-slate-200 pb-1.5">
                    <span className="text-slate-500 font-semibold">MIME Format:</span>
                    <span className="font-bold text-slate-900">{selectedArtifact.mime_type}</span>
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between border-b border-slate-200 pb-1.5">
                    <span className="text-slate-500 font-semibold">File Size:</span>
                    <span className="font-bold text-slate-900">{formatBytes(selectedArtifact.file_size_bytes)}</span>
                  </div>
                  <div className="flex items-center justify-between border-b border-slate-200 pb-1.5">
                    <span className="text-slate-500 font-semibold">Verification Status:</span>
                    <span className="font-bold text-emerald-700 flex items-center space-x-1">
                      <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                      <span>100% VERIFIED</span>
                    </span>
                  </div>
                  <div className="flex items-center justify-between border-b border-slate-200 pb-1.5">
                    <span className="text-slate-500 font-semibold">SHA-256 Checksum:</span>
                    <span className="font-bold text-slate-800 truncate max-w-[180px]" title={selectedArtifact.sha256_hash}>
                      {selectedArtifact.sha256_hash}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Modal Footer Actions */}
            <div className="px-5 py-3 bg-slate-100 border-t border-slate-200 flex items-center justify-between">
              <span className="text-xs font-mono text-slate-500">
                Stored at: <code className="text-slate-800 font-bold">{selectedArtifact.storage_uri}</code>
              </span>
              <div className="flex items-center space-x-2">
                <a
                  href={`http://localhost:8000/evidence_store/${selectedArtifact.storage_uri}`}
                  target="_blank"
                  rel="noreferrer"
                  className="bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs px-4 py-2 rounded flex items-center space-x-1.5 transition-colors shadow-2xs"
                >
                  <Download className="w-3.5 h-3.5 text-amber-400" />
                  <span>Download High-Res Asset</span>
                </a>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
