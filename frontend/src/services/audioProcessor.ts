/**
 * AudioProcessor Service
 * Professional-grade audio processing using FFmpeg.wasm
 * Implements EBU R128 loudness normalization, voice enhancement, ducking, noise reduction, and more
 */

// Make FFmpeg types available globally
declare global {
    interface Window {
        FFmpeg: any;
    }
}

let ffmpeg: any;

// Singleton FFmpeg loader
const loadFFmpeg = async (onLog?: (log: string) => void): Promise<any> => {
    if (ffmpeg) {
        return ffmpeg;
    }

    const { FFmpeg } = window.FFmpeg;
    const coreURL = "https://unpkg.com/@ffmpeg/core@0.12.6/dist/umd/ffmpeg-core.js";

    const instance = new FFmpeg();

    if (onLog) {
        instance.on('log', ({ message }: { message: string }) => {
            onLog(message);
        });
    }

    await instance.load({ coreURL });
    ffmpeg = instance;
    return ffmpeg;
};

// Helper to convert Blob to Uint8Array
const blobToUint8Array = (blob: Blob): Promise<Uint8Array> => {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
            if (reader.result instanceof ArrayBuffer) {
                resolve(new Uint8Array(reader.result));
            } else {
                reject(new Error("Failed to read blob as ArrayBuffer."));
            }
        };
        reader.onerror = reject;
        reader.readAsArrayBuffer(blob);
    });
};

// Types
export interface AudioTrack {
    blob: Blob;
    volume: number; // 0.0 to 1.0
    delay?: number; // seconds
}

export interface SilenceSegment {
    start: number;
    end: number;
    duration: number;
}

export interface LoudnessStats {
    integratedLoudness: number; // LUFS
    loudnessRange: number; // LU
    truePeak: number; // dBTP
}

/**
 * AudioProcessor Class
 * Handles all audio processing operations for video files
 */
export class AudioProcessor {
    private onLog?: (log: string) => void;

    constructor(onLog?: (log: string) => void) {
        this.onLog = onLog;
    }

    private log(message: string) {
        if (this.onLog) {
            this.onLog(message);
        }
    }

    /**
     * Normalize loudness using EBU R128 standard
     * @param videoBlob - Input video blob
     * @param targetLUFS - Target loudness in LUFS (default: -14 for streaming)
     * @returns Normalized video blob
     */
    async normalizeLoudness(videoBlob: Blob, targetLUFS: number = -14): Promise<Blob> {
        this.log('Starting loudness normalization...');
        const ffmpegInstance = await loadFFmpeg(this.onLog);

        const videoData = await blobToUint8Array(videoBlob);
        await ffmpegInstance.writeFile('input.mp4', videoData);

        // EBU R128 loudness normalization
        // I = integrated loudness target
        // TP = true peak limit
        // LRA = loudness range target
        const loudnormFilter = `loudnorm=I=${targetLUFS}:TP=-1:LRA=7`;

        await ffmpegInstance.exec([
            '-i', 'input.mp4',
            '-af', loudnormFilter,
            '-c:v', 'copy', // Copy video stream without re-encoding
            '-c:a', 'aac',
            '-b:a', '192k',
            '-y', 'output.mp4'
        ]);

        const outputData = await ffmpegInstance.readFile('output.mp4');
        await ffmpegInstance.deleteFile('input.mp4');
        await ffmpegInstance.deleteFile('output.mp4');

        this.log('Loudness normalization complete');
        return new Blob([outputData.buffer], { type: 'video/mp4' });
    }

    /**
     * Enhance voice clarity with highpass, lowpass, and EQ
     * @param videoBlob - Input video blob
     * @returns Enhanced video blob
     */
    async enhanceVoice(videoBlob: Blob): Promise<Blob> {
        this.log('Starting voice enhancement...');
        const ffmpegInstance = await loadFFmpeg(this.onLog);

        const videoData = await blobToUint8Array(videoBlob);
        await ffmpegInstance.writeFile('input.mp4', videoData);

        // Voice enhancement chain:
        // 1. Highpass at 80Hz to remove rumble
        // 2. Lowpass at 8000Hz to remove high-frequency noise
        // 3. EQ boost at 300Hz (body) with 200Hz width
        // 4. EQ boost at 3000Hz (clarity) with 500Hz width
        const voiceFilter = 'highpass=f=80,lowpass=f=8000,equalizer=f=300:width_type=h:width=200:g=3,equalizer=f=3000:width_type=h:width=500:g=2';

        await ffmpegInstance.exec([
            '-i', 'input.mp4',
            '-af', voiceFilter,
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-y', 'output.mp4'
        ]);

        const outputData = await ffmpegInstance.readFile('output.mp4');
        await ffmpegInstance.deleteFile('input.mp4');
        await ffmpegInstance.deleteFile('output.mp4');

        this.log('Voice enhancement complete');
        return new Blob([outputData.buffer], { type: 'video/mp4' });
    }

    /**
     * Add background music with ducking (sidechain compression)
     * @param videoBlob - Input video blob
     * @param musicBlob - Background music blob
     * @param duckLevel - Ducking amount in dB (default: -20)
     * @returns Video with ducked background music
     */
    async addBackgroundMusic(videoBlob: Blob, musicBlob: Blob, duckLevel: number = -20): Promise<Blob> {
        this.log('Adding background music with ducking...');
        const ffmpegInstance = await loadFFmpeg(this.onLog);

        const videoData = await blobToUint8Array(videoBlob);
        const musicData = await blobToUint8Array(musicBlob);

        await ffmpegInstance.writeFile('input.mp4', videoData);
        await ffmpegInstance.writeFile('music.mp3', musicData);

        // Complex filter for ducking:
        // 1. [1:a] = music track
        // 2. [0:a] = original voice
        // 3. sidechaincompress uses voice to duck music
        // 4. amix combines both tracks
        const filterComplex = `
            [1:a]volume=0.3[music];
            [music][0:a]sidechaincompress=threshold=0.05:ratio=4:attack=50:release=1000[ducked];
            [0:a][ducked]amix=inputs=2:duration=first:dropout_transition=2[a]
        `.replace(/\n/g, '').replace(/\s+/g, '');

        await ffmpegInstance.exec([
            '-i', 'input.mp4',
            '-i', 'music.mp3',
            '-filter_complex', filterComplex,
            '-map', '0:v',
            '-map', '[a]',
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-shortest',
            '-y', 'output.mp4'
        ]);

        const outputData = await ffmpegInstance.readFile('output.mp4');
        await ffmpegInstance.deleteFile('input.mp4');
        await ffmpegInstance.deleteFile('music.mp3');
        await ffmpegInstance.deleteFile('output.mp4');

        this.log('Background music added with ducking');
        return new Blob([outputData.buffer], { type: 'video/mp4' });
    }

    /**
     * Remove background noise using FFT denoiser
     * @param videoBlob - Input video blob
     * @param noiseFloor - Noise floor in dB (default: -25)
     * @returns Denoised video blob
     */
    async removeBackground(videoBlob: Blob, noiseFloor: number = -25): Promise<Blob> {
        this.log('Removing background noise...');
        const ffmpegInstance = await loadFFmpeg(this.onLog);

        const videoData = await blobToUint8Array(videoBlob);
        await ffmpegInstance.writeFile('input.mp4', videoData);

        // FFT denoiser with noise floor
        const denoiseFilter = `afftdn=nf=${noiseFloor}`;

        await ffmpegInstance.exec([
            '-i', 'input.mp4',
            '-af', denoiseFilter,
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-y', 'output.mp4'
        ]);

        const outputData = await ffmpegInstance.readFile('output.mp4');
        await ffmpegInstance.deleteFile('input.mp4');
        await ffmpegInstance.deleteFile('output.mp4');

        this.log('Background noise removed');
        return new Blob([outputData.buffer], { type: 'video/mp4' });
    }

    /**
     * Adjust overall volume
     * @param videoBlob - Input video blob
     * @param level - Volume level (1.0 = no change, 2.0 = double, 0.5 = half)
     * @returns Volume-adjusted video blob
     */
    async adjustVolume(videoBlob: Blob, level: number = 1.0): Promise<Blob> {
        this.log(`Adjusting volume to ${level}x...`);
        const ffmpegInstance = await loadFFmpeg(this.onLog);

        const videoData = await blobToUint8Array(videoBlob);
        await ffmpegInstance.writeFile('input.mp4', videoData);

        await ffmpegInstance.exec([
            '-i', 'input.mp4',
            '-af', `volume=${level}`,
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-y', 'output.mp4'
        ]);

        const outputData = await ffmpegInstance.readFile('output.mp4');
        await ffmpegInstance.deleteFile('input.mp4');
        await ffmpegInstance.deleteFile('output.mp4');

        this.log('Volume adjustment complete');
        return new Blob([outputData.buffer], { type: 'video/mp4' });
    }

    /**
     * Add fade in/out to audio
     * @param videoBlob - Input video blob
     * @param fadeIn - Fade in duration in seconds
     * @param fadeOut - Fade out duration in seconds
     * @returns Faded video blob
     */
    async fadeAudio(videoBlob: Blob, fadeIn: number = 0, fadeOut: number = 0): Promise<Blob> {
        this.log('Adding audio fades...');
        const ffmpegInstance = await loadFFmpeg(this.onLog);

        const videoData = await blobToUint8Array(videoBlob);
        await ffmpegInstance.writeFile('input.mp4', videoData);

        // Get video duration first
        let duration = 0;
        const logCallback = ({ message }: { message: string }) => {
            const match = message.match(/Duration: (\d{2}):(\d{2}):(\d{2}\.\d{2})/);
            if (match) {
                const [_, h, m, s] = match;
                duration = parseFloat(h) * 3600 + parseFloat(m) * 60 + parseFloat(s);
            }
        };
        ffmpegInstance.on('log', logCallback);
        await ffmpegInstance.exec(['-i', 'input.mp4']);
        ffmpegInstance.off('log', logCallback);

        const filters = [];
        if (fadeIn > 0) {
            filters.push(`afade=t=in:st=0:d=${fadeIn}`);
        }
        if (fadeOut > 0 && duration > 0) {
            const fadeStart = Math.max(0, duration - fadeOut);
            filters.push(`afade=t=out:st=${fadeStart}:d=${fadeOut}`);
        }

        if (filters.length === 0) {
            this.log('No fades applied');
            return videoBlob;
        }

        await ffmpegInstance.exec([
            '-i', 'input.mp4',
            '-af', filters.join(','),
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-y', 'output.mp4'
        ]);

        const outputData = await ffmpegInstance.readFile('output.mp4');
        await ffmpegInstance.deleteFile('input.mp4');
        await ffmpegInstance.deleteFile('output.mp4');

        this.log('Audio fades applied');
        return new Blob([outputData.buffer], { type: 'video/mp4' });
    }

    /**
     * Extract audio from video
     * @param videoBlob - Input video blob
     * @param format - Output format ('wav' or 'mp3')
     * @returns Audio blob
     */
    async extractAudio(videoBlob: Blob, format: 'wav' | 'mp3' = 'mp3'): Promise<Blob> {
        this.log(`Extracting audio as ${format.toUpperCase()}...`);
        const ffmpegInstance = await loadFFmpeg(this.onLog);

        const videoData = await blobToUint8Array(videoBlob);
        await ffmpegInstance.writeFile('input.mp4', videoData);

        const outputFile = `output.${format}`;
        const codecArgs = format === 'wav'
            ? ['-acodec', 'pcm_s16le', '-ar', '44100', '-ac', '2']
            : ['-acodec', 'libmp3lame', '-b:a', '192k'];

        await ffmpegInstance.exec([
            '-i', 'input.mp4',
            '-vn', // No video
            ...codecArgs,
            '-y', outputFile
        ]);

        const outputData = await ffmpegInstance.readFile(outputFile);
        await ffmpegInstance.deleteFile('input.mp4');
        await ffmpegInstance.deleteFile(outputFile);

        this.log('Audio extraction complete');
        const mimeType = format === 'wav' ? 'audio/wav' : 'audio/mpeg';
        return new Blob([outputData.buffer], { type: mimeType });
    }

    /**
     * Replace audio in video
     * @param videoBlob - Input video blob
     * @param audioBlob - New audio blob
     * @returns Video with replaced audio
     */
    async replaceAudio(videoBlob: Blob, audioBlob: Blob): Promise<Blob> {
        this.log('Replacing audio track...');
        const ffmpegInstance = await loadFFmpeg(this.onLog);

        const videoData = await blobToUint8Array(videoBlob);
        const audioData = await blobToUint8Array(audioBlob);

        await ffmpegInstance.writeFile('input.mp4', videoData);
        await ffmpegInstance.writeFile('audio.mp3', audioData);

        await ffmpegInstance.exec([
            '-i', 'input.mp4',
            '-i', 'audio.mp3',
            '-c:v', 'copy',
            '-map', '0:v:0',
            '-map', '1:a:0',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-shortest',
            '-y', 'output.mp4'
        ]);

        const outputData = await ffmpegInstance.readFile('output.mp4');
        await ffmpegInstance.deleteFile('input.mp4');
        await ffmpegInstance.deleteFile('audio.mp3');
        await ffmpegInstance.deleteFile('output.mp4');

        this.log('Audio replacement complete');
        return new Blob([outputData.buffer], { type: 'video/mp4' });
    }

    /**
     * Mix multiple audio tracks
     * @param videoBlob - Input video blob
     * @param tracks - Array of audio tracks with volume and delay
     * @returns Video with mixed audio
     */
    async mixAudioTracks(videoBlob: Blob, tracks: AudioTrack[]): Promise<Blob> {
        this.log(`Mixing ${tracks.length} audio tracks...`);
        const ffmpegInstance = await loadFFmpeg(this.onLog);

        const videoData = await blobToUint8Array(videoBlob);
        await ffmpegInstance.writeFile('input.mp4', videoData);

        // Write all audio tracks
        const inputArgs = ['-i', 'input.mp4'];
        for (let i = 0; i < tracks.length; i++) {
            const trackData = await blobToUint8Array(tracks[i].blob);
            const filename = `track_${i}.mp3`;
            await ffmpegInstance.writeFile(filename, trackData);
            inputArgs.push('-i', filename);
        }

        // Build filter complex for mixing
        const filterParts = [];
        for (let i = 0; i < tracks.length; i++) {
            const track = tracks[i];
            const inputIndex = i + 1; // +1 because 0 is the video
            let filter = `[${inputIndex}:a]`;

            if (track.volume !== 1.0) {
                filter += `volume=${track.volume}`;
            }
            if (track.delay && track.delay > 0) {
                filter += (track.volume !== 1.0 ? ',' : '') + `adelay=${track.delay * 1000}|${track.delay * 1000}`;
            }

            filterParts.push(filter + `[a${i}]`);
        }

        // Mix all tracks with original video audio
        const mixInputs = ['[0:a]', ...filterParts.map((_, i) => `[a${i}]`)].join('');
        const filterComplex = filterParts.join(';') +
            (filterParts.length > 0 ? ';' : '') +
            `${mixInputs}amix=inputs=${tracks.length + 1}:duration=first[a]`;

        await ffmpegInstance.exec([
            ...inputArgs,
            '-filter_complex', filterComplex,
            '-map', '0:v',
            '-map', '[a]',
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-y', 'output.mp4'
        ]);

        const outputData = await ffmpegInstance.readFile('output.mp4');

        // Cleanup
        await ffmpegInstance.deleteFile('input.mp4');
        await ffmpegInstance.deleteFile('output.mp4');
        for (let i = 0; i < tracks.length; i++) {
            await ffmpegInstance.deleteFile(`track_${i}.mp3`);
        }

        this.log('Audio mixing complete');
        return new Blob([outputData.buffer], { type: 'video/mp4' });
    }

    /**
     * Detect silence segments in video
     * @param videoBlob - Input video blob
     * @param threshold - Silence threshold in dB (default: -30)
     * @param minDuration - Minimum silence duration in seconds (default: 0.5)
     * @returns Array of silence segments
     */
    async detectSilence(videoBlob: Blob, threshold: number = -30, minDuration: number = 0.5): Promise<SilenceSegment[]> {
        this.log('Detecting silence...');
        const ffmpegInstance = await loadFFmpeg(this.onLog);

        const videoData = await blobToUint8Array(videoBlob);
        await ffmpegInstance.writeFile('input.mp4', videoData);

        // Use silencedetect filter
        const silenceSegments: SilenceSegment[] = [];
        let currentStart = -1;

        const logCallback = ({ message }: { message: string }) => {
            // Parse: silence_start: 1.234
            const startMatch = message.match(/silence_start: ([\d.]+)/);
            if (startMatch) {
                currentStart = parseFloat(startMatch[1]);
            }

            // Parse: silence_end: 2.345 | silence_duration: 1.111
            const endMatch = message.match(/silence_end: ([\d.]+) \| silence_duration: ([\d.]+)/);
            if (endMatch && currentStart >= 0) {
                const end = parseFloat(endMatch[1]);
                const duration = parseFloat(endMatch[2]);

                if (duration >= minDuration) {
                    silenceSegments.push({
                        start: currentStart,
                        end: end,
                        duration: duration
                    });
                }
                currentStart = -1;
            }
        };

        ffmpegInstance.on('log', logCallback);

        await ffmpegInstance.exec([
            '-i', 'input.mp4',
            '-af', `silencedetect=noise=${threshold}dB:d=${minDuration}`,
            '-f', 'null',
            '-'
        ]);

        ffmpegInstance.off('log', logCallback);
        await ffmpegInstance.deleteFile('input.mp4');

        this.log(`Detected ${silenceSegments.length} silence segments`);
        return silenceSegments;
    }

    /**
     * Remove silence from video
     * @param videoBlob - Input video blob
     * @param threshold - Silence threshold in dB (default: -30)
     * @param minDuration - Minimum silence duration to remove in seconds (default: 0.5)
     * @returns Video with silence removed
     */
    async removeSilence(videoBlob: Blob, threshold: number = -30, minDuration: number = 0.5): Promise<Blob> {
        this.log('Removing silence...');

        // First detect silence
        const silenceSegments = await this.detectSilence(videoBlob, threshold, minDuration);

        if (silenceSegments.length === 0) {
            this.log('No silence detected');
            return videoBlob;
        }

        const ffmpegInstance = await loadFFmpeg(this.onLog);
        const videoData = await blobToUint8Array(videoBlob);
        await ffmpegInstance.writeFile('input.mp4', videoData);

        // Get video duration
        let duration = 0;
        const logCallback = ({ message }: { message: string }) => {
            const match = message.match(/Duration: (\d{2}):(\d{2}):(\d{2}\.\d{2})/);
            if (match) {
                const [_, h, m, s] = match;
                duration = parseFloat(h) * 3600 + parseFloat(m) * 60 + parseFloat(s);
            }
        };
        ffmpegInstance.on('log', logCallback);
        await ffmpegInstance.exec(['-i', 'input.mp4']);
        ffmpegInstance.off('log', logCallback);

        // Build segments to keep (inverse of silence segments)
        const keepSegments: { start: number; end: number }[] = [];
        let lastEnd = 0;

        for (const silence of silenceSegments) {
            if (silence.start > lastEnd) {
                keepSegments.push({ start: lastEnd, end: silence.start });
            }
            lastEnd = silence.end;
        }

        // Add final segment if there's content after last silence
        if (lastEnd < duration) {
            keepSegments.push({ start: lastEnd, end: duration });
        }

        if (keepSegments.length === 0) {
            this.log('No content to keep after silence removal');
            return videoBlob;
        }

        // Build filter complex to concatenate non-silent segments
        let filterComplex = '';
        for (let i = 0; i < keepSegments.length; i++) {
            const seg = keepSegments[i];
            filterComplex += `[0:v]trim=start=${seg.start}:end=${seg.end},setpts=PTS-STARTPTS[v${i}];`;
            filterComplex += `[0:a]atrim=start=${seg.start}:end=${seg.end},asetpts=PTS-STARTPTS[a${i}];`;
        }

        // Concatenate all segments
        for (let i = 0; i < keepSegments.length; i++) {
            filterComplex += `[v${i}][a${i}]`;
        }
        filterComplex += `concat=n=${keepSegments.length}:v=1:a=1[v][a]`;

        await ffmpegInstance.exec([
            '-i', 'input.mp4',
            '-filter_complex', filterComplex,
            '-map', '[v]',
            '-map', '[a]',
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-y', 'output.mp4'
        ]);

        const outputData = await ffmpegInstance.readFile('output.mp4');
        await ffmpegInstance.deleteFile('input.mp4');
        await ffmpegInstance.deleteFile('output.mp4');

        this.log(`Removed ${silenceSegments.length} silence segments`);
        return new Blob([outputData.buffer], { type: 'video/mp4' });
    }

    /**
     * Analyze loudness statistics (simulated - requires two-pass with loudnorm)
     * @param videoBlob - Input video blob
     * @returns Loudness statistics
     */
    async analyzeLoudness(videoBlob: Blob): Promise<LoudnessStats> {
        this.log('Analyzing loudness...');
        const ffmpegInstance = await loadFFmpeg(this.onLog);

        const videoData = await blobToUint8Array(videoBlob);
        await ffmpegInstance.writeFile('input.mp4', videoData);

        const stats: LoudnessStats = {
            integratedLoudness: -23,
            loudnessRange: 7,
            truePeak: -1
        };

        const logCallback = ({ message }: { message: string }) => {
            // Parse loudnorm output
            const inputI = message.match(/Input Integrated:\s+([-\d.]+)/);
            const inputLRA = message.match(/Input LRA:\s+([-\d.]+)/);
            const inputTP = message.match(/Input True Peak:\s+([-\d.]+)/);

            if (inputI) stats.integratedLoudness = parseFloat(inputI[1]);
            if (inputLRA) stats.loudnessRange = parseFloat(inputLRA[1]);
            if (inputTP) stats.truePeak = parseFloat(inputTP[1]);
        };

        ffmpegInstance.on('log', logCallback);

        // First pass to measure
        await ffmpegInstance.exec([
            '-i', 'input.mp4',
            '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11:print_format=summary',
            '-f', 'null',
            '-'
        ]);

        ffmpegInstance.off('log', logCallback);
        await ffmpegInstance.deleteFile('input.mp4');

        this.log('Loudness analysis complete');
        return stats;
    }
}

// Export singleton instance
export const audioProcessor = new AudioProcessor();

// Export for custom instances
export default AudioProcessor;
