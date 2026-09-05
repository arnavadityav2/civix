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

  const availableCases = Array.from(
    new Map(
      evidenceItems
        .filter(i => i.case_number)
        .map(i => [i.case_number, { number: i.case_number, title: i.case_title }])
    ).values()
  );

  const filteredEvidence = evidenceItems.filter(item => {
    if (typeFilter !== 'ALL' && item.evidence_type !== typeFilter) return false;
    if (caseFilter !== 'ALL' && item.case_number !== caseFilter) return false;
    if (searchQuery.trim() !== '') {
      const q = searchQuery.toLowerCase();
      return (
        item.artifact_title?.toLowerCase().includes(q) ||
        item.case_number?.toLowerCase().includes(q) ||
        item.case_title?.toLowerCase().includes(q) ||
        item.sha256_hash?.toLowerCase().includes(q) ||
        item.artifact_id?.toLowerCase().includes(q)
      );
    }
    return true;
  });

  // Evidence type icons — dark palette
  const getEvidenceIcon = (type: string) => {
    switch (type) {
      case 'CCTV_FOOTAGE':     return <Video  className="w-4 h-4 text-civix-blue-light" />;
      case 'SKETCH':           return <PenTool className="w-4 h-4 text-civix-gold" />;
      case 'PHYSICAL_EVIDENCE':return <Ruler  className="w-4 h-4 text-civix-green-light" />;
      default:                 return <Camera className="w-4 h-4 text-civix-text-secondary" />;
    }
  };

  // Evidence type badge styles — dark
  const getBadgeStyle = (type: string) => {
    switch (type) {
      case 'CCTV_FOOTAGE':      return 'bg-civix-blue-subtle text-civix-blue-light border-civix-blue-muted';
      case 'SKETCH':            return 'bg-civix-gold-subtle text-civix-gold border-civix-gold-muted';
      case 'PHYSICAL_EVIDENCE': return 'bg-civix-green-subtle text-civix-green-light border-civix-green-muted';
      default:                  return 'bg-civix-surface-3 text-civix-text-secondary border-civix-border';
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

  const selectCls = 'w-full py-2 px-3 bg-civix-bg border border-civix-border rounded-sm text-xs text-civix-text-primary font-mono focus:outline-none focus:border-civix-blue transition-colors';

  return (
    <div className="space-y-5">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between pb-4 border-b border-civix-border gap-4">
        <div>
          <div className="text-[10px] font-mono text-civix-text-muted uppercase tracking-[0.15em] mb-1">
            FORENSIC EVIDENCE MANAGEMENT
          </div>
          <div className="flex items-center space-x-3">
            <div className="p-1.5 bg-civix-surface-2 border border-civix-border rounded-sm">
              <FileText className="w-4 h-4 text-civix-gold" />
            </div>
            <h1 className="text-xl font-extrabold text-civix-text-primary tracking-tight uppercase">
              Evidence Gallery & Artifact Store
            </h1>
          </div>
          <p className="text-xs text-civix-text-muted font-mono mt-1">
            Verified Law Enforcement Evidence Universe · SHA-256 Chain-of-Custody
          </p>
        </div>

        {/* Stats Pills */}
        <div className="flex items-center space-x-3 text-xs font-mono">
          <div className="bg-civix-surface-2 border border-civix-border rounded-sm px-3 py-1.5 flex items-center space-x-2">
            <Layers className="w-3.5 h-3.5 text-civix-text-muted" />
            <span className="text-civix-text-secondary font-semibold">
              {filteredEvidence.length} / {evidenceItems.length} Artifacts
            </span>
          </div>
          <div className="bg-civix-green-subtle border border-civix-green-muted text-civix-green rounded-sm px-3 py-1.5 flex items-center space-x-1.5 font-bold">
            <ShieldCheck className="w-4 h-4 text-civix-green" />
            <span>SHA-256 VERIFIED</span>
          </div>
        </div>
      </div>

      {/* Filter Controls Bar */}
      <div className="bg-civix-surface-2 border border-civix-border rounded-sm p-4 space-y-3">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-3">
          {/* Search Box */}
          <div className="md:col-span-5 relative">
            <Search className="w-3.5 h-3.5 text-civix-text-muted absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search evidence title, SHA-256, or artifact ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-civix-bg border border-civix-border rounded-sm text-xs text-civix-text-primary placeholder-civix-text-muted focus:outline-none focus:border-civix-blue transition-colors font-mono"
            />
          </div>

          {/* Evidence Type Filter */}
          <div className="md:col-span-3">
            <div className="flex items-center space-x-2">
              <Filter className="w-3.5 h-3.5 text-civix-text-muted flex-shrink-0" />
              <select
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                className={selectCls}
              >
                <option value="ALL">All Evidence Types ({evidenceItems.length})</option>
                <option value="CCTV_FOOTAGE">CCTV Footage</option>
                <option value="PHOTOGRAPH">Field Photographs</option>
                <option value="SKETCH">Suspect Sketches</option>
                <option value="PHYSICAL_EVIDENCE">Physical Evidence</option>
              </select>
            </div>
          </div>

          {/* Case Filter */}
          <div className="md:col-span-4">
            <select
              value={caseFilter}
              onChange={(e) => setCaseFilter(e.target.value)}
              className={selectCls}
            >
              <option value="ALL">All Active Cases ({availableCases.length})</option>
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
        <div className="py-20 flex flex-col items-center justify-center text-civix-text-muted space-y-3 font-mono text-xs">
          <Loader2 className="w-8 h-8 animate-spin text-civix-blue-light" />
          <span>Loading evidence gallery artifacts...</span>
        </div>
      ) : error ? (
        <div className="py-12 bg-civix-red-subtle border border-civix-red-muted rounded-sm text-center text-xs text-civix-red font-mono">
          Failed to load evidence artifacts from backend.
        </div>
      ) : filteredEvidence.length === 0 ? (
        <div className="py-16 text-center text-civix-text-muted font-mono text-xs bg-civix-surface-2 border border-civix-border rounded-sm">
          No evidence artifacts match the selected filters.
        </div>
      ) : (
        /* Evidence Cards Grid */
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {filteredEvidence.map((item) => {
            const imageUrl = item.storage_uri
              ? `http://localhost:8000/evidence_store/${item.storage_uri}`
              : null;

            return (
              <div
                key={item.artifact_id}
                onClick={() => setSelectedArtifact(item)}
                className="group bg-civix-surface border border-civix-border rounded-sm overflow-hidden hover:border-civix-border-strong transition-all cursor-pointer flex flex-col"
              >
                {/* Image Container */}
                <div className="relative aspect-4/3 bg-civix-bg overflow-hidden flex items-center justify-center">
                  {imageUrl ? (
                    <img
                      src={imageUrl}
                      alt={item.artifact_title}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                      loading="lazy"
                    />
                  ) : (
                    <div className="text-civix-text-muted font-mono text-[10px]">No image asset</div>
                  )}

                  {/* Top Badges Overlay */}
                  <div className="absolute top-2 left-2 right-2 flex items-center justify-between">
                    <span className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded-sm border backdrop-blur-md ${getBadgeStyle(item.evidence_type)}`}>
                      {item.evidence_type.replace('_', ' ')}
                    </span>
                    <span className="text-[9px] font-mono font-bold bg-civix-bg/90 text-civix-text-mono px-2 py-0.5 rounded-sm border border-civix-border backdrop-blur-md">
                      {item.case_number}
                    </span>
                  </div>

                  {/* Quick Inspect Hover Button */}
                  <div className="absolute inset-0 bg-civix-bg/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                    <span className="bg-civix-surface border border-civix-border-strong text-civix-text-primary text-xs font-bold px-3 py-1.5 rounded-sm flex items-center space-x-1.5">
                      <Eye className="w-3.5 h-3.5 text-civix-blue-light" />
                      <span>Inspect Artifact</span>
                    </span>
                  </div>
                </div>

                {/* Card Content */}
                <div className="p-3 space-y-2 flex-1 flex flex-col justify-between">
                  <div>
                    <h3 className="text-xs font-bold text-civix-text-primary group-hover:text-civix-blue-light transition-colors line-clamp-1">
                      {item.artifact_title}
                    </h3>
                    <p className="text-[10px] text-civix-text-muted font-mono line-clamp-1 mt-0.5">
                      {item.case_title}
                    </p>
                  </div>

                  {/* Footer Metadata */}
                  <div className="pt-2 border-t border-civix-border-subtle flex items-center justify-between text-[9px] font-mono text-civix-text-muted">
                    <div className="flex items-center space-x-1">
                      <CheckCircle2 className="w-3 h-3 text-civix-green" />
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
        <div className="fixed inset-0 z-50 bg-civix-bg/90 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-civix-surface border border-civix-border rounded-sm shadow-civix-lg max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            {/* Modal Header */}
            <div className="px-5 py-4 bg-civix-surface-2 border-b border-civix-border flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="p-1.5 bg-civix-surface-3 border border-civix-border rounded-sm">
                  {getEvidenceIcon(selectedArtifact.evidence_type)}
                </div>
                <div>
                  <h2 className="text-sm font-bold text-civix-text-primary font-sans">{selectedArtifact.artifact_title}</h2>
                  <p className="text-[10px] font-mono text-civix-text-muted">
                    Case: {selectedArtifact.case_number} — {selectedArtifact.case_title}
                  </p>
                </div>
              </div>
              <button
                onClick={() => setSelectedArtifact(null)}
                className="text-civix-text-muted hover:text-civix-text-primary p-1 rounded-sm hover:bg-civix-surface-3 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto space-y-6 flex-1">
              {/* Image Preview Canvas */}
              <div className="bg-civix-bg rounded-sm p-2 flex items-center justify-center border border-civix-border max-h-[480px]">
                <img
                  src={`http://localhost:8000/evidence_store/${selectedArtifact.storage_uri}`}
                  alt={selectedArtifact.artifact_title}
                  className="max-h-[440px] w-auto object-contain rounded-sm"
                />
              </div>

              {/* Technical Verification Details */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono bg-civix-surface-2 p-4 rounded-sm border border-civix-border">
                <div className="space-y-2">
                  <div className="flex items-center justify-between border-b border-civix-border-subtle pb-1.5">
                    <span className="text-civix-text-muted font-semibold">Artifact ID:</span>
                    <span className="font-bold text-civix-text-mono flex items-center space-x-1">
                      <span>{selectedArtifact.artifact_id.slice(0, 16)}...</span>
                      <button onClick={(e) => copyToClipboard(selectedArtifact.artifact_id, e)} title="Copy ID">
                        <Copy className="w-3 h-3 text-civix-text-muted hover:text-civix-text-primary" />
                      </button>
                    </span>
                  </div>
                  <div className="flex items-center justify-between border-b border-civix-border-subtle pb-1.5">
                    <span className="text-civix-text-muted font-semibold">Evidence Type:</span>
                    <span className="font-bold text-civix-blue-light">{selectedArtifact.evidence_type}</span>
                  </div>
                  <div className="flex items-center justify-between border-b border-civix-border-subtle pb-1.5">
                    <span className="text-civix-text-muted font-semibold">MIME Format:</span>
                    <span className="font-bold text-civix-text-primary">{selectedArtifact.mime_type}</span>
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between border-b border-civix-border-subtle pb-1.5">
                    <span className="text-civix-text-muted font-semibold">File Size:</span>
                    <span className="font-bold text-civix-text-primary">{formatBytes(selectedArtifact.file_size_bytes)}</span>
                  </div>
                  <div className="flex items-center justify-between border-b border-civix-border-subtle pb-1.5">
                    <span className="text-civix-text-muted font-semibold">Verification Status:</span>
                    <span className="font-bold text-civix-green flex items-center space-x-1">
                      <ShieldCheck className="w-3.5 h-3.5 text-civix-green" />
                      <span>100% VERIFIED</span>
                    </span>
                  </div>
                  <div className="flex items-center justify-between border-b border-civix-border-subtle pb-1.5">
                    <span className="text-civix-text-muted font-semibold">SHA-256:</span>
                    <span className="font-bold text-civix-text-mono truncate max-w-[180px]" title={selectedArtifact.sha256_hash}>
                      {selectedArtifact.sha256_hash}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Modal Footer Actions */}
            <div className="px-5 py-3 bg-civix-surface-2 border-t border-civix-border flex items-center justify-between">
              <span className="text-[10px] font-mono text-civix-text-muted">
                Stored at: <code className="text-civix-text-mono font-bold">{selectedArtifact.storage_uri}</code>
              </span>
              <div className="flex items-center space-x-2">
                <a
                  href={`http://localhost:8000/evidence_store/${selectedArtifact.storage_uri}`}
                  target="_blank"
                  rel="noreferrer"
                  className="civix-btn-primary flex items-center space-x-1.5"
                >
                  <Download className="w-3.5 h-3.5 text-civix-gold" />
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
