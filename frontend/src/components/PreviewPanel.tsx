import React, { useState, useEffect, useRef, useCallback } from 'react';
import { AdvancedEdit } from '../types';
import realtimePreview from '../services/realtimePreview';

interface PreviewPanelProps {
    sourceVideo: File;
    edits: AdvancedEdit[];
}

const PreviewPanel: React.FC<PreviewPanelProps> = ({ sourceVideo, edits }) => {
    const [originalVideoUrl, setOriginalVideoUrl] = useState<string>('');
    const [previewVideoUrl, setPreviewVideoUrl] = useState<string>('');
    const [isGenerating, setIsGenerating] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [quality, setQuality] = useState<'low' | 'medium' | 'high'>('low');
    const [duration, setDuration] = useState<number>(3);

    const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);
    const regenerateRef = useRef<boolean>(false);

    // Create original video URL on mount
    useEffect(() => {
        const url = URL.createObjectURL(sourceVideo);
        setOriginalVideoUrl(url);

        return () => {
            URL.revokeObjectURL(url);
        };
    }, [sourceVideo]);

    // Generate preview function
    const generatePreviewVideo = useCallback(async () => {
        if (isGenerating) {
            // If already generating, mark for regeneration
            regenerateRef.current = true;
            return;
        }

        try {
            setIsGenerating(true);
            setError(null);
            regenerateRef.current = false;

            // Apply settings to preview service
            realtimePreview.setQuality(quality);
            realtimePreview.setPreviewDuration(duration);

            // Generate preview
            const url = await realtimePreview.generatePreview(sourceVideo, edits);

            // Revoke old preview URL if exists
            if (previewVideoUrl) {
                URL.revokeObjectURL(previewVideoUrl);
            }

            setPreviewVideoUrl(url);
        } catch (err: any) {
            if (err?.message !== 'Preview generation cancelled') {
                console.error('Preview generation error:', err);
                setError(err?.message || 'Failed to generate preview');
            }
        } finally {
            setIsGenerating(false);

            // Check if we need to regenerate
            if (regenerateRef.current) {
                regenerateRef.current = false;
                setTimeout(() => generatePreviewVideo(), 100);
            }
        }
    }, [sourceVideo, edits, quality, duration, isGenerating, previewVideoUrl]);

    // Debounced regeneration on edit changes
    useEffect(() => {
        // Clear existing timer
        if (debounceTimerRef.current) {
            clearTimeout(debounceTimerRef.current);
        }

        // Set new timer for debounced regeneration
        debounceTimerRef.current = setTimeout(() => {
            if (edits.length > 0) {
                generatePreviewVideo();
            }
        }, 500); // 500ms debounce

        return () => {
            if (debounceTimerRef.current) {
                clearTimeout(debounceTimerRef.current);
            }
        };
    }, [edits, quality, duration]); // Regenerate on edits, quality, or duration change

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (previewVideoUrl) {
                URL.revokeObjectURL(previewVideoUrl);
            }
            realtimePreview.cleanup();
            realtimePreview.cancelPreview();
        };
    }, [previewVideoUrl]);

    // Handle quality change
    const handleQualityChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        setQuality(e.target.value as 'low' | 'medium' | 'high');
    };

    // Handle duration change
    const handleDurationChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setDuration(Number(e.target.value));
    };

    // Manual regenerate
    const handleManualRegenerate = () => {
        realtimePreview.cancelPreview();
        generatePreviewVideo();
    };

    return (
        <div style={styles.container}>
            <div style={styles.header}>
                <h3 style={styles.title}>Real-time Preview</h3>
                <div style={styles.controls}>
                    {/* Quality Selector */}
                    <div style={styles.controlGroup}>
                        <label style={styles.label}>Quality:</label>
                        <select
                            value={quality}
                            onChange={handleQualityChange}
                            style={styles.select}
                            disabled={isGenerating}
                        >
                            <option value="low">Low (480p, Fast)</option>
                            <option value="medium">Medium (720p, Balanced)</option>
                            <option value="high">High (1080p, Quality)</option>
                        </select>
                    </div>

                    {/* Duration Slider */}
                    <div style={styles.controlGroup}>
                        <label style={styles.label}>
                            Duration: {duration}s
                        </label>
                        <input
                            type="range"
                            min="1"
                            max="5"
                            step="0.5"
                            value={duration}
                            onChange={handleDurationChange}
                            style={styles.slider}
                            disabled={isGenerating}
                        />
                    </div>

                    {/* Manual Regenerate Button */}
                    <button
                        onClick={handleManualRegenerate}
                        disabled={isGenerating}
                        style={{
                            ...styles.button,
                            opacity: isGenerating ? 0.6 : 1,
                        }}
                    >
                        {isGenerating ? 'Generating...' : 'Regenerate'}
                    </button>
                </div>
            </div>

            {/* Error Display */}
            {error && (
                <div style={styles.error}>
                    <strong>Error:</strong> {error}
                </div>
            )}

            {/* Side-by-side Video Players */}
            <div style={styles.videoContainer}>
                {/* Original Video */}
                <div style={styles.videoPanel}>
                    <div style={styles.videoHeader}>
                        <h4 style={styles.videoTitle}>Original</h4>
                    </div>
                    {originalVideoUrl && (
                        <video
                            src={originalVideoUrl}
                            controls
                            style={styles.video}
                            preload="metadata"
                        />
                    )}
                </div>

                {/* Preview Video */}
                <div style={styles.videoPanel}>
                    <div style={styles.videoHeader}>
                        <h4 style={styles.videoTitle}>Preview with Edits</h4>
                        {isGenerating && (
                            <div style={styles.loadingBadge}>
                                <Spinner />
                                <span style={styles.loadingText}>Generating...</span>
                            </div>
                        )}
                    </div>
                    {previewVideoUrl ? (
                        <video
                            key={previewVideoUrl} // Force reload when URL changes
                            src={previewVideoUrl}
                            controls
                            style={styles.video}
                            preload="metadata"
                            autoPlay
                            muted
                        />
                    ) : (
                        <div style={styles.placeholder}>
                            {isGenerating ? (
                                <div style={styles.loadingContainer}>
                                    <Spinner size={48} />
                                    <p style={styles.loadingMessage}>
                                        Generating preview...
                                    </p>
                                </div>
                            ) : (
                                <div style={styles.emptyState}>
                                    <p style={styles.emptyText}>
                                        {edits.length > 0
                                            ? 'Add edits to see preview'
                                            : 'No preview yet'}
                                    </p>
                                    <button
                                        onClick={handleManualRegenerate}
                                        style={styles.button}
                                    >
                                        Generate Preview
                                    </button>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>

            {/* Info Panel */}
            <div style={styles.infoPanel}>
                <div style={styles.infoItem}>
                    <strong>Active Edits:</strong> {edits.length}
                </div>
                <div style={styles.infoItem}>
                    <strong>Preview Mode:</strong>{' '}
                    {quality === 'low'
                        ? '480p @ 15fps (Fast)'
                        : quality === 'medium'
                        ? '720p @ 24fps (Balanced)'
                        : '1080p @ 30fps (Quality)'}
                </div>
                <div style={styles.infoItem}>
                    <strong>Note:</strong> Preview auto-regenerates 500ms after edit changes
                </div>
            </div>
        </div>
    );
};

// Simple Spinner Component
const Spinner: React.FC<{ size?: number }> = ({ size = 20 }) => (
    <div
        style={{
            width: size,
            height: size,
            border: `${Math.max(2, size / 10)}px solid rgba(255, 255, 255, 0.3)`,
            borderTop: `${Math.max(2, size / 10)}px solid #007bff`,
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
        }}
    />
);

// Styles
const styles: { [key: string]: React.CSSProperties } = {
    container: {
        padding: '20px',
        backgroundColor: '#1a1a1a',
        borderRadius: '8px',
        color: '#ffffff',
        fontFamily: 'system-ui, -apple-system, sans-serif',
    },
    header: {
        marginBottom: '20px',
    },
    title: {
        margin: '0 0 15px 0',
        fontSize: '24px',
        fontWeight: '600',
    },
    controls: {
        display: 'flex',
        gap: '20px',
        alignItems: 'center',
        flexWrap: 'wrap',
        padding: '15px',
        backgroundColor: '#2a2a2a',
        borderRadius: '6px',
    },
    controlGroup: {
        display: 'flex',
        flexDirection: 'column',
        gap: '8px',
    },
    label: {
        fontSize: '14px',
        fontWeight: '500',
        color: '#cccccc',
    },
    select: {
        padding: '8px 12px',
        backgroundColor: '#3a3a3a',
        color: '#ffffff',
        border: '1px solid #4a4a4a',
        borderRadius: '4px',
        fontSize: '14px',
        cursor: 'pointer',
        minWidth: '180px',
    },
    slider: {
        width: '150px',
        cursor: 'pointer',
    },
    button: {
        padding: '8px 16px',
        backgroundColor: '#007bff',
        color: '#ffffff',
        border: 'none',
        borderRadius: '4px',
        fontSize: '14px',
        fontWeight: '500',
        cursor: 'pointer',
        transition: 'background-color 0.2s',
        alignSelf: 'flex-end',
    },
    error: {
        padding: '12px',
        backgroundColor: '#dc3545',
        color: '#ffffff',
        borderRadius: '4px',
        marginBottom: '15px',
        fontSize: '14px',
    },
    videoContainer: {
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: '20px',
        marginBottom: '20px',
    },
    videoPanel: {
        backgroundColor: '#2a2a2a',
        borderRadius: '6px',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
    },
    videoHeader: {
        padding: '12px 16px',
        backgroundColor: '#333333',
        borderBottom: '1px solid #4a4a4a',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
    },
    videoTitle: {
        margin: 0,
        fontSize: '16px',
        fontWeight: '500',
    },
    loadingBadge: {
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        padding: '4px 12px',
        backgroundColor: '#007bff',
        borderRadius: '12px',
        fontSize: '12px',
    },
    loadingText: {
        fontWeight: '500',
    },
    video: {
        width: '100%',
        height: 'auto',
        backgroundColor: '#000000',
        aspectRatio: '16/9',
        objectFit: 'contain',
    },
    placeholder: {
        width: '100%',
        aspectRatio: '16/9',
        backgroundColor: '#1a1a1a',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
    },
    loadingContainer: {
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '16px',
    },
    loadingMessage: {
        margin: 0,
        fontSize: '14px',
        color: '#cccccc',
    },
    emptyState: {
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '12px',
        padding: '40px',
    },
    emptyText: {
        margin: 0,
        fontSize: '16px',
        color: '#888888',
    },
    infoPanel: {
        display: 'flex',
        gap: '20px',
        padding: '12px 16px',
        backgroundColor: '#2a2a2a',
        borderRadius: '6px',
        fontSize: '13px',
        color: '#cccccc',
        flexWrap: 'wrap',
    },
    infoItem: {
        display: 'flex',
        gap: '6px',
    },
};

// Add keyframe animation for spinner (inject into document)
if (typeof document !== 'undefined') {
    const styleSheet = document.styleSheets[0];
    const keyframes = `
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    `;

    try {
        styleSheet.insertRule(keyframes, styleSheet.cssRules.length);
    } catch (e) {
        // Already exists or error, ignore
    }
}

export default PreviewPanel;
