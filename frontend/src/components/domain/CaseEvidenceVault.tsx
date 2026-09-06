import React, { useState, useMemo, useEffect } from 'react';
import { 
  FileText, 
  Search, 
  Filter, 
  Download, 
  Video, 
  Camera, 
  PenTool, 
  Ruler, 
  X, 
  Loader2, 
  Copy,
  Plus,
  Play,
  Music,
  ExternalLink,
  ZoomIn,
  ZoomOut,
  Maximize2,
  RotateCcw,
  CheckCircle2,
  AlertCircle,
  Clock,
  ShieldCheck,
  UploadCloud,
  FileCheck
} from 'lucide-react';
import type { EvidenceListItem } from '../../types/api';
import { evidenceApi } from '../../api/evidence';
import { useAuthenticatedMedia, downloadAuthenticatedEvidence } from '../../hooks/useAuthenticatedMedia';

interface CaseEvidenceVaultProps {
  caseId: string;
  evidenceList: EvidenceListItem[];
  isLoading: boolean;
  error: any;
  refetch: () => void;
}

// Format byte size cleanly
const formatBytes = (bytes?: number | null) => {
  if (bytes === undefined || bytes === null || isNaN(bytes)) return 'Unavailable';
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
};

// Copy helper
const copyToClipboard = (text: string, e: React.MouseEvent) => {
  e.stopPropagation();
  navigator.clipboard.writeText(text);
};

// Media Thumbnail Component (Uses Blob URL safely with Auth)
const EvidenceCardMedia: React.FC<{ item: EvidenceListItem }> = ({ item }) => {
  const { objectUrl, loading, error } = useAuthenticatedMedia(item.artifact_id);
  const mime = item.mime_type?.toLowerCase() || '';
  const filename = item.original_filename?.toLowerCase() || '';

  const isImage = mime.startsWith('image/') || /\.(png|jpg|jpeg|webp|gif|svg)$/.test(filename);
  const isVideo = mime.startsWith('video/') || /\.(mp4|mkv|avi|mov|webm)$/.test(filename);
  const isAudio = mime.startsWith('audio/') || /\.(mp3|wav|ogg|flac)$/.test(filename);
  const isPdf = mime === 'application/pdf' || filename.endsWith('.pdf');

  if (loading) {
    return (
      <div className="w-full h-full bg-[#0a0e17] flex flex-col items-center justify-center text-civix-text-muted text-[10px] font-mono space-y-1">
        <Loader2 className="w-4 h-4 animate-spin text-civix-blue-light" />
        <span>Loading asset...</span>
      </div>
    );
  }

  if (error || !objectUrl) {
    return (
      <div className="w-full h-full bg-[#0a0e17] flex flex-col items-center justify-center text-civix-text-muted p-2 text-center font-mono">
        {isPdf ? (
          <FileText className="w-8 h-8 text-civix-gold mb-1 opacity-80" />
        ) : isVideo ? (
          <Video className="w-8 h-8 text-civix-blue-light mb-1 opacity-80" />
        ) : isAudio ? (
          <Music className="w-8 h-8 text-civix-green mb-1 opacity-80" />
        ) : (
          <FileText className="w-8 h-8 text-slate-500 mb-1 opacity-60" />
        )}
        <span className="text-[10px] text-civix-text-secondary truncate max-w-full">
          {item.evidence_type?.replace(/_/g, ' ') || item.mime_type || 'BINARY ARTIFACT'}
        </span>
      </div>
    );
  }

  if (isImage) {
    return (
      <img
        src={objectUrl}
        alt={item.evidence_title || item.original_filename || 'Evidence Thumbnail'}
        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
        loading="lazy"
      />
    );
  }

  if (isVideo) {
    return (
      <div className="relative w-full h-full bg-[#070b12] flex items-center justify-center group-hover:bg-black/80 transition-colors">
        <video src={objectUrl} className="w-full h-full object-cover opacity-60" />
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-10 h-10 rounded-full bg-civix-blue/80 border border-civix-blue-light flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform">
            <Play className="w-5 h-5 text-white ml-0.5" />
          </div>
        </div>
      </div>
    );
  }

  if (isAudio) {
    return (
      <div className="w-full h-full bg-gradient-to-b from-[#0a1120] to-[#05080d] flex flex-col items-center justify-center p-3 text-civix-blue-light">
        <div className="flex items-center space-x-1 mb-2">
          <span className="w-1 h-4 bg-civix-blue-light animate-pulse" />
          <span className="w-1 h-6 bg-civix-blue-light animate-pulse delay-75" />
          <span className="w-1 h-8 bg-civix-blue-light animate-pulse delay-150" />
          <span className="w-1 h-5 bg-civix-blue-light animate-pulse delay-100" />
          <span className="w-1 h-3 bg-civix-blue-light animate-pulse" />
        </div>
        <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-civix-text-secondary">
          AUDIO RECORDING
        </span>
      </div>
    );
  }

  if (isPdf) {
    return (
      <div className="w-full h-full bg-[#090d16] flex flex-col items-center justify-center p-3">
        <FileText className="w-10 h-10 text-civix-gold mb-1" />
        <span className="text-[10px] font-mono font-bold text-civix-gold uppercase">DOCUMENT PDF</span>
        <span className="text-[9px] font-mono text-civix-text-muted mt-0.5 truncate max-w-[150px]">
          {item.original_filename || 'PDF Document'}
        </span>
      </div>
    );
  }

  return (
    <div className="w-full h-full bg-[#0a0e17] flex flex-col items-center justify-center p-2 text-civix-text-muted font-mono">
      <FileText className="w-8 h-8 text-slate-500 mb-1" />
      <span className="text-[10px] text-civix-text-secondary font-bold uppercase">
        {item.mime_type?.split('/')[1]?.toUpperCase() || 'FILE'}
      </span>
    </div>
  );
};

export const CaseEvidenceVault: React.FC<CaseEvidenceVaultProps> = ({
  caseId,
  evidenceList,
  isLoading,
  error,
  refetch,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [sortBy, setSortBy] = useState<string>('NEWEST');

  const [selectedArtifact, setSelectedArtifact] = useState<EvidenceListItem | null>(null);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);

  // Esc key handler
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setSelectedArtifact(null);
        setIsUploadModalOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Filtered & Sorted items
  const filteredEvidence = useMemo(() => {
    return evidenceList
      .filter((item) => {
        // Status filter
        if (statusFilter !== 'ALL' && item.processing_status !== statusFilter) return false;

        // Type filter
        if (typeFilter !== 'ALL') {
          const mime = (item.mime_type || '').toLowerCase();
          const ext = (item.original_filename || '').toLowerCase();

          if (typeFilter === 'IMAGES' && !(mime.startsWith('image/') || /\.(png|jpg|jpeg|webp|gif|svg)$/.test(ext))) {
            return false;
          }
          if (typeFilter === 'VIDEO' && !(mime.startsWith('video/') || /\.(mp4|mkv|avi|mov|webm)$/.test(ext))) {
            return false;
          }
          if (typeFilter === 'AUDIO' && !(mime.startsWith('audio/') || /\.(mp3|wav|ogg|flac)$/.test(ext))) {
            return false;
          }
          if (typeFilter === 'DOCUMENTS' && !(mime === 'application/pdf' || /\.(pdf|doc|docx|txt|json)$/.test(ext))) {
            return false;
          }
          if (
            typeFilter === 'OTHER' &&
            (mime.startsWith('image/') || mime.startsWith('video/') || mime.startsWith('audio/') || mime === 'application/pdf')
          ) {
            return false;
          }
        }

        // Search query
        if (searchQuery.trim()) {
          const q = searchQuery.toLowerCase();
          const titleMatch = (item.evidence_title || '').toLowerCase().includes(q);
          const fileMatch = (item.original_filename || '').toLowerCase().includes(q);
          const idMatch = (item.artifact_id || '').toLowerCase().includes(q);
          const mimeMatch = (item.mime_type || '').toLowerCase().includes(q);
          const typeMatch = (item.evidence_type || '').toLowerCase().includes(q);
          return titleMatch || fileMatch || idMatch || mimeMatch || typeMatch;
        }

        return true;
      })
      .sort((a, b) => {
        if (sortBy === 'NEWEST') {
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
        }
        if (sortBy === 'OLDEST') {
          return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
        }
        if (sortBy === 'NAME') {
          const nameA = a.evidence_title || a.original_filename || '';
          const nameB = b.evidence_title || b.original_filename || '';
          return nameA.localeCompare(nameB);
        }
        if (sortBy === 'TYPE') {
          return (a.mime_type || '').localeCompare(b.mime_type || '');
        }
        return 0;
      });
  }, [evidenceList, searchQuery, typeFilter, statusFilter, sortBy]);

  const selectCls =
    'py-2 px-3 bg-[#0a0e17] border border-civix-border rounded-xs text-xs text-civix-text-primary font-mono focus:outline-none focus:border-civix-blue-light transition-colors';

  return (
    <div className="space-y-5 text-civix-text-primary font-sans">
      {/* 1. VAULT HEADER */}
      <div className="bg-civix-surface border border-civix-border rounded-xs p-5 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-3">
            <h2 className="text-lg font-extrabold text-white tracking-wide uppercase font-mono">
              CASE EVIDENCE VAULT
            </h2>
          </div>
          <p className="text-xs text-civix-text-muted font-mono mt-1">
            Evidence artifacts linked to this investigation
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <div className="bg-[#0a0e17] border border-civix-border rounded-xs px-3 py-1.5 flex items-center space-x-2 font-mono text-xs">
            <ShieldCheck className="w-4 h-4 text-civix-blue-light" />
            <span className="text-civix-text-secondary font-bold">
              TOTAL <span className="text-white font-extrabold">{evidenceList.length}</span> EVIDENCE ARTIFACTS
            </span>
          </div>
          <button
            onClick={() => setIsUploadModalOpen(true)}
            className="civix-btn-primary flex items-center space-x-1.5 py-2 px-4 text-xs font-mono font-bold tracking-wider uppercase cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            <span>+ ADD EVIDENCE</span>
          </button>
        </div>
      </div>

      {/* 2. TOP TOOLBAR */}
      <div className="bg-civix-surface border border-civix-border rounded-xs p-4 space-y-3">
        <div className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-3">
          {/* Search Box */}
          <div className="relative flex-1 min-w-[260px]">
            <Search className="w-4 h-4 text-civix-text-muted absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search evidence (title, filename, artifact ID, type)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-[#0a0e17] border border-civix-border rounded-xs text-xs text-civix-text-primary placeholder-civix-text-muted focus:outline-none focus:border-civix-blue-light transition-colors font-mono"
            />
          </div>

          {/* Filters & Sort Controls */}
          <div className="flex flex-wrap items-center gap-2">
            {/* Type Filter */}
            <div className="flex items-center space-x-1.5">
              <Filter className="w-3.5 h-3.5 text-civix-text-muted" />
              <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)} className={selectCls}>
                <option value="ALL">All Types</option>
                <option value="IMAGES">Images</option>
                <option value="VIDEO">Video</option>
                <option value="AUDIO">Audio</option>
                <option value="DOCUMENTS">Documents</option>
                <option value="OTHER">Other</option>
              </select>
            </div>

            {/* Status Filter */}
            <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className={selectCls}>
              <option value="ALL">All Status</option>
              <option value="COMPLETED">Completed / Stored</option>
              <option value="PROCESSING">Processing</option>
              <option value="FAILED">Failed</option>
            </select>

            {/* Sort Order */}
            <select value={sortBy} onChange={(e) => setSortBy(e.target.value)} className={selectCls}>
              <option value="NEWEST">Newest First</option>
              <option value="OLDEST">Oldest First</option>
              <option value="NAME">Name (A-Z)</option>
              <option value="TYPE">Type</option>
            </select>
          </div>
        </div>
      </div>

      {/* 3. EVIDENCE GRID & STATES */}
      {isLoading ? (
        <div className="grid grid-cols-[repeat(auto-fill,minmax(220px,1fr))] gap-4 py-4">
          {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
            <div key={i} className="bg-civix-surface border border-civix-border rounded-xs h-56 animate-pulse flex flex-col">
              <div className="h-32 bg-[#0a0e17]" />
              <div className="p-3 space-y-2 flex-1">
                <div className="h-3 bg-civix-surface-3 rounded w-3/4" />
                <div className="h-2 bg-civix-surface-3 rounded w-1/2" />
              </div>
            </div>
          ))}
        </div>
      ) : error ? (
        <div className="py-16 text-center bg-civix-surface border border-civix-red/40 rounded-xs space-y-3 p-6">
          <AlertCircle className="w-8 h-8 text-civix-red mx-auto" />
          <h3 className="text-sm font-bold text-white font-mono uppercase">EVIDENCE UNAVAILABLE</h3>
          <p className="text-xs text-civix-text-muted font-mono">Unable to retrieve evidence artifacts for this case.</p>
          <button onClick={() => refetch()} className="civix-btn-secondary py-1.5 px-4 text-xs font-mono cursor-pointer">
            RETRY
          </button>
        </div>
      ) : filteredEvidence.length === 0 ? (
        <div className="py-20 text-center bg-civix-surface border border-civix-border rounded-xs space-y-4 p-8">
          <FileText className="w-10 h-10 text-civix-text-muted opacity-50 mx-auto" />
          <div>
            <h3 className="text-sm font-bold text-white font-mono uppercase tracking-wide">
              {evidenceList.length === 0 ? 'NO EVIDENCE LINKED' : 'NO MATCHING EVIDENCE'}
            </h3>
            <p className="text-xs text-civix-text-muted font-sans mt-1">
              {evidenceList.length === 0
                ? 'No evidence artifacts have been linked to this investigation.'
                : 'No evidence artifacts match your selected search or filter criteria.'}
            </p>
          </div>
          {evidenceList.length === 0 && (
            <button
              onClick={() => setIsUploadModalOpen(true)}
              className="civix-btn-primary py-2 px-4 text-xs font-mono font-bold uppercase inline-flex items-center space-x-1.5 cursor-pointer"
            >
              <Plus className="w-4 h-4" />
              <span>+ ADD EVIDENCE</span>
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-[repeat(auto-fill,minmax(220px,1fr))] gap-4">
          {filteredEvidence.map((item) => {
            const isCompleted =
              item.processing_status === 'COMPLETED' ||
              item.processing_status === 'STORED' ||
              item.processing_status === 'GENERATED';
            const isProcessing = item.processing_status === 'PROCESSING';

            return (
              <div
                key={item.artifact_id}
                onClick={() => setSelectedArtifact(item)}
                className={`group bg-civix-surface border rounded-xs overflow-hidden transition-all duration-200 cursor-pointer flex flex-col ${
                  selectedArtifact?.artifact_id === item.artifact_id
                    ? 'border-civix-blue-light ring-1 ring-civix-blue-light/30'
                    : 'border-civix-border hover:border-civix-blue-light/50'
                }`}
              >
                {/* Real Preview Container */}
                <div className="relative h-36 bg-[#060911] border-b border-civix-border overflow-hidden flex items-center justify-center">
                  <EvidenceCardMedia item={item} />

                  {/* Top Badges Overlay */}
                  <div className="absolute top-2 left-2 right-2 flex items-center justify-between pointer-events-none">
                    <span className="text-[9px] font-mono font-bold px-1.5 py-0.5 rounded-xs bg-black/80 text-civix-blue-light border border-civix-border backdrop-blur-xs uppercase">
                      {item.mime_type?.split('/')[1]?.toUpperCase() || 'BINARY'}
                    </span>
                    <span
                      className={`text-[9px] font-mono font-bold px-1.5 py-0.5 rounded-xs border backdrop-blur-xs ${
                        isCompleted
                          ? 'bg-civix-green/20 text-civix-green border-civix-green/40'
                          : isProcessing
                          ? 'bg-civix-gold/20 text-civix-gold border-civix-gold/40'
                          : 'bg-civix-red/20 text-civix-red border-civix-red/40'
                      }`}
                    >
                      {isCompleted ? '✓ COMPLETED' : isProcessing ? '● PROCESSING' : '✖ FAILED'}
                    </span>
                  </div>

                  {/* Hover Inspect Indicator */}
                  <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center pointer-events-none">
                    <span className="text-[10px] font-mono font-bold bg-civix-surface border border-civix-blue-light text-white px-2.5 py-1 rounded-xs flex items-center space-x-1 shadow-md">
                      <span>INSPECT ARTIFACT ▶</span>
                    </span>
                  </div>
                </div>

                {/* Card Content & Metadata */}
                <div className="p-3 space-y-2 flex-1 flex flex-col justify-between">
                  <div>
                    <h3
                      className="text-xs font-bold text-white group-hover:text-civix-blue-light transition-colors line-clamp-1 font-sans"
                      title={item.evidence_title || item.original_filename || 'Evidence Artifact'}
                    >
                      {item.evidence_title || item.original_filename || 'Evidence Artifact'}
                    </h3>
                    <div className="flex items-center justify-between text-[10px] font-mono text-civix-text-muted mt-1">
                      <span>
                        {new Date(item.created_at).toLocaleDateString('en-GB', {
                          day: 'numeric',
                          month: 'short',
                          year: 'numeric',
                        })}
                      </span>
                      <span>{formatBytes(item.file_size_bytes)}</span>
                    </div>
                  </div>

                  {/* Shortened ID & Copy */}
                  <div className="pt-2 border-t border-civix-border-subtle flex items-center justify-between text-[9px] font-mono text-civix-text-muted">
                    <span className="truncate max-w-[130px]">
                      ID: <code className="text-civix-text-secondary">{item.artifact_id.slice(0, 8)}...</code>
                    </span>
                    <button
                      onClick={(e) => copyToClipboard(item.artifact_id, e)}
                      title="Copy Artifact ID"
                      className="hover:text-white transition-colors"
                    >
                      <Copy className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* 4. EVIDENCE VIEWER MODAL / DRAWER */}
      {selectedArtifact && (
        <EvidenceViewerModal artifact={selectedArtifact} onClose={() => setSelectedArtifact(null)} />
      )}

      {/* 5. ADD EVIDENCE UPLOAD MODAL */}
      {isUploadModalOpen && (
        <AddEvidenceModal
          caseId={caseId}
          onClose={() => setIsUploadModalOpen(false)}
          onSuccess={() => {
            setIsUploadModalOpen(false);
            refetch();
          }}
        />
      )}
    </div>
  );
};

// ---------------------------------------------------------------------------
// Evidence Viewer Modal Component
// ---------------------------------------------------------------------------
const EvidenceViewerModal: React.FC<{ artifact: EvidenceListItem; onClose: () => void }> = ({
  artifact,
  onClose,
}) => {
  const { objectUrl, loading, error } = useAuthenticatedMedia(artifact.artifact_id);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [detailedStatus, setDetailedStatus] = useState<any>(null);

  const mime = artifact.mime_type?.toLowerCase() || '';
  const filename = (artifact.original_filename || '').toLowerCase();
  const isImage = mime.startsWith('image/') || /\.(png|jpg|jpeg|webp|gif|svg)$/.test(filename);
  const isVideo = mime.startsWith('video/') || /\.(mp4|mkv|avi|mov|webm)$/.test(filename);
  const isAudio = mime.startsWith('audio/') || /\.(mp3|wav|ogg|flac)$/.test(filename);
  const isPdf = mime === 'application/pdf' || filename.endsWith('.pdf');

  // Fetch detailed status (for acquired_by, acquisition_method if available)
  useEffect(() => {
    evidenceApi
      .getEvidenceStatus(artifact.artifact_id, artifact.artifact_id)
      .then((res) => setDetailedStatus(res))
      .catch(() => {});
  }, [artifact.artifact_id]);

  const handleDownload = () => {
    downloadAuthenticatedEvidence(
      artifact.artifact_id,
      artifact.original_filename || `evidence_${artifact.artifact_id.slice(0, 8)}`
    );
  };

  const handleOpenInNewTab = () => {
    if (objectUrl) {
      window.open(objectUrl, '_blank');
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/85 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-civix-surface border border-civix-border rounded-xs shadow-2xl max-w-5xl w-full max-h-[92vh] overflow-hidden flex flex-col text-civix-text-primary">
        {/* Modal Header */}
        <div className="px-5 py-3.5 bg-[#080c14] border-b border-civix-border flex items-center justify-between">
          <div className="flex items-center space-x-3 min-w-0">
            <div className="p-1.5 bg-civix-surface border border-civix-border rounded-xs">
              {isImage ? (
                <Camera className="w-4 h-4 text-civix-blue-light" />
              ) : isPdf ? (
                <FileText className="w-4 h-4 text-civix-gold" />
              ) : isVideo ? (
                <Video className="w-4 h-4 text-civix-blue-light" />
              ) : isAudio ? (
                <Music className="w-4 h-4 text-civix-green" />
              ) : (
                <FileText className="w-4 h-4 text-civix-text-muted" />
              )}
            </div>
            <div className="min-w-0">
              <h2
                className="text-sm font-bold text-white truncate font-sans"
                title={artifact.evidence_title || artifact.original_filename || 'Evidence Viewer'}
              >
                {artifact.evidence_title || artifact.original_filename || 'Evidence Artifact Viewer'}
              </h2>
              <p className="text-[10px] font-mono text-civix-text-muted">
                Artifact ID: {artifact.artifact_id}
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2 flex-shrink-0">
            {objectUrl && (
              <button
                onClick={handleOpenInNewTab}
                className="civix-btn-secondary py-1.5 px-3 text-xs font-mono flex items-center space-x-1.5 cursor-pointer"
                title="Open raw stream in new browser tab"
              >
                <ExternalLink className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Open in New Tab</span>
              </button>
            )}
            <button
              onClick={handleDownload}
              className="civix-btn-primary py-1.5 px-3 text-xs font-mono font-bold flex items-center space-x-1.5 cursor-pointer"
            >
              <Download className="w-3.5 h-3.5" />
              <span>DOWNLOAD</span>
            </button>
            <button
              onClick={onClose}
              className="text-civix-text-muted hover:text-white p-1.5 rounded-xs hover:bg-civix-surface-2 transition-colors cursor-pointer"
              title="Close Viewer (Esc)"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Modal Body */}
        <div className="p-5 overflow-y-auto space-y-5 flex-1 bg-[#05080d]">
          {/* Main Media Preview Canvas */}
          <div className="bg-[#070b12] rounded-xs border border-civix-border overflow-hidden relative min-h-[300px] max-h-[500px] flex items-center justify-center">
            {loading ? (
              <div className="py-16 text-center text-civix-text-muted font-mono text-xs space-y-2">
                <Loader2 className="w-8 h-8 animate-spin text-civix-blue-light mx-auto" />
                <span>Decrypting & loading authenticated media content...</span>
              </div>
            ) : error || !objectUrl ? (
              <div className="py-16 text-center text-civix-text-muted font-mono text-xs space-y-2 p-4">
                <AlertCircle className="w-8 h-8 text-civix-gold mx-auto" />
                <p className="font-bold text-white uppercase">PREVIEW UNAVAILABLE</p>
                <p className="text-[11px] text-civix-text-muted">
                  Direct browser preview is not supported for format ({artifact.mime_type || 'binary'}). Use Download below to inspect the file.
                </p>
              </div>
            ) : isImage ? (
              <div className="relative w-full h-full flex flex-col items-center justify-center overflow-auto p-4">
                {/* Zoom Controls Bar */}
                <div className="absolute top-3 right-3 z-10 bg-black/80 border border-civix-border rounded-xs p-1 flex items-center space-x-1 text-xs font-mono backdrop-blur-xs">
                  <button
                    onClick={() => setZoomLevel((z) => Math.max(0.5, z - 0.25))}
                    className="p-1 text-civix-text-muted hover:text-white"
                    title="Zoom Out"
                  >
                    <ZoomOut className="w-4 h-4" />
                  </button>
                  <span className="px-2 text-[10px] font-bold text-civix-blue-light">{Math.round(zoomLevel * 100)}%</span>
                  <button
                    onClick={() => setZoomLevel((z) => Math.min(3, z + 0.25))}
                    className="p-1 text-civix-text-muted hover:text-white"
                    title="Zoom In"
                  >
                    <ZoomIn className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => setZoomLevel(1)}
                    className="p-1 text-civix-text-muted hover:text-white border-l border-civix-border pl-1"
                    title="Reset / Fit"
                  >
                    <RotateCcw className="w-3.5 h-3.5" />
                  </button>
                </div>

                <img
                  src={objectUrl}
                  alt={artifact.evidence_title || artifact.original_filename || 'Evidence'}
                  style={{ transform: `scale(${zoomLevel})` }}
                  className="max-h-[440px] w-auto object-contain transition-transform duration-150 rounded-xs"
                />
              </div>
            ) : isVideo ? (
              <video src={objectUrl} controls className="max-h-[460px] w-full" />
            ) : isAudio ? (
              <div className="p-8 w-full max-w-md space-y-4 text-center">
                <Music className="w-12 h-12 text-civix-green mx-auto animate-bounce" />
                <audio src={objectUrl} controls className="w-full" />
              </div>
            ) : isPdf ? (
              <iframe src={objectUrl} title="PDF Viewer" className="w-full h-[460px] border-0" />
            ) : (
              <div className="p-8 text-center space-y-3">
                <FileText className="w-12 h-12 text-civix-text-muted mx-auto" />
                <p className="text-xs font-mono text-civix-text-muted">Binary file loaded successfully ({formatBytes(artifact.file_size_bytes)}).</p>
              </div>
            )}
          </div>

          {/* Technical Metadata & Chain of Custody (DATA FIRST) */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* EVIDENCE DETAILS */}
            <div className="bg-civix-surface border border-civix-border rounded-xs p-4 space-y-2.5 text-xs font-mono">
              <h3 className="text-[10px] font-bold text-civix-gold uppercase tracking-wider border-b border-civix-border pb-1.5">
                EVIDENCE DETAILS
              </h3>
              <div className="space-y-1.5">
                <div className="flex justify-between">
                  <span className="text-civix-text-muted">Title / Filename:</span>
                  <span className="text-white font-bold text-right truncate max-w-[200px]" title={artifact.evidence_title || artifact.original_filename || 'N/A'}>
                    {artifact.evidence_title || artifact.original_filename || 'N/A'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-civix-text-muted">Artifact ID:</span>
                  <span className="text-civix-blue-light font-bold flex items-center space-x-1">
                    <span>{artifact.artifact_id.slice(0, 16)}...</span>
                    <button onClick={(e) => copyToClipboard(artifact.artifact_id, e)} title="Copy Full ID">
                      <Copy className="w-3 h-3 text-civix-text-muted hover:text-white" />
                    </button>
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-civix-text-muted">Instance ID:</span>
                  <span className="text-civix-text-secondary font-mono text-[11px] truncate max-w-[180px]">
                    {artifact.instance_id}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-civix-text-muted">MIME Format:</span>
                  <span className="text-white font-bold uppercase">{artifact.mime_type || 'Unknown'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-civix-text-muted">File Size:</span>
                  <span className="text-white">{formatBytes(artifact.file_size_bytes)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-civix-text-muted">Status:</span>
                  <span className="text-civix-green font-bold uppercase">{artifact.processing_status}</span>
                </div>
              </div>
            </div>

            {/* CHAIN OF CUSTODY (ONLY SUPPORTED DB FIELDS) */}
            <div className="bg-civix-surface border border-civix-border rounded-xs p-4 space-y-2.5 text-xs font-mono">
              <h3 className="text-[10px] font-bold text-civix-blue-light uppercase tracking-wider border-b border-civix-border pb-1.5">
                CHAIN OF CUSTODY & INTEGRITY
              </h3>
              <div className="space-y-1.5">
                <div className="flex justify-between">
                  <span className="text-civix-text-muted">Ingested Timestamp:</span>
                  <span className="text-white">
                    {new Date(artifact.created_at).toLocaleString('en-GB')}
                  </span>
                </div>

                {detailedStatus?.acquisition_method && (
                  <div className="flex justify-between">
                    <span className="text-civix-text-muted">Acquisition Method:</span>
                    <span className="text-civix-gold font-bold uppercase">{detailedStatus.acquisition_method}</span>
                  </div>
                )}

                {detailedStatus?.acquired_by && (
                  <div className="flex justify-between">
                    <span className="text-civix-text-muted">Acquired By User:</span>
                    <span className="text-white font-mono">{detailedStatus.acquired_by}</span>
                  </div>
                )}

                {(artifact.sha256_hash || detailedStatus?.sha256_hash) && (
                  <div className="flex justify-between flex-col gap-1 pt-1 border-t border-civix-border-subtle">
                    <span className="text-civix-text-muted">SHA-256 Digest:</span>
                    <span className="text-civix-green font-mono text-[10px] break-all font-bold">
                      {artifact.sha256_hash || detailedStatus?.sha256_hash}
                    </span>
                  </div>
                )}

                {!detailedStatus?.acquisition_method && !detailedStatus?.acquired_by && !(artifact.sha256_hash || detailedStatus?.sha256_hash) && (
                  <div className="pt-2 text-[10px] text-civix-text-muted">
                    No additional acquisition metadata recorded in case ledger.
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Modal Footer Actions */}
        <div className="px-5 py-3 bg-[#080c14] border-t border-civix-border flex items-center justify-between text-xs font-mono">
          <span className="text-civix-text-muted text-[10px] truncate max-w-[350px]">
            Artifact ID: <code className="text-white">{artifact.artifact_id}</code>
          </span>
          <div className="flex items-center space-x-3">
            <button onClick={onClose} className="civix-btn-secondary py-1.5 px-4 text-xs font-mono cursor-pointer">
              CLOSE
            </button>
            <button
              onClick={handleDownload}
              className="civix-btn-primary py-1.5 px-4 text-xs font-mono font-bold flex items-center space-x-1.5 cursor-pointer"
            >
              <Download className="w-3.5 h-3.5" />
              <span>DOWNLOAD FILE</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// ---------------------------------------------------------------------------
// Add Evidence Upload Modal Component (Matches exact API contract)
// ---------------------------------------------------------------------------
const AddEvidenceModal: React.FC<{ caseId: string; onClose: () => void; onSuccess: () => void }> = ({
  caseId,
  onClose,
  onSuccess,
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [acquisitionMethod, setAcquisitionMethod] = useState('FIELD_COLLECTION');
  const [acquisitionContext, setAcquisitionContext] = useState('');
  const [uploadState, setUploadState] = useState<'IDLE' | 'UPLOADING' | 'COMPLETED' | 'FAILED'>('IDLE');
  const [errorMessage, setErrorMessage] = useState('');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setUploadState('UPLOADING');
    setErrorMessage('');

    try {
      await evidenceApi.uploadEvidence(caseId, file, acquisitionMethod, acquisitionContext);
      setUploadState('COMPLETED');
      setTimeout(() => {
        onSuccess();
      }, 1000);
    } catch (err: any) {
      console.error('Evidence upload failed:', err);
      setUploadState('FAILED');
      setErrorMessage(err?.response?.data?.detail || err?.message || 'Evidence upload failed.');
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/85 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-civix-surface border border-civix-border rounded-xs shadow-2xl max-w-lg w-full overflow-hidden flex flex-col text-civix-text-primary">
        {/* Header */}
        <div className="px-5 py-4 bg-[#080c14] border-b border-civix-border flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <UploadCloud className="w-5 h-5 text-civix-blue-light" />
            <h2 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
              ADD CASE EVIDENCE
            </h2>
          </div>
          <button onClick={onClose} className="text-civix-text-muted hover:text-white p-1 rounded-xs">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleUpload} className="p-5 space-y-4 text-xs font-mono">
          {/* File Dropzone */}
          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-xs p-6 text-center space-y-3 transition-colors ${
              file ? 'border-civix-blue-light bg-civix-blue/10' : 'border-civix-border hover:border-civix-border-strong bg-[#060911]'
            }`}
          >
            {file ? (
              <div className="space-y-2">
                <FileCheck className="w-8 h-8 text-civix-green mx-auto" />
                <div>
                  <p className="font-bold text-white truncate max-w-xs mx-auto">{file.name}</p>
                  <p className="text-[10px] text-civix-text-muted">{file.type || 'Unknown MIME'} · {formatBytes(file.size)}</p>
                </div>
                <button
                  type="button"
                  onClick={() => setFile(null)}
                  className="text-[10px] text-civix-red hover:underline font-bold"
                >
                  Change File
                </button>
              </div>
            ) : (
              <div className="space-y-2">
                <UploadCloud className="w-8 h-8 text-civix-text-muted mx-auto opacity-70" />
                <div>
                  <p className="text-white font-bold">Drop evidence file here</p>
                  <p className="text-[10px] text-civix-text-muted mt-0.5">Images, Videos, Audio, PDFs, Logs up to 50MB</p>
                </div>
                <label className="civix-btn-secondary inline-block py-1.5 px-3 text-xs cursor-pointer">
                  <span>[ SELECT FILE ]</span>
                  <input type="file" onChange={handleFileChange} className="hidden" />
                </label>
              </div>
            )}
          </div>

          {/* Acquisition Method (backend param) */}
          <div className="space-y-1">
            <label className="text-[10px] font-bold text-civix-text-muted uppercase">Acquisition Method</label>
            <input
              type="text"
              value={acquisitionMethod}
              onChange={(e) => setAcquisitionMethod(e.target.value)}
              placeholder="e.g. FIELD_COLLECTION, FORENSIC_EXTRACT, CCTV_DUMP"
              className="w-full py-2 px-3 bg-[#0a0e17] border border-civix-border rounded-xs text-xs text-white placeholder-civix-text-muted focus:outline-none focus:border-civix-blue-light font-mono"
            />
          </div>

          {/* Acquisition Context (backend param) */}
          <div className="space-y-1">
            <label className="text-[10px] font-bold text-civix-text-muted uppercase">Acquisition Notes / Context</label>
            <textarea
              rows={2}
              value={acquisitionContext}
              onChange={(e) => setAcquisitionContext(e.target.value)}
              placeholder="Optional operational details, seizure location, officer notes..."
              className="w-full py-2 px-3 bg-[#0a0e17] border border-civix-border rounded-xs text-xs text-white placeholder-civix-text-muted focus:outline-none focus:border-civix-blue-light font-mono"
            />
          </div>

          {/* Upload Status Alert */}
          {uploadState === 'UPLOADING' && (
            <div className="p-3 bg-civix-blue/20 border border-civix-blue/40 rounded-xs flex items-center space-x-2 text-civix-blue-light">
              <Loader2 className="w-4 h-4 animate-spin flex-shrink-0" />
              <span>Uploading evidence file & initializing chain of custody...</span>
            </div>
          )}

          {uploadState === 'COMPLETED' && (
            <div className="p-3 bg-civix-green/20 border border-civix-green/40 rounded-xs flex items-center space-x-2 text-civix-green">
              <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
              <span>Evidence ingested successfully. SHA-256 recorded.</span>
            </div>
          )}

          {uploadState === 'FAILED' && (
            <div className="p-3 bg-civix-red/20 border border-civix-red/40 rounded-xs text-civix-red space-y-1">
              <p className="font-bold flex items-center space-x-1">
                <AlertCircle className="w-4 h-4 inline mr-1" />
                <span>Upload Failed</span>
              </p>
              <p className="text-[10px] text-civix-text-secondary">{errorMessage}</p>
            </div>
          )}

          {/* Actions */}
          <div className="pt-2 border-t border-civix-border flex items-center justify-end space-x-2">
            <button
              type="button"
              onClick={onClose}
              disabled={uploadState === 'UPLOADING'}
              className="civix-btn-secondary py-1.5 px-4 text-xs font-mono cursor-pointer"
            >
              CANCEL
            </button>
            <button
              type="submit"
              disabled={!file || uploadState === 'UPLOADING'}
              className="civix-btn-primary py-1.5 px-4 text-xs font-mono font-bold flex items-center space-x-1.5 disabled:opacity-50 cursor-pointer"
            >
              {uploadState === 'UPLOADING' ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>UPLOADING...</span>
                </>
              ) : (
                <>
                  <UploadCloud className="w-3.5 h-3.5" />
                  <span>UPLOAD EVIDENCE</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
