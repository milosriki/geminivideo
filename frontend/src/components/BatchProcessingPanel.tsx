import { useState, useEffect, useCallback, useRef } from 'react';
import {
  batchProcessor,
  BatchJob,
  BatchQueueState,
  EditTemplate
} from '../services/batchProcessor';
import { AdCreative, AdvancedEdit } from '../types';

export default function BatchProcessingPanel() {
  const [queueState, setQueueState] = useState<BatchQueueState>(batchProcessor.getQueueState());
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [templateMode, setTemplateMode] = useState<'creative' | 'advanced'>('advanced');
  const [concurrentLimit, setConcurrentLimit] = useState(2);
  const [showStats, setShowStats] = useState(true);

  // Template configuration state
  const [editConfig, setEditConfig] = useState<AdvancedEdit[]>([]);

  // File input ref
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Polling interval for queue state updates
  useEffect(() => {
    const interval = setInterval(() => {
      setQueueState(batchProcessor.getQueueState());
    }, 500);

    return () => clearInterval(interval);
  }, []);

  // Setup callbacks
  useEffect(() => {
    batchProcessor.onJobComplete((job) => {
      console.log('Job completed:', job.id);
      setQueueState(batchProcessor.getQueueState());
    });

    batchProcessor.onJobError((job) => {
      console.error('Job failed:', job.id, job.error);
      setQueueState(batchProcessor.getQueueState());
    });

    batchProcessor.onQueueComplete(() => {
      console.log('All jobs completed!');
      setQueueState(batchProcessor.getQueueState());
    });
  }, []);

  // File drop handlers
  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = Array.from(e.dataTransfer.files).filter(file =>
      file.type.startsWith('video/')
    );

    if (files.length > 0) {
      setSelectedFiles(prev => [...prev, ...files]);
    }
  }, []);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files ? Array.from(e.target.files) : [];
    if (files.length > 0) {
      setSelectedFiles(prev => [...prev, ...files]);
    }
  }, []);

  const removeSelectedFile = useCallback((index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  }, []);

  const handleAddToQueue = useCallback(() => {
    if (selectedFiles.length === 0) {
      alert('Please select at least one video file');
      return;
    }

    // Create template based on mode
    let template: EditTemplate;

    if (templateMode === 'creative') {
      // For demo purposes, create a simple creative template
      const sampleCreative: AdCreative = {
        primarySourceFileName: selectedFiles[0].name,
        variationTitle: 'Batch Processed Video',
        headline: 'Automated Edit',
        body: 'Processed with batch system',
        cta: 'Learn More',
        editPlan: [
          {
            timestamp: '0s-5s',
            visual: 'Opening scene',
            edit: 'Intro',
            sourceFile: selectedFiles[0].name
          }
        ]
      };

      template = {
        mode: 'creative',
        creative: sampleCreative,
        sourceVideos: selectedFiles
      };
    } else {
      // Advanced mode - use configured edits
      template = {
        mode: 'advanced',
        edits: editConfig.length > 0 ? editConfig : [
          { id: '1', type: 'trim', start: '0', end: '10' }
        ]
      };
    }

    // Add jobs to queue
    const jobIds = batchProcessor.addToQueue(selectedFiles, template);
    console.log(`Added ${jobIds.length} jobs to queue`);

    // Clear selected files
    setSelectedFiles([]);

    // Update state
    setQueueState(batchProcessor.getQueueState());
  }, [selectedFiles, templateMode, editConfig]);

  const handleCancelJob = useCallback((jobId: string) => {
    batchProcessor.cancelJob(jobId);
    setQueueState(batchProcessor.getQueueState());
  }, []);

  const handleRetryJob = useCallback((jobId: string) => {
    batchProcessor.retryJob(jobId);
    setQueueState(batchProcessor.getQueueState());
  }, []);

  const handleRemoveJob = useCallback((jobId: string) => {
    batchProcessor.removeFromQueue(jobId);
    setQueueState(batchProcessor.getQueueState());
  }, []);

  const handlePauseQueue = useCallback(() => {
    batchProcessor.pauseQueue();
    setQueueState(batchProcessor.getQueueState());
  }, []);

  const handleResumeQueue = useCallback(() => {
    batchProcessor.resumeQueue();
    setQueueState(batchProcessor.getQueueState());
  }, []);

  const handleClearCompleted = useCallback(() => {
    batchProcessor.clearCompleted();
    setQueueState(batchProcessor.getQueueState());
  }, []);

  const handleClearAll = useCallback(() => {
    if (confirm('Are you sure you want to clear all jobs? This cannot be undone.')) {
      batchProcessor.clearAll();
      setQueueState(batchProcessor.getQueueState());
    }
  }, []);

  const handleDownloadAll = useCallback(async () => {
    try {
      await batchProcessor.downloadAll();
    } catch (error: any) {
      alert(error.message);
    }
  }, []);

  const handleDownloadJob = useCallback((job: BatchJob) => {
    if (job.outputUrl) {
      const link = document.createElement('a');
      link.href = job.outputUrl;
      link.download = `${job.sourceVideo.name.replace(/\.[^/.]+$/, '')}_processed.mp4`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  }, []);

  const handleConcurrentLimitChange = useCallback((limit: number) => {
    setConcurrentLimit(limit);
    batchProcessor.setConcurrentLimit(limit);
    setQueueState(batchProcessor.getQueueState());
  }, []);

  const addSimpleEdit = useCallback((type: 'mute' | 'grayscale' | 'sepia') => {
    const newEdit: AdvancedEdit =
      type === 'mute'
        ? { id: Date.now().toString(), type: 'mute' }
        : { id: Date.now().toString(), type: 'filter', name: type };

    setEditConfig(prev => [...prev, newEdit]);
  }, []);

  const removeEdit = useCallback((id: string) => {
    setEditConfig(prev => prev.filter(e => e.id !== id));
  }, []);

  // Calculate statistics
  const totalJobs = queueState.jobs.length;
  const pendingJobs = queueState.jobs.filter(j => j.status === 'pending').length;
  const processingJobs = queueState.jobs.filter(j => j.status === 'processing').length;
  const avgProgress = totalJobs > 0
    ? queueState.jobs.reduce((sum, job) => sum + job.progress, 0) / totalJobs
    : 0;

  const totalProcessingTime = queueState.jobs
    .filter(j => j.completedAt && j.startedAt)
    .reduce((sum, job) => {
      const start = job.startedAt!.getTime();
      const end = job.completedAt!.getTime();
      return sum + (end - start);
    }, 0);

  const avgProcessingTime = queueState.completedCount > 0
    ? totalProcessingTime / queueState.completedCount / 1000
    : 0;

  return (
    <div className="card">
      <div className="panel-header">
        <h2>Batch Video Processing</h2>
      </div>

      <p style={{ marginBottom: '20px', color: '#666' }}>
        Process multiple videos with the same template. Drag and drop files or click to select.
      </p>

      {/* File Dropzone */}
      <div
        onDragEnter={handleDragEnter}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        style={{
          border: `2px dashed ${isDragging ? '#007bff' : '#ccc'}`,
          borderRadius: '8px',
          padding: '40px',
          textAlign: 'center',
          cursor: 'pointer',
          backgroundColor: isDragging ? '#f0f8ff' : '#fafafa',
          marginBottom: '20px',
          transition: 'all 0.3s ease'
        }}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="video/*"
          multiple
          onChange={handleFileSelect}
          style={{ display: 'none' }}
        />
        <div style={{ fontSize: '48px', marginBottom: '10px' }}>🎬</div>
        <h3>Drop video files here</h3>
        <p style={{ color: '#666' }}>or click to browse</p>
      </div>

      {/* Selected Files */}
      {selectedFiles.length > 0 && (
        <div className="card" style={{ marginBottom: '20px', border: '1px solid #e0e0e0' }}>
          <h3>Selected Files ({selectedFiles.length})</h3>
          <div style={{ maxHeight: '150px', overflowY: 'auto' }}>
            {selectedFiles.map((file, index) => (
              <div
                key={index}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '8px',
                  borderBottom: '1px solid #f0f0f0'
                }}
              >
                <span style={{ fontSize: '14px' }}>
                  {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
                </span>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    removeSelectedFile(index);
                  }}
                  style={{
                    background: '#dc3545',
                    color: 'white',
                    border: 'none',
                    padding: '4px 8px',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '12px'
                  }}
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Template Configuration */}
      <div className="card" style={{ marginBottom: '20px', border: '1px solid #007bff' }}>
        <h3>Template Configuration</h3>

        <div style={{ marginBottom: '15px' }}>
          <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
            Processing Mode:
          </label>
          <select
            className="input"
            value={templateMode}
            onChange={(e) => setTemplateMode(e.target.value as 'creative' | 'advanced')}
          >
            <option value="advanced">Advanced Edits</option>
            <option value="creative">Creative Template</option>
          </select>
        </div>

        {templateMode === 'advanced' && (
          <div>
            <h4>Quick Edit Presets:</h4>
            <div style={{ display: 'flex', gap: '10px', marginBottom: '15px', flexWrap: 'wrap' }}>
              <button className="button" onClick={() => addSimpleEdit('mute')}>
                Add Mute
              </button>
              <button className="button" onClick={() => addSimpleEdit('grayscale')}>
                Add Grayscale
              </button>
              <button className="button" onClick={() => addSimpleEdit('sepia')}>
                Add Sepia
              </button>
            </div>

            {editConfig.length > 0 && (
              <div>
                <h4>Current Edits ({editConfig.length}):</h4>
                {editConfig.map((edit) => (
                  <div
                    key={edit.id}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '8px',
                      background: '#f5f5f5',
                      borderRadius: '4px',
                      marginBottom: '5px'
                    }}
                  >
                    <span>{edit.type}</span>
                    <button
                      onClick={() => removeEdit(edit.id)}
                      style={{
                        background: '#dc3545',
                        color: 'white',
                        border: 'none',
                        padding: '4px 8px',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '12px'
                      }}
                    >
                      Remove
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        <div style={{ marginTop: '15px' }}>
          <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
            Concurrent Processing Limit: {concurrentLimit}
          </label>
          <input
            type="range"
            min="1"
            max="5"
            value={concurrentLimit}
            onChange={(e) => handleConcurrentLimitChange(parseInt(e.target.value))}
            style={{ width: '100%' }}
          />
          <small style={{ color: '#666' }}>
            Higher values process faster but use more memory
          </small>
        </div>

        <button
          className="button"
          onClick={handleAddToQueue}
          disabled={selectedFiles.length === 0}
          style={{
            marginTop: '15px',
            width: '100%',
            background: selectedFiles.length === 0 ? '#ccc' : '#007bff'
          }}
        >
          Add {selectedFiles.length} Video{selectedFiles.length !== 1 ? 's' : ''} to Queue
        </button>
      </div>

      {/* Statistics */}
      {showStats && totalJobs > 0 && (
        <div className="card" style={{ marginBottom: '20px', border: '1px solid #28a745' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
            <h3>Statistics</h3>
            <button onClick={() => setShowStats(false)} style={{ border: 'none', background: 'none', cursor: 'pointer' }}>
              ✕
            </button>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '15px' }}>
            <div className="metric-card">
              <h4>Total Jobs</h4>
              <div className="value">{totalJobs}</div>
            </div>
            <div className="metric-card">
              <h4>Completed</h4>
              <div className="value" style={{ color: '#28a745' }}>{queueState.completedCount}</div>
            </div>
            <div className="metric-card">
              <h4>Processing</h4>
              <div className="value" style={{ color: '#ffc107' }}>{processingJobs}</div>
            </div>
            <div className="metric-card">
              <h4>Pending</h4>
              <div className="value" style={{ color: '#007bff' }}>{pendingJobs}</div>
            </div>
            <div className="metric-card">
              <h4>Errors</h4>
              <div className="value" style={{ color: '#dc3545' }}>{queueState.errorCount}</div>
            </div>
            <div className="metric-card">
              <h4>Avg Progress</h4>
              <div className="value">{(avgProgress * 100).toFixed(0)}%</div>
            </div>
            {queueState.completedCount > 0 && (
              <div className="metric-card">
                <h4>Avg Time</h4>
                <div className="value">{avgProcessingTime.toFixed(1)}s</div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Bulk Actions */}
      {totalJobs > 0 && (
        <div className="card" style={{ marginBottom: '20px', border: '1px solid #6c757d' }}>
          <h3>Queue Controls</h3>
          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
            {queueState.isProcessing ? (
              <button className="button" onClick={handlePauseQueue}>
                ⏸ Pause Queue
              </button>
            ) : (
              <button className="button" onClick={handleResumeQueue} disabled={pendingJobs === 0}>
                ▶ Resume Queue
              </button>
            )}
            <button
              className="button"
              onClick={handleClearCompleted}
              disabled={queueState.completedCount === 0}
            >
              🗑 Clear Completed
            </button>
            <button
              className="button"
              onClick={handleDownloadAll}
              disabled={queueState.completedCount === 0}
              style={{ background: '#28a745' }}
            >
              ⬇ Download All ({queueState.completedCount})
            </button>
            <button
              className="button"
              onClick={handleClearAll}
              style={{ background: '#dc3545' }}
            >
              🗑 Clear All
            </button>
          </div>
        </div>
      )}

      {/* Job Queue List */}
      {totalJobs > 0 && (
        <div className="card" style={{ border: '1px solid #e0e0e0' }}>
          <h3>Job Queue ({totalJobs})</h3>
          <div style={{ maxHeight: '500px', overflowY: 'auto' }}>
            {queueState.jobs.map((job) => (
              <div
                key={job.id}
                className="card"
                style={{
                  marginBottom: '15px',
                  border: `1px solid ${
                    job.status === 'complete' ? '#28a745' :
                    job.status === 'error' ? '#dc3545' :
                    job.status === 'processing' ? '#ffc107' :
                    job.status === 'cancelled' ? '#6c757d' :
                    '#007bff'
                  }`
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                  <div>
                    <strong>{job.sourceVideo.name}</strong>
                    <div style={{ fontSize: '12px', color: '#666' }}>
                      {(job.sourceVideo.size / 1024 / 1024).toFixed(2)} MB
                    </div>
                  </div>
                  <span
                    className={`status-badge ${
                      job.status === 'complete' ? 'success' :
                      job.status === 'error' ? 'error' :
                      job.status === 'processing' ? 'warning' :
                      job.status === 'cancelled' ? 'info' :
                      'info'
                    }`}
                  >
                    {job.status.toUpperCase()}
                  </span>
                </div>

                {/* Progress Bar */}
                {(job.status === 'processing' || job.status === 'pending') && (
                  <div style={{ marginBottom: '10px' }}>
                    <div style={{
                      width: '100%',
                      height: '8px',
                      backgroundColor: '#e0e0e0',
                      borderRadius: '4px',
                      overflow: 'hidden'
                    }}>
                      <div style={{
                        width: `${job.progress * 100}%`,
                        height: '100%',
                        backgroundColor: job.status === 'processing' ? '#007bff' : '#6c757d',
                        transition: 'width 0.3s ease'
                      }} />
                    </div>
                    <div style={{ fontSize: '12px', color: '#666', marginTop: '5px' }}>
                      {(job.progress * 100).toFixed(0)}%
                    </div>
                  </div>
                )}

                {/* Error Message */}
                {job.error && (
                  <div className="error" style={{ marginBottom: '10px', fontSize: '12px' }}>
                    {job.error}
                  </div>
                )}

                {/* Timestamps */}
                {job.completedAt && (
                  <div style={{ fontSize: '11px', color: '#666', marginBottom: '10px' }}>
                    Completed: {new Date(job.completedAt).toLocaleTimeString()}
                    {job.startedAt && ` (${((new Date(job.completedAt).getTime() - new Date(job.startedAt).getTime()) / 1000).toFixed(1)}s)`}
                  </div>
                )}

                {/* Job Actions */}
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                  {job.status === 'processing' && (
                    <button
                      onClick={() => handleCancelJob(job.id)}
                      style={{
                        background: '#dc3545',
                        color: 'white',
                        border: 'none',
                        padding: '6px 12px',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '12px'
                      }}
                    >
                      Cancel
                    </button>
                  )}

                  {job.status === 'error' && (
                    <button
                      onClick={() => handleRetryJob(job.id)}
                      style={{
                        background: '#ffc107',
                        color: 'black',
                        border: 'none',
                        padding: '6px 12px',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '12px'
                      }}
                    >
                      Retry
                    </button>
                  )}

                  {job.status === 'complete' && job.outputUrl && (
                    <button
                      onClick={() => handleDownloadJob(job)}
                      style={{
                        background: '#28a745',
                        color: 'white',
                        border: 'none',
                        padding: '6px 12px',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '12px'
                      }}
                    >
                      Download
                    </button>
                  )}

                  {(job.status === 'pending' || job.status === 'complete' || job.status === 'error' || job.status === 'cancelled') && (
                    <button
                      onClick={() => handleRemoveJob(job.id)}
                      style={{
                        background: '#6c757d',
                        color: 'white',
                        border: 'none',
                        padding: '6px 12px',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '12px'
                      }}
                    >
                      Remove
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {totalJobs === 0 && (
        <div className="card" style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
          <div style={{ fontSize: '48px', marginBottom: '10px' }}>📋</div>
          <h3>No jobs in queue</h3>
          <p>Add videos above to get started with batch processing</p>
        </div>
      )}
    </div>
  );
}
