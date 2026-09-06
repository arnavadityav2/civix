import React, { useState } from 'react';
import { 
  X, 
  Upload, 
  FileText, 
  CheckCircle2, 
  AlertTriangle,
  Loader2,
  FileBadge,
  Users,
  MessageSquare,
  Video,
  Radio,
  Car,
  CreditCard,
  Plus
} from 'lucide-react';

interface NewCaseIntakeModalProps {
  isOpen: boolean;
  onClose: () => void;
}

interface StagedFile {
  id: string;
  category: string;
  file: File;
  previewUrl?: string;
}

const CATEGORIES = [
  { id: 'fir', label: 'FIR DOCUMENT', icon: FileBadge },
  { id: 'suspect', label: 'SUSPECT / PERSON DOCUMENTS', icon: Users },
  { id: 'witness', label: 'WITNESS REPORTS', icon: MessageSquare },
  { id: 'cctv', label: 'CCTV / VIDEO MATERIAL', icon: Video },
  { id: 'telecom', label: 'CALL / TELECOM DATA', icon: Radio },
  { id: 'vehicle', label: 'VEHICLE / TRANSPORT RECORDS', icon: Car },
  { id: 'financial', label: 'FINANCIAL RECORDS', icon: CreditCard },
  { id: 'other', label: 'OTHER EVIDENCE', icon: FileText }
];

export const NewCaseIntakeModal: React.FC<NewCaseIntakeModalProps> = ({ isOpen, onClose }) => {
  const [firNumber, setFirNumber] = useState('');
  const [caseTitle, setCaseTitle] = useState('');
  const [caseType, setCaseType] = useState('CRIMINAL');
  const [jurisdiction, setJurisdiction] = useState('');
  const [incidentDate, setIncidentDate] = useState('');
  const [priority, setPriority] = useState('HIGH');
  const [description, setDescription] = useState('');
  
  const [stagedFiles, setStagedFiles] = useState<StagedFile[]>([]);
  
  const [isProcessing, setIsProcessing] = useState(false);
  const [progressState, setProgressState] = useState<string>('');
  const [isReady, setIsReady] = useState(false);

  if (!isOpen) return null;

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>, categoryId: string) => {
    if (e.target.files && e.target.files.length > 0) {
      const newFiles = Array.from(e.target.files).map(file => ({
        id: Math.random().toString(36).substring(7),
        category: categoryId,
        file,
        previewUrl: file.type.startsWith('image/') ? URL.createObjectURL(file) : undefined
      }));
      setStagedFiles(prev => [...prev, ...newFiles]);
    }
  };

  const removeFile = (id: string) => {
    setStagedFiles(prev => prev.filter(f => f.id !== id));
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const handlePrepareCase = () => {
    if (!firNumber || !caseTitle) return;
    
    setIsProcessing(true);
    setProgressState('FILES VALIDATED');
    
    setTimeout(() => {
      setProgressState('CASE MATERIAL ORGANIZED');
      setTimeout(() => {
        setProgressState('DOCUMENTS READY FOR ANALYSIS');
        setTimeout(() => {
          setIsProcessing(false);
          setIsReady(true);
        }, 1000);
      }, 1200);
    }, 1000);
  };

  const handleClose = () => {
    // Reset state on close
    setFirNumber('');
    setCaseTitle('');
    setCaseType('CRIMINAL');
    setJurisdiction('');
    setIncidentDate('');
    setPriority('HIGH');
    setDescription('');
    setStagedFiles([]);
    setIsProcessing(false);
    setProgressState('');
    setIsReady(false);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm font-sans select-none">
      <div className="bg-[#0B0F17] border border-[#1E2430] w-full max-w-6xl max-h-[90vh] rounded-xl shadow-2xl flex flex-col overflow-hidden">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#1E2430] bg-[#11141C]">
          <div>
            <h2 className="text-xl font-black text-white tracking-wide">NEW INVESTIGATION</h2>
            <p className="text-xs text-slate-400 font-medium mt-1">Create a case workspace and provide the initial investigation material.</p>
          </div>
          <div className="flex items-center space-x-4">
            <span className="text-[10px] font-bold text-amber-500 bg-amber-500/10 px-2 py-1 rounded border border-amber-500/20 uppercase tracking-widest flex items-center">
              <AlertTriangle className="w-3 h-3 mr-1.5" />
              DEMO INTAKE — NOT PERSISTED
            </span>
            <button onClick={handleClose} className="text-slate-400 hover:text-white transition-colors">
              <X className="w-6 h-6" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-8 bg-[#090C12]">
          
          {/* Section 1: CASE IDENTIFICATION */}
          <section>
            <h3 className="text-sm font-bold text-slate-300 uppercase tracking-widest border-b border-[#1E2430] pb-2 mb-4">
              CASE IDENTIFICATION
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div>
                  <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">FIR Number *</label>
                  <input 
                    type="text"
                    value={firNumber}
                    onChange={(e) => setFirNumber(e.target.value)}
                    placeholder="e.g. FIR-127/2012"
                    className="w-full bg-[#11141C] border border-[#1E2430] rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:border-red-500 transition-colors"
                  />
                </div>
                <div>
                  <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">Case Title *</label>
                  <input 
                    type="text"
                    value={caseTitle}
                    onChange={(e) => setCaseTitle(e.target.value)}
                    placeholder="e.g. Dwarka Sector 23 Cash Van Robbery"
                    className="w-full bg-[#11141C] border border-[#1E2430] rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:border-red-500 transition-colors"
                  />
                </div>
                <div>
                  <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">Description / Initial Brief</label>
                  <textarea 
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    rows={4}
                    className="w-full bg-[#11141C] border border-[#1E2430] rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:border-red-500 transition-colors resize-none"
                  />
                </div>
              </div>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">Case Type</label>
                    <select 
                      value={caseType}
                      onChange={(e) => setCaseType(e.target.value)}
                      className="w-full bg-[#11141C] border border-[#1E2430] rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:border-red-500 transition-colors"
                    >
                      <option value="CRIMINAL">CRIMINAL</option>
                      <option value="CYBER">CYBER</option>
                      <option value="ECONOMIC">ECONOMIC</option>
                      <option value="NARCOTICS">NARCOTICS</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">Priority</label>
                    <select 
                      value={priority}
                      onChange={(e) => setPriority(e.target.value)}
                      className="w-full bg-[#11141C] border border-[#1E2430] rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:border-red-500 transition-colors"
                    >
                      <option value="NORMAL">NORMAL</option>
                      <option value="HIGH">HIGH</option>
                      <option value="CRITICAL">CRITICAL</option>
                    </select>
                  </div>
                </div>
                <div>
                  <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">Jurisdiction / Police Station</label>
                  <input 
                    type="text"
                    value={jurisdiction}
                    onChange={(e) => setJurisdiction(e.target.value)}
                    placeholder="e.g. Dwarka PS, Delhi"
                    className="w-full bg-[#11141C] border border-[#1E2430] rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:border-red-500 transition-colors"
                  />
                </div>
                <div>
                  <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">Date of Incident</label>
                  <input 
                    type="date"
                    value={incidentDate}
                    onChange={(e) => setIncidentDate(e.target.value)}
                    className="w-full bg-[#11141C] border border-[#1E2430] rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:border-red-500 transition-colors [color-scheme:dark]"
                  />
                </div>
              </div>
            </div>
          </section>

          {/* Section 2: CASE MATERIAL */}
          <section>
            <h3 className="text-sm font-bold text-slate-300 uppercase tracking-widest border-b border-[#1E2430] pb-2 mb-4">
              CASE MATERIAL
            </h3>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {CATEGORIES.map(category => {
                const Icon = category.icon;
                const categoryFiles = stagedFiles.filter(f => f.category === category.id);
                
                return (
                  <div key={category.id} className="bg-[#11141C] border border-[#1E2430] rounded-lg p-4 hover:border-slate-600 transition-colors relative group">
                    <div className="flex items-center space-x-2 mb-3 text-slate-300">
                      <Icon className="w-4 h-4 text-slate-400" />
                      <span className="text-[10px] font-bold uppercase tracking-wider">{category.label}</span>
                    </div>
                    
                    <label className="cursor-pointer block border-2 border-dashed border-[#2A3140] hover:border-slate-400 rounded-lg p-3 text-center transition-colors">
                      <input type="file" multiple className="hidden" onChange={(e) => handleFileUpload(e, category.id)} />
                      <Plus className="w-5 h-5 text-slate-400 mx-auto mb-1" />
                      <span className="text-xs text-slate-400 font-medium">Upload files</span>
                    </label>
                  </div>
                );
              })}
            </div>

            {/* Staged Files List */}
            {stagedFiles.length > 0 && (
              <div className="mt-6 bg-[#11141C] border border-[#1E2430] rounded-lg p-4">
                <h4 className="text-xs font-bold text-white uppercase tracking-wider mb-3 flex items-center">
                  <CheckCircle2 className="w-4 h-4 text-emerald-500 mr-2" />
                  Files Ready ({stagedFiles.length})
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {stagedFiles.map(fileObj => (
                    <div key={fileObj.id} className="flex items-center justify-between bg-[#0B0F17] border border-[#1E2430] rounded-md p-2.5">
                      <div className="flex items-center space-x-3 overflow-hidden">
                        <div className="w-8 h-8 flex-shrink-0 bg-[#1E2430] rounded flex items-center justify-center">
                          {fileObj.previewUrl ? (
                            <img src={fileObj.previewUrl} alt="preview" className="w-full h-full object-cover rounded" />
                          ) : (
                            <FileText className="w-4 h-4 text-slate-400" />
                          )}
                        </div>
                        <div className="truncate">
                          <div className="text-xs font-semibold text-white truncate" title={fileObj.file.name}>{fileObj.file.name}</div>
                          <div className="text-[10px] text-slate-400 flex space-x-2 mt-0.5">
                            <span>{fileObj.file.type || 'Unknown type'}</span>
                            <span>•</span>
                            <span>{formatFileSize(fileObj.file.size)}</span>
                          </div>
                        </div>
                      </div>
                      <button 
                        onClick={() => removeFile(fileObj.id)}
                        className="p-1.5 text-slate-500 hover:text-red-400 hover:bg-red-500/10 rounded transition-colors"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </section>

        </div>

        {/* Footer / Actions */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-[#1E2430] bg-[#11141C]">
          <div className="flex items-center space-x-3">
            {isProcessing && (
              <>
                <Loader2 className="w-5 h-5 text-red-500 animate-spin" />
                <span className="text-xs font-bold text-white uppercase tracking-widest">{progressState}</span>
              </>
            )}
            {isReady && (
              <>
                <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                <span className="text-xs font-bold text-emerald-400 uppercase tracking-widest">DEMO INTAKE READY</span>
              </>
            )}
          </div>
          
          <div className="flex items-center space-x-3">
            <button 
              onClick={handleClose}
              disabled={isProcessing}
              className="px-4 py-2 text-xs font-bold text-slate-300 hover:text-white transition-colors"
            >
              CANCEL
            </button>
            <button 
              onClick={handlePrepareCase}
              disabled={isProcessing || isReady || !firNumber || !caseTitle}
              className="flex items-center space-x-2 px-6 py-2.5 bg-red-600 hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed text-white text-xs font-bold rounded-md shadow-lg transition-colors"
            >
              {isProcessing ? (
                <span>PROCESSING...</span>
              ) : isReady ? (
                <span>READY</span>
              ) : (
                <>
                  <Upload className="w-4 h-4" />
                  <span>PREPARE CASE</span>
                </>
              )}
            </button>
          </div>
        </div>

      </div>
    </div>
  );
};
