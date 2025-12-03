/**
 * AudioSuitePanel Component
 * Professional audio processing interface with real-time controls
 * Features: Loudness normalization, voice enhancement, ducking, noise reduction, and more
 */

import React, { useState, useRef, useEffect } from 'react';
import { AudioProcessor, LoudnessStats, SilenceSegment } from '../services/audioProcessor';

// Simple icons
const Spinner = () => (
    <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
    </svg>
);

const VolumeIcon: React.FC<{ className?: string }> = ({ className }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
    </svg>
);

const MicIcon: React.FC<{ className?: string }> = ({ className }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
    </svg>
);

const MusicIcon: React.FC<{ className?: string }> = ({ className }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
    </svg>
);

const SparklesIcon: React.FC<{ className?: string }> = ({ className }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
    </svg>
);

const DownloadIcon: React.FC<{ className?: string }> = ({ className }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
    </svg>
);

const UploadIcon: React.FC<{ className?: string }> = ({ className }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
    </svg>
);

const ScissorsIcon: React.FC<{ className?: string }> = ({ className }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.121 14.121L19 19m-7-7l7-7m-7 7l-2.879 2.879M12 12L9.121 9.121m0 5.758a3 3 0 10-4.243 4.243 3 3 0 004.243-4.243zm0-5.758a3 3 0 10-4.243-4.243 3 3 0 004.243 4.243z" />
    </svg>
);

interface AudioSuitePanelProps {
    videoFile?: File | Blob;
    onProcessed?: (blob: Blob) => void;
}

const AudioSuitePanel: React.FC<AudioSuitePanelProps> = ({ videoFile, onProcessed }) => {
    const [activeTab, setActiveTab] = useState<'normalize' | 'enhance' | 'music' | 'effects' | 'analysis'>('normalize');
    const [isProcessing, setIsProcessing] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [logs, setLogs] = useState<string[]>([]);
    const [processedBlob, setProcessedBlob] = useState<Blob | null>(null);

    // Normalization
    const [targetLUFS, setTargetLUFS] = useState(-14);
    const [loudnessStats, setLoudnessStats] = useState<LoudnessStats | null>(null);

    // Voice enhancement
    const [voiceEnhanceEnabled, setVoiceEnhanceEnabled] = useState(false);

    // Background music
    const [musicFile, setMusicFile] = useState<File | null>(null);
    const [duckLevel, setDuckLevel] = useState(-20);

    // Noise reduction
    const [noiseReductionEnabled, setNoiseReductionEnabled] = useState(false);
    const [noiseFloor, setNoiseFloor] = useState(-25);

    // Volume
    const [volumeLevel, setVolumeLevel] = useState(1.0);

    // Fade
    const [fadeInDuration, setFadeInDuration] = useState(0);
    const [fadeOutDuration, setFadeOutDuration] = useState(0);

    // Silence removal
    const [silenceThreshold, setSilenceThreshold] = useState(-30);
    const [minSilenceDuration, setMinSilenceDuration] = useState(0.5);
    const [silenceSegments, setSilenceSegments] = useState<SilenceSegment[]>([]);

    // Audio extraction/replacement
    const [extractFormat, setExtractFormat] = useState<'mp3' | 'wav'>('mp3');
    const [replacementAudio, setReplacementAudio] = useState<File | null>(null);

    // Waveform visualization
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const audioContextRef = useRef<AudioContext | null>(null);

    const audioProcessor = useRef(new AudioProcessor((log) => {
        setLogs(prev => [...prev.slice(-50), log]); // Keep last 50 logs
    }));

    const addLog = (message: string) => {
        setLogs(prev => [...prev.slice(-50), `[${new Date().toLocaleTimeString()}] ${message}`]);
    };

    const handleProcess = async () => {
        if (!videoFile) {
            setError('Please select a video file first');
            return;
        }

        setIsProcessing(true);
        setError(null);
        setLogs([]);

        try {
            let currentBlob = videoFile instanceof File ? videoFile : videoFile;

            // Apply operations in sequence
            if (activeTab === 'normalize') {
                addLog(`Normalizing to ${targetLUFS} LUFS...`);
                currentBlob = await audioProcessor.current.normalizeLoudness(currentBlob, targetLUFS);
            } else if (activeTab === 'enhance') {
                if (voiceEnhanceEnabled) {
                    addLog('Enhancing voice clarity...');
                    currentBlob = await audioProcessor.current.enhanceVoice(currentBlob);
                }
                if (noiseReductionEnabled) {
                    addLog('Removing background noise...');
                    currentBlob = await audioProcessor.current.removeBackground(currentBlob, noiseFloor);
                }
            } else if (activeTab === 'music' && musicFile) {
                addLog('Adding background music with ducking...');
                currentBlob = await audioProcessor.current.addBackgroundMusic(currentBlob, musicFile, duckLevel);
            } else if (activeTab === 'effects') {
                if (volumeLevel !== 1.0) {
                    addLog(`Adjusting volume to ${volumeLevel}x...`);
                    currentBlob = await audioProcessor.current.adjustVolume(currentBlob, volumeLevel);
                }
                if (fadeInDuration > 0 || fadeOutDuration > 0) {
                    addLog('Applying audio fades...');
                    currentBlob = await audioProcessor.current.fadeAudio(currentBlob, fadeInDuration, fadeOutDuration);
                }
            }

            setProcessedBlob(currentBlob);
            addLog('✓ Processing complete!');

            if (onProcessed) {
                onProcessed(currentBlob);
            }

            // Generate waveform
            if (canvasRef.current) {
                await drawWaveform(currentBlob);
            }
        } catch (err) {
            const errorMsg = err instanceof Error ? err.message : 'Processing failed';
            setError(errorMsg);
            addLog(`✗ Error: ${errorMsg}`);
        } finally {
            setIsProcessing(false);
        }
    };

    const handleAnalyzeLoudness = async () => {
        if (!videoFile) {
            setError('Please select a video file first');
            return;
        }

        setIsProcessing(true);
        setError(null);

        try {
            addLog('Analyzing loudness...');
            const stats = await audioProcessor.current.analyzeLoudness(videoFile);
            setLoudnessStats(stats);
            addLog('✓ Loudness analysis complete');
        } catch (err) {
            const errorMsg = err instanceof Error ? err.message : 'Analysis failed';
            setError(errorMsg);
        } finally {
            setIsProcessing(false);
        }
    };

    const handleDetectSilence = async () => {
        if (!videoFile) {
            setError('Please select a video file first');
            return;
        }

        setIsProcessing(true);
        setError(null);

        try {
            addLog('Detecting silence...');
            const segments = await audioProcessor.current.detectSilence(videoFile, silenceThreshold, minSilenceDuration);
            setSilenceSegments(segments);
            addLog(`✓ Found ${segments.length} silence segments`);
        } catch (err) {
            const errorMsg = err instanceof Error ? err.message : 'Detection failed';
            setError(errorMsg);
        } finally {
            setIsProcessing(false);
        }
    };

    const handleRemoveSilence = async () => {
        if (!videoFile) {
            setError('Please select a video file first');
            return;
        }

        setIsProcessing(true);
        setError(null);

        try {
            addLog('Removing silence...');
            const result = await audioProcessor.current.removeSilence(videoFile, silenceThreshold, minSilenceDuration);
            setProcessedBlob(result);
            addLog('✓ Silence removed successfully');

            if (onProcessed) {
                onProcessed(result);
            }
        } catch (err) {
            const errorMsg = err instanceof Error ? err.message : 'Silence removal failed';
            setError(errorMsg);
        } finally {
            setIsProcessing(false);
        }
    };

    const handleExtractAudio = async () => {
        if (!videoFile) {
            setError('Please select a video file first');
            return;
        }

        setIsProcessing(true);
        setError(null);

        try {
            addLog(`Extracting audio as ${extractFormat.toUpperCase()}...`);
            const audioBlob = await audioProcessor.current.extractAudio(videoFile, extractFormat);

            // Download the audio file
            const url = URL.createObjectURL(audioBlob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `extracted_audio.${extractFormat}`;
            a.click();
            URL.revokeObjectURL(url);

            addLog('✓ Audio extracted and downloaded');
        } catch (err) {
            const errorMsg = err instanceof Error ? err.message : 'Extraction failed';
            setError(errorMsg);
        } finally {
            setIsProcessing(false);
        }
    };

    const handleReplaceAudio = async () => {
        if (!videoFile || !replacementAudio) {
            setError('Please select both video and audio files');
            return;
        }

        setIsProcessing(true);
        setError(null);

        try {
            addLog('Replacing audio track...');
            const result = await audioProcessor.current.replaceAudio(videoFile, replacementAudio);
            setProcessedBlob(result);
            addLog('✓ Audio replaced successfully');

            if (onProcessed) {
                onProcessed(result);
            }
        } catch (err) {
            const errorMsg = err instanceof Error ? err.message : 'Audio replacement failed';
            setError(errorMsg);
        } finally {
            setIsProcessing(false);
        }
    };

    const drawWaveform = async (blob: Blob) => {
        if (!canvasRef.current) return;

        try {
            if (!audioContextRef.current) {
                audioContextRef.current = new AudioContext();
            }

            const arrayBuffer = await blob.arrayBuffer();
            const audioBuffer = await audioContextRef.current.decodeAudioData(arrayBuffer);

            const canvas = canvasRef.current;
            const ctx = canvas.getContext('2d');
            if (!ctx) return;

            const width = canvas.width;
            const height = canvas.height;
            const data = audioBuffer.getChannelData(0);
            const step = Math.ceil(data.length / width);
            const amp = height / 2;

            ctx.fillStyle = '#1a1a2e';
            ctx.fillRect(0, 0, width, height);

            ctx.strokeStyle = '#4ade80';
            ctx.lineWidth = 1;
            ctx.beginPath();

            for (let i = 0; i < width; i++) {
                let min = 1.0;
                let max = -1.0;

                for (let j = 0; j < step; j++) {
                    const datum = data[(i * step) + j];
                    if (datum < min) min = datum;
                    if (datum > max) max = datum;
                }

                const yMin = (1 + min) * amp;
                const yMax = (1 + max) * amp;

                if (i === 0) {
                    ctx.moveTo(i, yMin);
                } else {
                    ctx.lineTo(i, yMin);
                }
                ctx.lineTo(i, yMax);
            }

            ctx.stroke();
        } catch (err) {
            console.error('Waveform drawing failed:', err);
        }
    };

    const downloadProcessed = () => {
        if (!processedBlob) return;

        const url = URL.createObjectURL(processedBlob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'processed_video.mp4';
        a.click();
        URL.revokeObjectURL(url);
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold flex items-center gap-2">
                    <VolumeIcon className="w-6 h-6" />
                    Audio Processing Suite
                </h2>
                {processedBlob && (
                    <button
                        onClick={downloadProcessed}
                        className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg font-semibold"
                    >
                        <DownloadIcon className="w-5 h-5" />
                        Download
                    </button>
                )}
            </div>

            {/* Tab Navigation */}
            <div className="flex gap-2 p-1 bg-gray-900/50 rounded-lg border border-gray-700 overflow-x-auto">
                <button
                    onClick={() => setActiveTab('normalize')}
                    className={`px-4 py-2 rounded-md font-semibold whitespace-nowrap ${activeTab === 'normalize' ? 'bg-indigo-600' : 'hover:bg-gray-700'}`}
                >
                    Normalize
                </button>
                <button
                    onClick={() => setActiveTab('enhance')}
                    className={`px-4 py-2 rounded-md font-semibold whitespace-nowrap ${activeTab === 'enhance' ? 'bg-indigo-600' : 'hover:bg-gray-700'}`}
                >
                    Enhance
                </button>
                <button
                    onClick={() => setActiveTab('music')}
                    className={`px-4 py-2 rounded-md font-semibold whitespace-nowrap ${activeTab === 'music' ? 'bg-indigo-600' : 'hover:bg-gray-700'}`}
                >
                    Music
                </button>
                <button
                    onClick={() => setActiveTab('effects')}
                    className={`px-4 py-2 rounded-md font-semibold whitespace-nowrap ${activeTab === 'effects' ? 'bg-indigo-600' : 'hover:bg-gray-700'}`}
                >
                    Effects
                </button>
                <button
                    onClick={() => setActiveTab('analysis')}
                    className={`px-4 py-2 rounded-md font-semibold whitespace-nowrap ${activeTab === 'analysis' ? 'bg-indigo-600' : 'hover:bg-gray-700'}`}
                >
                    Analysis
                </button>
            </div>

            {/* Error Display */}
            {error && (
                <div className="p-4 bg-red-900/30 border border-red-500 rounded-lg text-red-400">
                    {error}
                </div>
            )}

            {/* Content Area */}
            <div className="bg-gray-800/50 p-6 rounded-lg border border-gray-700 space-y-6">
                {/* Normalize Tab */}
                {activeTab === 'normalize' && (
                    <div className="space-y-4">
                        <h3 className="text-lg font-bold flex items-center gap-2">
                            <SparklesIcon className="w-5 h-5" />
                            Loudness Normalization (EBU R128)
                        </h3>

                        <div>
                            <label className="block text-sm font-medium mb-2">
                                Target LUFS: {targetLUFS} dB
                            </label>
                            <input
                                type="range"
                                min="-23"
                                max="-9"
                                step="0.5"
                                value={targetLUFS}
                                onChange={(e) => setTargetLUFS(parseFloat(e.target.value))}
                                className="w-full"
                            />
                            <div className="flex justify-between text-xs text-gray-400 mt-1">
                                <span>Broadcast (-23)</span>
                                <span>Streaming (-14)</span>
                                <span>Loud (-9)</span>
                            </div>
                        </div>

                        {loudnessStats && (
                            <div className="p-4 bg-gray-900/50 rounded-lg border border-gray-600">
                                <h4 className="font-semibold mb-2">Current Loudness:</h4>
                                <div className="grid grid-cols-3 gap-4 text-sm">
                                    <div>
                                        <div className="text-gray-400">Integrated</div>
                                        <div className="text-xl font-bold text-green-400">
                                            {loudnessStats.integratedLoudness.toFixed(1)} LUFS
                                        </div>
                                    </div>
                                    <div>
                                        <div className="text-gray-400">Range</div>
                                        <div className="text-xl font-bold text-blue-400">
                                            {loudnessStats.loudnessRange.toFixed(1)} LU
                                        </div>
                                    </div>
                                    <div>
                                        <div className="text-gray-400">True Peak</div>
                                        <div className="text-xl font-bold text-yellow-400">
                                            {loudnessStats.truePeak.toFixed(1)} dBTP
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        <div className="flex gap-2">
                            <button
                                onClick={handleAnalyzeLoudness}
                                disabled={isProcessing || !videoFile}
                                className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white font-bold py-2 px-4 rounded-lg flex items-center justify-center gap-2"
                            >
                                {isProcessing ? <Spinner /> : <SparklesIcon className="w-5 h-5" />}
                                Analyze
                            </button>
                            <button
                                onClick={handleProcess}
                                disabled={isProcessing || !videoFile}
                                className="flex-1 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white font-bold py-2 px-4 rounded-lg flex items-center justify-center gap-2"
                            >
                                {isProcessing ? <Spinner /> : <SparklesIcon className="w-5 h-5" />}
                                Normalize
                            </button>
                        </div>
                    </div>
                )}

                {/* Enhance Tab */}
                {activeTab === 'enhance' && (
                    <div className="space-y-4">
                        <h3 className="text-lg font-bold flex items-center gap-2">
                            <MicIcon className="w-5 h-5" />
                            Voice Enhancement & Noise Reduction
                        </h3>

                        <div className="space-y-3">
                            <label className="flex items-center gap-3 p-3 bg-gray-900/50 rounded-lg cursor-pointer hover:bg-gray-900/70">
                                <input
                                    type="checkbox"
                                    checked={voiceEnhanceEnabled}
                                    onChange={(e) => setVoiceEnhanceEnabled(e.target.checked)}
                                    className="w-5 h-5"
                                />
                                <div>
                                    <div className="font-semibold">Voice Enhancement</div>
                                    <div className="text-sm text-gray-400">
                                        Highpass, lowpass, and EQ boost for clarity
                                    </div>
                                </div>
                            </label>

                            <label className="flex items-center gap-3 p-3 bg-gray-900/50 rounded-lg cursor-pointer hover:bg-gray-900/70">
                                <input
                                    type="checkbox"
                                    checked={noiseReductionEnabled}
                                    onChange={(e) => setNoiseReductionEnabled(e.target.checked)}
                                    className="w-5 h-5"
                                />
                                <div className="flex-1">
                                    <div className="font-semibold">Noise Reduction</div>
                                    <div className="text-sm text-gray-400">
                                        FFT denoiser for background noise removal
                                    </div>
                                </div>
                            </label>

                            {noiseReductionEnabled && (
                                <div className="ml-8">
                                    <label className="block text-sm font-medium mb-2">
                                        Noise Floor: {noiseFloor} dB
                                    </label>
                                    <input
                                        type="range"
                                        min="-60"
                                        max="-10"
                                        step="1"
                                        value={noiseFloor}
                                        onChange={(e) => setNoiseFloor(parseFloat(e.target.value))}
                                        className="w-full"
                                    />
                                </div>
                            )}
                        </div>

                        <button
                            onClick={handleProcess}
                            disabled={isProcessing || !videoFile || (!voiceEnhanceEnabled && !noiseReductionEnabled)}
                            className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white font-bold py-2 px-4 rounded-lg flex items-center justify-center gap-2"
                        >
                            {isProcessing ? <Spinner /> : <SparklesIcon className="w-5 h-5" />}
                            Apply Enhancement
                        </button>
                    </div>
                )}

                {/* Music Tab */}
                {activeTab === 'music' && (
                    <div className="space-y-4">
                        <h3 className="text-lg font-bold flex items-center gap-2">
                            <MusicIcon className="w-5 h-5" />
                            Background Music with Ducking
                        </h3>

                        <div>
                            <label className="block text-sm font-medium mb-2">
                                Upload Background Music
                            </label>
                            <input
                                type="file"
                                accept="audio/*"
                                onChange={(e) => setMusicFile(e.target.files?.[0] || null)}
                                className="w-full p-2 bg-gray-900/70 border border-gray-600 rounded-lg"
                            />
                            {musicFile && (
                                <p className="text-sm text-green-400 mt-2">
                                    ✓ {musicFile.name}
                                </p>
                            )}
                        </div>

                        <div>
                            <label className="block text-sm font-medium mb-2">
                                Duck Level: {duckLevel} dB
                            </label>
                            <input
                                type="range"
                                min="-30"
                                max="-10"
                                step="1"
                                value={duckLevel}
                                onChange={(e) => setDuckLevel(parseFloat(e.target.value))}
                                className="w-full"
                            />
                            <p className="text-xs text-gray-400 mt-1">
                                Sidechain compression: music ducks when voice is present
                            </p>
                        </div>

                        <button
                            onClick={handleProcess}
                            disabled={isProcessing || !videoFile || !musicFile}
                            className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white font-bold py-2 px-4 rounded-lg flex items-center justify-center gap-2"
                        >
                            {isProcessing ? <Spinner /> : <MusicIcon className="w-5 h-5" />}
                            Add Music
                        </button>
                    </div>
                )}

                {/* Effects Tab */}
                {activeTab === 'effects' && (
                    <div className="space-y-4">
                        <h3 className="text-lg font-bold">Audio Effects</h3>

                        <div>
                            <label className="block text-sm font-medium mb-2">
                                Volume: {volumeLevel.toFixed(2)}x
                            </label>
                            <input
                                type="range"
                                min="0"
                                max="3"
                                step="0.1"
                                value={volumeLevel}
                                onChange={(e) => setVolumeLevel(parseFloat(e.target.value))}
                                className="w-full"
                            />
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium mb-2">
                                    Fade In: {fadeInDuration}s
                                </label>
                                <input
                                    type="range"
                                    min="0"
                                    max="5"
                                    step="0.5"
                                    value={fadeInDuration}
                                    onChange={(e) => setFadeInDuration(parseFloat(e.target.value))}
                                    className="w-full"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium mb-2">
                                    Fade Out: {fadeOutDuration}s
                                </label>
                                <input
                                    type="range"
                                    min="0"
                                    max="5"
                                    step="0.5"
                                    value={fadeOutDuration}
                                    onChange={(e) => setFadeOutDuration(parseFloat(e.target.value))}
                                    className="w-full"
                                />
                            </div>
                        </div>

                        <button
                            onClick={handleProcess}
                            disabled={isProcessing || !videoFile}
                            className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white font-bold py-2 px-4 rounded-lg flex items-center justify-center gap-2"
                        >
                            {isProcessing ? <Spinner /> : <SparklesIcon className="w-5 h-5" />}
                            Apply Effects
                        </button>
                    </div>
                )}

                {/* Analysis Tab */}
                {activeTab === 'analysis' && (
                    <div className="space-y-4">
                        <h3 className="text-lg font-bold">Audio Analysis & Tools</h3>

                        {/* Silence Detection */}
                        <div className="p-4 bg-gray-900/50 rounded-lg border border-gray-600 space-y-3">
                            <h4 className="font-semibold flex items-center gap-2">
                                <ScissorsIcon className="w-5 h-5" />
                                Silence Removal
                            </h4>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium mb-2">
                                        Threshold: {silenceThreshold} dB
                                    </label>
                                    <input
                                        type="range"
                                        min="-60"
                                        max="-10"
                                        step="1"
                                        value={silenceThreshold}
                                        onChange={(e) => setSilenceThreshold(parseFloat(e.target.value))}
                                        className="w-full"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium mb-2">
                                        Min Duration: {minSilenceDuration}s
                                    </label>
                                    <input
                                        type="range"
                                        min="0.1"
                                        max="2"
                                        step="0.1"
                                        value={minSilenceDuration}
                                        onChange={(e) => setMinSilenceDuration(parseFloat(e.target.value))}
                                        className="w-full"
                                    />
                                </div>
                            </div>

                            {silenceSegments.length > 0 && (
                                <div className="p-3 bg-gray-800 rounded-lg">
                                    <p className="text-sm font-semibold mb-2">
                                        Found {silenceSegments.length} silence segments:
                                    </p>
                                    <div className="max-h-40 overflow-y-auto space-y-1 text-xs">
                                        {silenceSegments.slice(0, 10).map((seg, i) => (
                                            <div key={i} className="text-gray-400">
                                                {seg.start.toFixed(2)}s - {seg.end.toFixed(2)}s ({seg.duration.toFixed(2)}s)
                                            </div>
                                        ))}
                                        {silenceSegments.length > 10 && (
                                            <div className="text-gray-500">
                                                ... and {silenceSegments.length - 10} more
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}

                            <div className="flex gap-2">
                                <button
                                    onClick={handleDetectSilence}
                                    disabled={isProcessing || !videoFile}
                                    className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white font-bold py-2 px-4 rounded-lg"
                                >
                                    Detect
                                </button>
                                <button
                                    onClick={handleRemoveSilence}
                                    disabled={isProcessing || !videoFile}
                                    className="flex-1 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white font-bold py-2 px-4 rounded-lg"
                                >
                                    Remove
                                </button>
                            </div>
                        </div>

                        {/* Audio Extraction */}
                        <div className="p-4 bg-gray-900/50 rounded-lg border border-gray-600 space-y-3">
                            <h4 className="font-semibold flex items-center gap-2">
                                <DownloadIcon className="w-5 h-5" />
                                Extract Audio
                            </h4>

                            <div className="flex items-center gap-4">
                                <label className="flex items-center gap-2">
                                    <input
                                        type="radio"
                                        value="mp3"
                                        checked={extractFormat === 'mp3'}
                                        onChange={() => setExtractFormat('mp3')}
                                    />
                                    MP3
                                </label>
                                <label className="flex items-center gap-2">
                                    <input
                                        type="radio"
                                        value="wav"
                                        checked={extractFormat === 'wav'}
                                        onChange={() => setExtractFormat('wav')}
                                    />
                                    WAV
                                </label>
                            </div>

                            <button
                                onClick={handleExtractAudio}
                                disabled={isProcessing || !videoFile}
                                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white font-bold py-2 px-4 rounded-lg flex items-center justify-center gap-2"
                            >
                                {isProcessing ? <Spinner /> : <DownloadIcon className="w-5 h-5" />}
                                Extract & Download
                            </button>
                        </div>

                        {/* Audio Replacement */}
                        <div className="p-4 bg-gray-900/50 rounded-lg border border-gray-600 space-y-3">
                            <h4 className="font-semibold flex items-center gap-2">
                                <UploadIcon className="w-5 h-5" />
                                Replace Audio
                            </h4>

                            <input
                                type="file"
                                accept="audio/*"
                                onChange={(e) => setReplacementAudio(e.target.files?.[0] || null)}
                                className="w-full p-2 bg-gray-900/70 border border-gray-600 rounded-lg text-sm"
                            />

                            {replacementAudio && (
                                <p className="text-sm text-green-400">
                                    ✓ {replacementAudio.name}
                                </p>
                            )}

                            <button
                                onClick={handleReplaceAudio}
                                disabled={isProcessing || !videoFile || !replacementAudio}
                                className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white font-bold py-2 px-4 rounded-lg flex items-center justify-center gap-2"
                            >
                                {isProcessing ? <Spinner /> : <UploadIcon className="w-5 h-5" />}
                                Replace Audio
                            </button>
                        </div>
                    </div>
                )}
            </div>

            {/* Waveform Visualization */}
            {processedBlob && (
                <div className="bg-gray-800/50 p-4 rounded-lg border border-gray-700">
                    <h4 className="text-sm font-semibold mb-2">Audio Waveform Preview</h4>
                    <canvas
                        ref={canvasRef}
                        width={800}
                        height={120}
                        className="w-full h-auto rounded-lg bg-gray-900"
                    />
                </div>
            )}

            {/* Processing Logs */}
            {logs.length > 0 && (
                <div className="bg-gray-900/50 p-4 rounded-lg border border-gray-700">
                    <h4 className="text-sm font-semibold mb-2">Processing Log</h4>
                    <div className="max-h-40 overflow-y-auto font-mono text-xs text-gray-400 space-y-1">
                        {logs.map((log, i) => (
                            <div key={i}>{log}</div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

export default AudioSuitePanel;
