import React, { useState, useRef } from 'react';
import { LayoutDashboard, Upload, CheckCircle2, AlertTriangle, XCircle, Search, Activity, Camera, Link as LinkIcon, Database, ExternalLink } from 'lucide-react';
import { Link } from 'react-router-dom';
import { biometricApi } from '../api/biometric';
import type { BiometricSearchResponse, BiometricContextResponse, BiometricReference } from '../api/biometric';

const BiometricIntelligencePage: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [imagePreviewUrl, setImagePreviewUrl] = useState<string | null>(null);
  
  const [isSearching, setIsSearching] = useState(false);
  const [searchResult, setSearchResult] = useState<BiometricSearchResponse | null>(null);
  const [context, setContext] = useState<BiometricContextResponse | null>(null);
  const [references, setReferences] = useState<BiometricReference[]>([]);
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreviewUrl(reader.result as string);
      };
      reader.readAsDataURL(file);
      
      // Reset state
      setSearchResult(null);
      setContext(null);
      setReferences([]);
    }
  };

  const triggerFileInput = () => {
    fileInputRef.current?.click();
  };

  const handleSearch = async () => {
    if (!selectedFile) return;
    
    setIsSearching(true);
    try {
      const result = await biometricApi.search(selectedFile);
      setSearchResult(result);
      
      if (result.person_id) {
        // Fetch context and references
        const [contextData, refsData] = await Promise.all([
          biometricApi.getContext(result.person_id),
          biometricApi.getReferences(result.person_id)
        ]);
        setContext(contextData);
        setReferences(refsData.references || []);
      }
    } catch (error) {
      console.error('Biometric search failed:', error);
      setSearchResult({
        status: 'ERROR',
        detected_faces: 0,
        error_message: 'Biometric engine encountered an error.'
      });
    } finally {
      setIsSearching(false);
    }
  };
  
  const getBandColor = (band?: string) => {
    switch (band) {
      case 'HIGH': return 'text-green-500';
      case 'MEDIUM': return 'text-yellow-500';
      case 'LOW': return 'text-orange-500';
      case 'UNCERTAIN': return 'text-red-500';
      default: return 'text-gray-400';
    }
  };

  return (
    <div className="h-full bg-[#07090E] text-slate-300 p-6 overflow-y-auto">
      
      {/* HEADER & DATA SOURCES */}
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-slate-100 flex items-center gap-2 mb-6">
          <Activity className="w-6 h-6 text-[#E6B325]" />
          Biometric & Facial Intelligence
        </h1>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-[#151b23] border border-[#1E2430] rounded p-4 flex items-start gap-3">
            <Database className="w-5 h-5 text-green-500 mt-0.5" />
            <div>
              <h3 className="text-sm font-medium text-slate-200">CIVIX SYNTHETIC BIOMETRIC INDEX</h3>
              <p className="text-xs text-green-500 mt-1 uppercase tracking-wider font-semibold">Operational</p>
            </div>
          </div>
          
          <div className="bg-[#151b23] border border-[#1E2430] rounded p-4 flex items-start gap-3">
            <LinkIcon className="w-5 h-5 text-yellow-600 mt-0.5" />
            <div>
              <h3 className="text-sm font-medium text-slate-200">AUTHORIZED IDENTITY CONNECTOR</h3>
              <p className="text-xs text-yellow-600 mt-1 uppercase tracking-wider font-semibold">READY — NOT CONNECTED</p>
              <p className="text-[10px] text-slate-500 mt-1">Government authorization required</p>
            </div>
          </div>
          
          <div className="bg-[#151b23] border border-[#1E2430] rounded p-4 flex items-start gap-3">
            <LayoutDashboard className="w-5 h-5 text-blue-500 mt-0.5" />
            <div>
              <h3 className="text-sm font-medium text-slate-200">SYNTHETIC IDENTITY SERVICE</h3>
              <p className="text-xs text-blue-500 mt-1 uppercase tracking-wider font-semibold">Available</p>
            </div>
          </div>
        </div>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* LEFT PANEL: INPUT & ANALYSIS */}
        <div className="lg:col-span-5 space-y-6">
          <div className="bg-[#151b23] border border-[#1E2430] rounded overflow-hidden">
            <div className="px-4 py-3 border-b border-[#1E2430] flex justify-between items-center bg-[#0f141a]">
              <h2 className="text-sm font-medium text-slate-200 flex items-center gap-2">
                <Camera className="w-4 h-4 text-slate-400" />
                Image Input
              </h2>
            </div>
            
            <div className="p-4">
              <div 
                className={`border-2 border-dashed rounded-lg p-6 flex flex-col items-center justify-center text-center cursor-pointer transition-colors ${
                  imagePreviewUrl ? 'border-[#30363d] bg-[#0d1117]' : 'border-[#30363d] hover:border-[#E6B325] hover:bg-[#1c2128]'
                }`}
                onClick={triggerFileInput}
                style={{ minHeight: '300px' }}
              >
                <input 
                  type="file" 
                  ref={fileInputRef}
                  className="hidden" 
                  accept="image/jpeg, image/png, image/webp"
                  onChange={handleFileChange}
                />
                
                {imagePreviewUrl ? (
                  <div className="relative w-full h-full flex items-center justify-center">
                    <img 
                      src={imagePreviewUrl} 
                      alt="Upload preview" 
                      className="max-h-[400px] max-w-full object-contain rounded"
                    />
                    
                    {/* Render bounding box if available */}
                    {searchResult?.face_bounding_box && (
                      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                        <div className="relative" style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                           {/* Since we don't know the exact rendered size vs original size easily here without a resize observer, 
                               we'll rely on the visual indicator overlay. For a production app we'd map coords precisely. */}
                           <div className="absolute top-4 right-4 bg-black/60 px-2 py-1 rounded text-xs text-[#E6B325] border border-[#E6B325]/30">
                             Face Detected
                           </div>
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="w-16 h-16 bg-[#1c2128] rounded-full flex items-center justify-center mx-auto text-slate-400">
                      <Upload className="w-8 h-8" />
                    </div>
                    <div>
                      <p className="text-sm text-slate-300 font-medium">Click to upload face image</p>
                      <p className="text-xs text-slate-500 mt-1">JPEG, PNG or WEBP</p>
                    </div>
                  </div>
                )}
              </div>
              
              <div className="mt-4">
                <button
                  onClick={handleSearch}
                  disabled={!selectedFile || isSearching}
                  className={`w-full py-2.5 rounded text-sm font-medium flex items-center justify-center gap-2 transition-colors ${
                    !selectedFile || isSearching 
                      ? 'bg-[#1c2128] text-slate-500 cursor-not-allowed' 
                      : 'bg-[#E6B325] text-black hover:bg-[#f5c338]'
                  }`}
                >
                  {isSearching ? (
                    <>
                      <div className="w-4 h-4 border-2 border-slate-500 border-t-transparent rounded-full animate-spin"></div>
                      Processing Analysis...
                    </>
                  ) : (
                    <>
                      <Search className="w-4 h-4" />
                      Run Biometric Search
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
          
          {/* Analysis Telemetry */}
          {searchResult && (
            <div className="bg-[#151b23] border border-[#1E2430] rounded overflow-hidden">
              <div className="px-4 py-3 border-b border-[#1E2430] bg-[#0f141a]">
                <h2 className="text-sm font-medium text-slate-200">Analysis Telemetry</h2>
              </div>
              <div className="p-4 space-y-3">
                <div className="flex justify-between items-center text-sm">
                  <span className="text-slate-400">Detected Faces:</span>
                  <span className="text-slate-200 font-mono">{searchResult.detected_faces}</span>
                </div>
                {searchResult.status !== 'ERROR' && (
                  <>
                    <div className="flex justify-between items-center text-sm">
                      <span className="text-slate-400">Model Version:</span>
                      <span className="text-slate-200 font-mono">{searchResult.model_version || 'N/A'}</span>
                    </div>
                    <div className="flex justify-between items-center text-sm">
                      <span className="text-slate-400">Index Source:</span>
                      <span className="text-slate-200 font-mono">{searchResult.index_source || 'N/A'}</span>
                    </div>
                  </>
                )}
              </div>
            </div>
          )}
        </div>
        
        {/* RIGHT PANEL: RESULTS & CONTEXT */}
        <div className="lg:col-span-7 space-y-6">
          
          {!searchResult && !isSearching && (
            <div className="bg-[#151b23] border border-[#1E2430] rounded p-12 flex flex-col items-center justify-center text-center h-full min-h-[400px]">
              <div className="w-16 h-16 rounded-full bg-[#1c2128] flex items-center justify-center mb-4">
                <Search className="w-8 h-8 text-slate-500" />
              </div>
              <h3 className="text-lg font-medium text-slate-300">Awaiting Input</h3>
              <p className="text-sm text-slate-500 mt-2 max-w-sm">
                Upload a face image to search the CIVIX biometric index and retrieve linked investigative context.
              </p>
            </div>
          )}
          
          {searchResult && (
            <>
              {/* STATUS BANNER */}
              <div className={`border rounded p-4 flex items-start gap-4 ${
                searchResult.status === 'MATCH_FOUND' ? 'bg-green-950/20 border-green-900/50' :
                searchResult.status === 'AMBIGUOUS_MATCH' ? 'bg-yellow-950/20 border-yellow-900/50' :
                searchResult.status === 'NO_CIVIX_MATCH' ? 'bg-orange-950/20 border-orange-900/50' :
                'bg-red-950/20 border-red-900/50'
              }`}>
                <div className="mt-1">
                  {searchResult.status === 'MATCH_FOUND' ? <CheckCircle2 className="w-6 h-6 text-green-500" /> :
                   searchResult.status === 'AMBIGUOUS_MATCH' ? <AlertTriangle className="w-6 h-6 text-yellow-500" /> :
                   searchResult.status === 'NO_CIVIX_MATCH' ? <Activity className="w-6 h-6 text-orange-500" /> :
                   <XCircle className="w-6 h-6 text-red-500" />}
                </div>
                <div>
                  <h2 className={`text-lg font-bold tracking-wider ${
                    searchResult.status === 'MATCH_FOUND' ? 'text-green-500' :
                    searchResult.status === 'AMBIGUOUS_MATCH' ? 'text-yellow-500' :
                    searchResult.status === 'NO_CIVIX_MATCH' ? 'text-orange-500' :
                    'text-red-500'
                  }`}>
                    {searchResult.status.replace(/_/g, ' ')}
                  </h2>
                  
                  {searchResult.error_message ? (
                    <p className="text-sm text-slate-300 mt-1">{searchResult.error_message}</p>
                  ) : searchResult.status === 'MULTIPLE_FACES_DETECTED' ? (
                    <p className="text-sm text-slate-400 mt-1">Multiple prominent faces were detected in this image. Please upload a clear photo focusing on a single subject.</p>
                  ) : searchResult.status === 'NO_FACE_DETECTED' ? (
                    <p className="text-sm text-slate-400 mt-1">No human face could be detected in the uploaded image. Please try a clearer front-facing portrait.</p>
                  ) : null}
                  
                  {searchResult.match_score !== undefined && (
                    <div className="flex gap-4 mt-2">
                      <div className="text-xs">
                        <span className="text-slate-500 mr-1">Match Score:</span>
                        <span className="font-mono text-slate-300">{searchResult.match_score.toFixed(4)}</span>
                      </div>
                      <div className="text-xs">
                        <span className="text-slate-500 mr-1">Confidence Band:</span>
                        <span className={`font-mono font-semibold ${getBandColor(searchResult.confidence_band)}`}>
                          {searchResult.confidence_band}
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              </div>
              
              {/* PROFILE RESULT */}
              {(searchResult.status === 'MATCH_FOUND' || searchResult.status === 'AMBIGUOUS_MATCH') && searchResult.person_id && (
                <div className="bg-[#151b23] border border-[#1E2430] rounded p-5 flex items-start gap-6">
                  {searchResult.avatar_url ? (
                    <img 
                      src={searchResult.avatar_url} 
                      alt={searchResult.person_name} 
                      className="w-24 h-24 object-cover rounded border border-[#30363d]"
                    />
                  ) : (
                    <div className="w-24 h-24 bg-[#1c2128] rounded border border-[#30363d] flex items-center justify-center text-slate-500">
                      No Photo
                    </div>
                  )}
                  
                  <div className="flex-1">
                    <div className="flex justify-between items-start">
                      <div>
                        <h2 className="text-xl font-bold text-slate-100">{searchResult.person_name}</h2>
                        <div className="text-xs font-mono text-slate-500 mt-1">ID: {searchResult.person_id}</div>
                      </div>
                      <div className="text-right">
                        <div className={`px-3 py-1 text-xs font-bold rounded inline-block ${
                          searchResult.classification === 'INVESTIGATIVE_SUBJECT' 
                            ? 'bg-red-950/30 text-red-500 border border-red-900/50' 
                            : 'bg-blue-950/30 text-blue-400 border border-blue-900/50'
                        }`}>
                          {searchResult.classification?.replace(/_/g, ' ')}
                        </div>
                        <div className="text-xs text-slate-400 mt-1 uppercase tracking-wider font-semibold">
                          {searchResult.primary_role?.replace(/_/g, ' ')}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
              
              {/* SYNTHETIC FALLBACK */}
              {searchResult.status === 'NO_CIVIX_MATCH' && searchResult.synthetic_identity && (
                <div className="bg-[#151b23] border border-orange-900/50 rounded overflow-hidden">
                  <div className="bg-orange-950/20 px-4 py-2 border-b border-orange-900/50 flex justify-between items-center">
                    <span className="text-xs font-bold text-orange-500">{searchResult.synthetic_identity.status}</span>
                    <span className="text-xs font-bold text-orange-500 bg-orange-950 px-2 py-0.5 rounded">{searchResult.synthetic_identity.label}</span>
                  </div>
                  <div className="p-5">
                    <h2 className="text-xl font-bold text-slate-200">{searchResult.synthetic_identity.name}</h2>
                    <div className="text-xs font-mono text-slate-500 mt-1 mb-4">SEED: {searchResult.synthetic_identity.image_hash_prefix}</div>
                    
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div><span className="text-slate-500">Age:</span> <span className="text-slate-300">{searchResult.synthetic_identity.age}</span></div>
                      <div><span className="text-slate-500">Occupation:</span> <span className="text-slate-300">{searchResult.synthetic_identity.occupation}</span></div>
                      <div><span className="text-slate-500">City:</span> <span className="text-slate-300">{searchResult.synthetic_identity.city}</span></div>
                      <div><span className="text-slate-500">Phone:</span> <span className="text-slate-300">{searchResult.synthetic_identity.phone}</span></div>
                      <div className="col-span-2"><span className="text-slate-500">Address:</span> <span className="text-slate-300">{searchResult.synthetic_identity.address}</span></div>
                    </div>
                  </div>
                </div>
              )}
              
              {/* CANONICAL CONTEXT */}
              {context && (
                <div className="bg-[#151b23] border border-[#1E2430] rounded overflow-hidden">
                  <div className="px-4 py-3 border-b border-[#1E2430] bg-[#0f141a]">
                    <h2 className="text-sm font-medium text-slate-200 flex items-center gap-2">
                      <LinkIcon className="w-4 h-4 text-slate-400" />
                      CIVIX Investigative Context
                    </h2>
                  </div>
                  
                  <div className="p-4 space-y-6">
                    {/* Cases */}
                    {context.cases && context.cases.length > 0 && (
                      <div>
                        <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Linked Cases ({context.cases.length})</h3>
                        <div className="space-y-2">
                          {context.cases.map(c => (
                            <Link to={`/cases/${c.case_id}`} key={c.case_id} className="block bg-[#1c2128] hover:bg-[#22272e] p-3 rounded border border-[#30363d] transition-colors">
                              <div className="flex justify-between items-start">
                                <div>
                                  <div className="text-xs font-mono text-[#E6B325]">{c.case_number}</div>
                                  <div className="text-sm text-slate-200 font-medium mt-0.5">{c.title}</div>
                                </div>
                                <div className="text-right">
                                  <div className="text-[10px] text-slate-400 uppercase">{c.status}</div>
                                  <div className="text-[10px] text-slate-500 mt-1">Role: {c.role}</div>
                                </div>
                              </div>
                            </Link>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {/* Events & Evidence & Leads Summaries */}
                    <div className="grid grid-cols-3 gap-4">
                      <div className="bg-[#1c2128] rounded border border-[#30363d] p-3 text-center">
                        <div className="text-xl font-bold text-slate-200">{context.evidence?.length || 0}</div>
                        <div className="text-[10px] text-slate-500 uppercase tracking-wider mt-1">Evidence Links</div>
                      </div>
                      <div className="bg-[#1c2128] rounded border border-[#30363d] p-3 text-center">
                        <div className="text-xl font-bold text-slate-200">{context.events?.length || 0}</div>
                        <div className="text-[10px] text-slate-500 uppercase tracking-wider mt-1">Event Links</div>
                      </div>
                      <div className="bg-[#1c2128] rounded border border-[#30363d] p-3 text-center">
                        <div className="text-xl font-bold text-slate-200">{context.leads?.length || 0}</div>
                        <div className="text-[10px] text-slate-500 uppercase tracking-wider mt-1">Active Leads</div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
              
              {/* BIOMETRIC REFERENCES */}
              {references && references.length > 0 && (
                <div className="bg-[#151b23] border border-[#1E2430] rounded overflow-hidden mt-6">
                  <div className="px-4 py-3 border-b border-[#1E2430] bg-[#0f141a]">
                    <h2 className="text-sm font-medium text-slate-200 flex items-center gap-2">
                      <Database className="w-4 h-4 text-slate-400" />
                      Index References ({references.length})
                    </h2>
                  </div>
                  
                  <div className="p-4 grid grid-cols-2 md:grid-cols-4 gap-3">
                    {references.map(ref => (
                      <div key={ref.ref_id} className="bg-[#1c2128] rounded border border-[#30363d] overflow-hidden relative group">
                        <img 
                          src={`http://127.0.0.1:8000/api/v1/${ref.image_path}`} 
                          alt={ref.quality_note}
                          className="w-full aspect-square object-cover"
                        />
                        {ref.is_derived && (
                          <div className="absolute top-1 right-1 bg-black/70 text-[9px] font-bold text-orange-500 px-1.5 py-0.5 rounded border border-orange-900/50">
                            DERIVED
                          </div>
                        )}
                        <div className="p-2">
                          <div className="text-[10px] text-slate-400 truncate">{ref.quality_note}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default BiometricIntelligencePage;
