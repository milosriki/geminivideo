import { AdvancedEdit } from '../types';

// Make FFmpeg types available globally
declare global {
    interface Window {
        FFmpeg: any;
    }
}

type QualityLevel = 'low' | 'medium' | 'high';

interface QualityPreset {
    resolution: string;
    fps: number;
    crf: number; // Constant Rate Factor (lower = better quality)
    preset: string; // FFmpeg encoding preset
}

const QUALITY_PRESETS: Record<QualityLevel, QualityPreset> = {
    low: {
        resolution: '854x480', // 480p
        fps: 15,
        crf: 28,
        preset: 'ultrafast',
    },
    medium: {
        resolution: '1280x720', // 720p
        fps: 24,
        crf: 23,
        preset: 'fast',
    },
    high: {
        resolution: '1920x1080', // 1080p
        fps: 30,
        crf: 18,
        preset: 'medium',
    },
};

class RealtimePreview {
    private ffmpeg: any = null;
    private previewDuration: number = 3; // Default 3 seconds
    private quality: QualityLevel = 'low'; // Default to fast preview
    private isFontLoaded: boolean = false;
    private abortController: AbortController | null = null;
    private generatedUrls: Set<string> = new Set(); // Track URLs for cleanup

    /**
     * Load FFmpeg instance (singleton pattern)
     */
    private async loadFFmpeg(): Promise<any> {
        if (this.ffmpeg) {
            return this.ffmpeg;
        }

        const { FFmpeg } = window.FFmpeg;
        const coreURL = "https://unpkg.com/@ffmpeg/core@0.12.6/dist/umd/ffmpeg-core.js";

        const instance = new FFmpeg();
        instance.on('log', ({ message }: { message: string }) => {
            // console.log('[RealtimePreview FFmpeg]:', message);
        });

        await instance.load({ coreURL });
        this.ffmpeg = instance;
        return this.ffmpeg;
    }

    /**
     * Ensure font is loaded for text overlays
     */
    private async ensureFontIsLoaded(): Promise<void> {
        if (this.isFontLoaded || !this.ffmpeg) return;

        try {
            // console.log('[RealtimePreview] Loading custom font...');
            const fontResponse = await fetch('https://fonts.gstatic.com/s/roboto/v20/KFOmCnqEu92Fr1Mu4mxK.woff2');
            const fontBlob = await fontResponse.arrayBuffer();
            await this.ffmpeg.writeFile('/fonts/Roboto-Regular.ttf', new Uint8Array(fontBlob));
            this.isFontLoaded = true;
            // console.log('[RealtimePreview] Custom font loaded.');
        } catch (e) {
            console.error('[RealtimePreview] Failed to load custom font.', e);
        }
    }

    /**
     * Convert File to Uint8Array
     */
    private async fileToUint8Array(file: File): Promise<Uint8Array> {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => {
                if (reader.result instanceof ArrayBuffer) {
                    resolve(new Uint8Array(reader.result));
                } else {
                    reject(new Error("Failed to read file as ArrayBuffer."));
                }
            };
            reader.onerror = reject;
            reader.readAsArrayBuffer(file);
        });
    }

    /**
     * Build FFmpeg filter complex from edits
     */
    private buildFilterComplex(edits: AdvancedEdit[], videoDuration: number): {
        filterComplexParts: string[];
        lastVideoStream: string;
        lastAudioStream: string;
        imageInputs: { edit: Extract<AdvancedEdit, { type: 'image' }>; index: number }[];
    } {
        const filterComplexParts: string[] = [];
        let lastVideoStream = '[0:v]';
        let lastAudioStream = '[0:a]';
        const imageInputs: { edit: Extract<AdvancedEdit, { type: 'image' }>; index: number }[] = [];
        let imageInputIndex = 1;

        for (const edit of edits) {
            const stepIndex = filterComplexParts.length;
            const newVideoStream = `[v${stepIndex}]`;
            const newAudioStream = `[a${stepIndex}]`;

            switch (edit.type) {
                case 'filter': {
                    let filterName = '';
                    if (edit.name === 'grayscale') filterName = 'format=gray';
                    else if (edit.name === 'sepia') filterName = 'colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131';
                    else if (edit.name === 'negate') filterName = 'negate';
                    else if (edit.name === 'vignette') filterName = 'vignette';
                    if (filterName) {
                        filterComplexParts.push(`${lastVideoStream}${filterName}${newVideoStream}`);
                        lastVideoStream = newVideoStream;
                    }
                    break;
                }
                case 'color': {
                    const eqFilter = `eq=brightness=${edit.brightness}:contrast=${edit.contrast}:saturation=${edit.saturation}`;
                    filterComplexParts.push(`${lastVideoStream}${eqFilter}${newVideoStream}`);
                    lastVideoStream = newVideoStream;
                    break;
                }
                case 'volume': {
                    filterComplexParts.push(`${lastAudioStream}volume=${edit.level}${newAudioStream}`);
                    lastAudioStream = newAudioStream;
                    break;
                }
                case 'fade': {
                    const fadeDuration = edit.duration;
                    let videoFilters = [];
                    let audioFilters = [];

                    if (edit.typeIn) {
                        videoFilters.push(`fade=t=in:st=0:d=${fadeDuration}`);
                        audioFilters.push(`afade=t=in:st=0:d=${fadeDuration}`);
                    }
                    if (edit.typeOut && videoDuration > 0) {
                        const startTime = Math.max(0, videoDuration - fadeDuration);
                        videoFilters.push(`fade=t=out:st=${startTime}:d=${fadeDuration}`);
                        audioFilters.push(`afade=t=out:st=${startTime}:d=${fadeDuration}`);
                    }

                    if (videoFilters.length > 0) {
                        filterComplexParts.push(`${lastVideoStream}${videoFilters.join(',')}${newVideoStream}`);
                        lastVideoStream = newVideoStream;
                    }
                    if (audioFilters.length > 0) {
                        filterComplexParts.push(`${lastAudioStream}${audioFilters.join(',')}${newAudioStream}`);
                        lastAudioStream = newAudioStream;
                    }
                    break;
                }
                case 'crop': {
                    let cropFilter = '';
                    switch (edit.ratio) {
                        case '9:16': cropFilter = 'crop=ih*9/16:ih:(iw-ow)/2:0'; break;
                        case '1:1': cropFilter = 'crop=ih:ih:(iw-ow)/2:0'; break;
                        case '4:5': cropFilter = 'crop=ih*4/5:ih:(iw-ow)/2:0'; break;
                        case '16:9': default: cropFilter = 'crop=iw:iw*9/16:0:(ih-oh)/2'; break;
                    }
                    if (cropFilter) {
                        filterComplexParts.push(`${lastVideoStream}${cropFilter}${newVideoStream}`);
                        lastVideoStream = newVideoStream;
                    }
                    break;
                }
                case 'subtitles': {
                    const fontPath = this.isFontLoaded ? `/fonts/Roboto-Regular.ttf` : 'sans-serif';
                    const safeText = edit.text.replace(/'/g, "'\\''").replace(/:/g, '\\:').replace(/%/g, '\\%');
                    const subtitleFilter = `drawtext=fontfile='${fontPath}':text='${safeText}':fontcolor=white:fontsize=24:box=1:boxcolor=black@0.6:x=(w-text_w)/2:y=h-50`;
                    filterComplexParts.push(`${lastVideoStream}${subtitleFilter}${newVideoStream}`);
                    lastVideoStream = newVideoStream;
                    break;
                }
                case 'speed': {
                    filterComplexParts.push(`${lastVideoStream}setpts=${1 / edit.factor}*PTS${newVideoStream}`);
                    lastVideoStream = newVideoStream;

                    if (edit.factor > 0) {
                        const atempoFilters = [];
                        let currentFactor = edit.factor;
                        while (currentFactor < 0.5) {
                            atempoFilters.push('atempo=0.5');
                            currentFactor /= 0.5;
                        }
                        while (currentFactor > 2.0) {
                            atempoFilters.push('atempo=2.0');
                            currentFactor /= 2.0;
                        }
                        if (currentFactor >= 0.5 && currentFactor <= 2.0) {
                            atempoFilters.push(`atempo=${currentFactor}`);
                        }

                        const audioFilter = atempoFilters.join(',');
                        filterComplexParts.push(`${lastAudioStream}${audioFilter}${newAudioStream}`);
                        lastAudioStream = newAudioStream;
                    }
                    break;
                }
                case 'text': {
                    const safeText = edit.text.replace(/'/g, "'\\''").replace(/:/g, '\\:').replace(/%/g, '\\%');
                    const yPos = edit.position === 'top' ? '20' : edit.position === 'center' ? '(h-text_h)/2' : `(h-text_h-20)`;
                    const fontPath = this.isFontLoaded ? `/fonts/Roboto-Regular.ttf` : 'sans-serif';
                    const drawtextFilter = `drawtext=fontfile='${fontPath}':text='${safeText}':fontcolor=white:fontsize=${edit.fontSize}:box=1:boxcolor=black@0.5:boxborderw=10:x=(w-text_w)/2:y=${yPos}:enable='between(t,${edit.start},${edit.end})'`;
                    filterComplexParts.push(`${lastVideoStream}${drawtextFilter}${newVideoStream}`);
                    lastVideoStream = newVideoStream;
                    break;
                }
                case 'image': {
                    imageInputs.push({ edit, index: imageInputIndex });
                    const imgStream = `[${imageInputIndex++}:v]`;
                    const scaledImgStream = `[scaled_img_${stepIndex}]`;
                    const overlayedStream = `[overlayed_${stepIndex}]`;

                    let pos = '10:10'; // top_left
                    if (edit.position === 'top_right') pos = 'W-w-10:10';
                    if (edit.position === 'bottom_left') pos = '10:H-h-10';
                    if (edit.position === 'bottom_right') pos = 'W-w-10:H-h-10';

                    filterComplexParts.push(`${imgStream}format=rgba,colorchannelmixer=aa=${edit.opacity},scale=iw*${edit.scale}:-1${scaledImgStream}`);
                    filterComplexParts.push(`${lastVideoStream}${scaledImgStream}overlay=${pos}${overlayedStream}`);
                    lastVideoStream = overlayedStream;
                    break;
                }
                case 'mute': {
                    filterComplexParts.push(`${lastAudioStream}volume=0${newAudioStream}`);
                    lastAudioStream = newAudioStream;
                    break;
                }
                case 'trim':
                    // Trim is handled at input/output level, not in filter
                    break;
            }
        }

        return { filterComplexParts, lastVideoStream, lastAudioStream, imageInputs };
    }

    /**
     * Generate a real-time preview with all edits applied
     */
    async generatePreview(sourceVideo: File, edits: AdvancedEdit[]): Promise<string> {
        // Create new abort controller for this preview
        this.abortController = new AbortController();

        try {
            const ffmpegInstance = await this.loadFFmpeg();
            await this.ensureFontIsLoaded();

            // Write source video to FFmpeg filesystem
            const videoData = await this.fileToUint8Array(sourceVideo);
            await ffmpegInstance.writeFile('preview_input.mp4', videoData);

            // Get video duration (use probe)
            let videoDuration = this.previewDuration; // Fallback to preview duration
            const logCallback = ({ message }: { message: string }) => {
                const match = message.match(/Duration: (\d{2}):(\d{2}):(\d{2}\.\d{2})/);
                if (match) {
                    const [_, h, m, s] = match;
                    videoDuration = parseFloat(h) * 3600 + parseFloat(m) * 60 + parseFloat(s);
                }
            };
            ffmpegInstance.on('log', logCallback);
            await ffmpegInstance.exec(['-i', 'preview_input.mp4']);
            ffmpegInstance.off('log', logCallback);

            // Build command
            const command: string[] = [];
            const preset = QUALITY_PRESETS[this.quality];
            const trimEdit = edits.find(e => e.type === 'trim') as Extract<AdvancedEdit, { type: 'trim' }> | undefined;

            // Apply trim at input if specified
            if (trimEdit) {
                command.push('-ss', trimEdit.start);
            }

            command.push('-i', 'preview_input.mp4');

            // Limit duration for preview
            const endTime = trimEdit
                ? Math.min(parseFloat(trimEdit.start) + this.previewDuration, parseFloat(trimEdit.end))
                : this.previewDuration;
            command.push('-t', String(this.previewDuration));

            // Handle image overlays - write them to FFmpeg filesystem
            const { filterComplexParts, lastVideoStream, lastAudioStream, imageInputs } =
                this.buildFilterComplex(edits, Math.min(videoDuration, this.previewDuration));

            for (const { edit, index } of imageInputs) {
                const imageData = await this.fileToUint8Array(edit.file);
                const imageFileName = `preview_overlay_${index}.png`;
                await ffmpegInstance.writeFile(imageFileName, imageData);
                command.push('-i', imageFileName);
            }

            // Add quality settings and filters
            if (filterComplexParts.length > 0) {
                command.push('-filter_complex', filterComplexParts.join(';'));
                command.push('-map', lastVideoStream);
                command.push('-map', lastAudioStream);
            }

            // Apply quality preset
            command.push(
                '-vf', `scale=${preset.resolution}:force_original_aspect_ratio=decrease,fps=${preset.fps}`,
                '-c:v', 'libx264',
                '-preset', preset.preset,
                '-crf', String(preset.crf),
                '-c:a', 'aac',
                '-b:a', '128k',
                '-movflags', '+faststart', // Enable streaming
                '-y', 'preview_output.mp4'
            );

            // console.log('[RealtimePreview] Executing FFmpeg command:', command);

            // Check if aborted before executing
            if (this.abortController?.signal.aborted) {
                throw new Error('Preview generation cancelled');
            }

            await ffmpegInstance.exec(command);

            // Check if aborted after executing
            if (this.abortController?.signal.aborted) {
                throw new Error('Preview generation cancelled');
            }

            // Read output
            const outputData = await ffmpegInstance.readFile('preview_output.mp4');
            const blob = new Blob([(outputData as Uint8Array).buffer as ArrayBuffer], { type: 'video/mp4' });
            const url = URL.createObjectURL(blob);

            // Track URL for cleanup
            this.generatedUrls.add(url);

            // Cleanup FFmpeg filesystem
            await ffmpegInstance.deleteFile('preview_input.mp4');
            await ffmpegInstance.deleteFile('preview_output.mp4');
            for (const { index } of imageInputs) {
                try {
                    await ffmpegInstance.deleteFile(`preview_overlay_${index}.png`);
                } catch (e) {
                    console.warn(`Failed to delete overlay ${index}`, e);
                }
            }

            return url;
        } catch (error) {
            console.error('[RealtimePreview] Error generating preview:', error);
            throw error;
        } finally {
            this.abortController = null;
        }
    }

    /**
     * Generate a preview for a single edit (for quick testing)
     */
    async generateEditPreview(sourceVideo: File, edit: AdvancedEdit): Promise<string> {
        return this.generatePreview(sourceVideo, [edit]);
    }

    /**
     * Set preview duration in seconds
     */
    setPreviewDuration(seconds: number): void {
        this.previewDuration = Math.max(1, Math.min(5, seconds)); // Clamp between 1-5 seconds
    }

    /**
     * Set quality level for preview
     */
    setQuality(quality: QualityLevel): void {
        this.quality = quality;
    }

    /**
     * Cancel ongoing preview generation
     */
    cancelPreview(): void {
        if (this.abortController) {
            this.abortController.abort();
        }
    }

    /**
     * Cleanup all generated blob URLs to prevent memory leaks
     */
    cleanup(): void {
        for (const url of this.generatedUrls) {
            URL.revokeObjectURL(url);
        }
        this.generatedUrls.clear();
    }

    /**
     * Get current quality setting
     */
    getQuality(): QualityLevel {
        return this.quality;
    }

    /**
     * Get current preview duration
     */
    getPreviewDuration(): number {
        return this.previewDuration;
    }
}

// Export singleton instance
export const realtimePreview = new RealtimePreview();
export default realtimePreview;
