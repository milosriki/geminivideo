import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react';

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

interface AudioTrack {
  id: string;
  name: string;
  level: number; // -60 to +12 dB
  pan: number; // -100 to +100 (L to R)
  mute: boolean;
  solo: boolean;
  eq: {
    low: number; // -12 to +12 dB
    mid: number;
    high: number;
  };
  compression: {
    threshold: number; // -60 to 0 dB
    ratio: number; // 1:1 to 20:1
    attack: number; // 0.1 to 100 ms
    release: number; // 10 to 1000 ms
    enabled: boolean;
  };
  effects: {
    reverb: number; // 0 to 100%
    delay: number; // 0 to 100%
    delayTime: number; // 0 to 1000 ms
    reverbSize: number; // 0 to 100%
  };
  stereoLinked: boolean;
  linkedTrackId?: string;
  currentLevel: number; // Current audio level for VU meter
  peakLevel: number; // Peak hold level
  waveformData: number[]; // Waveform visualization data
}

interface AudioPreset {
  name: string;
  description: string;
  settings: Partial<AudioTrack>;
}

interface MasterSettings {
  level: number;
  limiter: boolean;
  autoDucking: boolean;
  duckingThreshold: number;
  duckingAmount: number;
}

// ============================================================================
// CONSTANTS
// ============================================================================

const AUDIO_PRESETS: AudioPreset[] = [
  {
    name: 'Voice Enhancement',
    description: 'Optimized for clear speech',
    settings: {
      level: 0,
      eq: { low: -3, mid: 6, high: 3 },
      compression: { threshold: -20, ratio: 4, attack: 5, release: 50, enabled: true },
      effects: { reverb: 10, delay: 0, delayTime: 0, reverbSize: 20 }
    }
  },
  {
    name: 'Music Boost',
    description: 'Enhanced music presence',
    settings: {
      level: 2,
      eq: { low: 4, mid: 0, high: 3 },
      compression: { threshold: -15, ratio: 3, attack: 10, release: 100, enabled: true },
      effects: { reverb: 25, delay: 0, delayTime: 0, reverbSize: 40 }
    }
  },
  {
    name: 'Podcast',
    description: 'Broadcast-quality dialogue',
    settings: {
      level: -2,
      eq: { low: -2, mid: 4, high: 2 },
      compression: { threshold: -18, ratio: 6, attack: 3, release: 40, enabled: true },
      effects: { reverb: 5, delay: 0, delayTime: 0, reverbSize: 15 }
    }
  },
  {
    name: 'Cinematic',
    description: 'Wide dynamic range',
    settings: {
      level: 0,
      eq: { low: 3, mid: 0, high: 2 },
      compression: { threshold: -25, ratio: 2, attack: 15, release: 150, enabled: true },
      effects: { reverb: 35, delay: 20, delayTime: 250, reverbSize: 60 }
    }
  }
];

// ============================================================================
// VU METER COMPONENT
// ============================================================================

interface VUMeterProps {
  level: number; // 0-100
  peakLevel: number;
  height?: number;
  width?: number;
}

const VUMeter: React.FC<VUMeterProps> = ({
  level,
  peakLevel,
  height = 200,
  width = 30
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [peakHold, setPeakHold] = useState(peakLevel);
  const peakTimerRef = useRef<NodeJS.Timeout>();

  useEffect(() => {
    if (peakLevel > peakHold) {
      setPeakHold(peakLevel);
      clearTimeout(peakTimerRef.current);
      peakTimerRef.current = setTimeout(() => {
        setPeakHold(0);
      }, 2000);
    }
  }, [peakLevel, peakHold]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.fillStyle = '#1a1a1a';
    ctx.fillRect(0, 0, width, height);

    // Draw background segments
    const segmentHeight = 4;
    const segmentGap = 2;
    const segmentCount = Math.floor(height / (segmentHeight + segmentGap));

    for (let i = 0; i < segmentCount; i++) {
      const y = height - (i * (segmentHeight + segmentGap)) - segmentHeight;
      const intensity = i / segmentCount;

      // Color gradient: green -> yellow -> red
      let color;
      if (intensity < 0.6) {
        color = '#2ecc40'; // Green
      } else if (intensity < 0.85) {
        color = '#ffdc00'; // Yellow
      } else {
        color = '#ff4136'; // Red
      }

      // Dim inactive segments
      const normalizedLevel = level / 100;
      if (intensity <= normalizedLevel) {
        ctx.fillStyle = color;
      } else {
        ctx.fillStyle = '#333333';
      }

      ctx.fillRect(2, y, width - 4, segmentHeight);
    }

    // Draw peak hold indicator
    if (peakHold > 0) {
      const peakY = height - (peakHold / 100 * height);
      ctx.fillStyle = '#ff4136';
      ctx.fillRect(0, peakY - 2, width, 2);
    }

    // Draw border
    ctx.strokeStyle = '#444444';
    ctx.lineWidth = 1;
    ctx.strokeRect(0, 0, width, height);

  }, [level, peakHold, height, width]);

  return (
    <canvas
      ref={canvasRef}
      width={width}
      height={height}
      style={{ display: 'block' }}
    />
  );
};

// ============================================================================
// KNOB COMPONENT
// ============================================================================

interface KnobProps {
  value: number;
  min: number;
  max: number;
  size?: number;
  onChange: (value: number) => void;
  label?: string;
  unit?: string;
  color?: string;
}

const Knob: React.FC<KnobProps> = ({
  value,
  min,
  max,
  size = 50,
  onChange,
  label,
  unit = '',
  color = '#4CAF50'
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const startYRef = useRef(0);
  const startValueRef = useRef(0);

  const angle = useMemo(() => {
    const normalized = (value - min) / (max - min);
    return (normalized * 270) - 135; // -135° to +135°
  }, [value, min, max]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const centerX = size / 2;
    const centerY = size / 2;
    const radius = size / 2 - 5;

    // Clear canvas
    ctx.clearRect(0, 0, size, size);

    // Draw knob body
    const gradient = ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, radius);
    gradient.addColorStop(0, '#444444');
    gradient.addColorStop(1, '#222222');
    ctx.fillStyle = gradient;
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
    ctx.fill();

    // Draw arc track
    ctx.strokeStyle = '#333333';
    ctx.lineWidth = 4;
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius - 5, -135 * Math.PI / 180, 135 * Math.PI / 180);
    ctx.stroke();

    // Draw value arc
    ctx.strokeStyle = color;
    ctx.lineWidth = 4;
    ctx.beginPath();
    ctx.arc(
      centerX,
      centerY,
      radius - 5,
      -135 * Math.PI / 180,
      angle * Math.PI / 180
    );
    ctx.stroke();

    // Draw indicator line
    const indicatorAngle = angle * Math.PI / 180;
    const indicatorLength = radius - 10;
    const indicatorX = centerX + Math.cos(indicatorAngle) * indicatorLength;
    const indicatorY = centerY + Math.sin(indicatorAngle) * indicatorLength;

    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(centerX, centerY);
    ctx.lineTo(indicatorX, indicatorY);
    ctx.stroke();

    // Draw center dot
    ctx.fillStyle = '#666666';
    ctx.beginPath();
    ctx.arc(centerX, centerY, 4, 0, Math.PI * 2);
    ctx.fill();

  }, [angle, size, color]);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    setIsDragging(true);
    startYRef.current = e.clientY;
    startValueRef.current = value;
    e.preventDefault();
  }, [value]);

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!isDragging) return;

    const deltaY = startYRef.current - e.clientY;
    const range = max - min;
    const sensitivity = range / 200; // 200 pixels for full range
    const newValue = Math.max(min, Math.min(max, startValueRef.current + (deltaY * sensitivity)));

    onChange(newValue);
  }, [isDragging, min, max, onChange]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  useEffect(() => {
    if (isDragging) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
      return () => {
        window.removeEventListener('mousemove', handleMouseMove);
        window.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging, handleMouseMove, handleMouseUp]);

  const displayValue = value.toFixed(1);

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      userSelect: 'none'
    }}>
      <canvas
        ref={canvasRef}
        width={size}
        height={size}
        onMouseDown={handleMouseDown}
        style={{ cursor: isDragging ? 'grabbing' : 'grab' }}
      />
      <div style={{
        marginTop: '4px',
        fontSize: '11px',
        color: '#ffffff',
        fontWeight: 'bold'
      }}>
        {displayValue}{unit}
      </div>
      {label && (
        <div style={{
          marginTop: '2px',
          fontSize: '10px',
          color: '#aaaaaa',
          textAlign: 'center'
        }}>
          {label}
        </div>
      )}
    </div>
  );
};

// ============================================================================
// VERTICAL FADER COMPONENT
// ============================================================================

interface FaderProps {
  value: number;
  min: number;
  max: number;
  height?: number;
  width?: number;
  onChange: (value: number) => void;
  label?: string;
  unit?: string;
}

const VerticalFader: React.FC<FaderProps> = ({
  value,
  min,
  max,
  height = 200,
  width = 40,
  onChange,
  label,
  unit = 'dB'
}) => {
  const trackRef = useRef<HTMLDivElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  const percentage = useMemo(() => {
    return ((value - min) / (max - min)) * 100;
  }, [value, min, max]);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    setIsDragging(true);
    updateValue(e.clientY);
    e.preventDefault();
  }, []);

  const updateValue = useCallback((clientY: number) => {
    if (!trackRef.current) return;

    const rect = trackRef.current.getBoundingClientRect();
    const y = clientY - rect.top;
    const percentage = Math.max(0, Math.min(100, ((height - y) / height) * 100));
    const newValue = min + (percentage / 100) * (max - min);

    onChange(Math.round(newValue * 2) / 2); // Round to 0.5 dB
  }, [height, min, max, onChange]);

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!isDragging) return;
    updateValue(e.clientY);
  }, [isDragging, updateValue]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  useEffect(() => {
    if (isDragging) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
      return () => {
        window.removeEventListener('mousemove', handleMouseMove);
        window.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging, handleMouseMove, handleMouseUp]);

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      userSelect: 'none'
    }}>
      <div style={{
        fontSize: '12px',
        color: '#ffffff',
        marginBottom: '4px',
        fontWeight: 'bold'
      }}>
        {value.toFixed(1)}{unit}
      </div>
      <div
        ref={trackRef}
        onMouseDown={handleMouseDown}
        style={{
          position: 'relative',
          width: `${width}px`,
          height: `${height}px`,
          backgroundColor: '#2a2a2a',
          borderRadius: '4px',
          cursor: isDragging ? 'grabbing' : 'grab',
          border: '1px solid #444444'
        }}
      >
        {/* Fader fill */}
        <div style={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          height: `${percentage}%`,
          backgroundColor: value > 0 ? '#ff9800' : '#4CAF50',
          borderRadius: '4px',
          transition: isDragging ? 'none' : 'height 0.1s ease'
        }} />

        {/* 0 dB marker */}
        {min < 0 && max > 0 && (
          <div style={{
            position: 'absolute',
            left: '-5px',
            right: '-5px',
            bottom: `${((0 - min) / (max - min)) * 100}%`,
            height: '2px',
            backgroundColor: '#ffeb3b',
            zIndex: 1
          }} />
        )}

        {/* Fader handle */}
        <div style={{
          position: 'absolute',
          left: '-5px',
          right: '-5px',
          bottom: `calc(${percentage}% - 8px)`,
          height: '16px',
          backgroundColor: '#666666',
          border: '2px solid #888888',
          borderRadius: '3px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.3)',
          zIndex: 2
        }} />
      </div>
      {label && (
        <div style={{
          marginTop: '6px',
          fontSize: '10px',
          color: '#aaaaaa',
          textAlign: 'center'
        }}>
          {label}
        </div>
      )}
    </div>
  );
};

// ============================================================================
// WAVEFORM COMPONENT
// ============================================================================

interface WaveformProps {
  data: number[];
  width?: number;
  height?: number;
  color?: string;
}

const Waveform: React.FC<WaveformProps> = ({
  data,
  width = 200,
  height = 40,
  color = '#4CAF50'
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !data.length) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.fillStyle = '#1a1a1a';
    ctx.fillRect(0, 0, width, height);

    // Draw waveform
    ctx.strokeStyle = color;
    ctx.lineWidth = 1;
    ctx.beginPath();

    const step = Math.ceil(data.length / width);
    const amp = height / 2;

    for (let i = 0; i < width; i++) {
      const dataIndex = Math.floor(i * step);
      const value = data[dataIndex] || 0;
      const y = amp + (value * amp);

      if (i === 0) {
        ctx.moveTo(i, y);
      } else {
        ctx.lineTo(i, y);
      }
    }

    ctx.stroke();

    // Draw center line
    ctx.strokeStyle = '#333333';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, height / 2);
    ctx.lineTo(width, height / 2);
    ctx.stroke();

  }, [data, width, height, color]);

  return (
    <canvas
      ref={canvasRef}
      width={width}
      height={height}
      style={{ display: 'block', borderRadius: '4px' }}
    />
  );
};

// ============================================================================
// TRACK CHANNEL STRIP COMPONENT
// ============================================================================

interface TrackChannelProps {
  track: AudioTrack;
  onUpdate: (trackId: string, updates: Partial<AudioTrack>) => void;
  onRemove: (trackId: string) => void;
  isSoloActive: boolean;
}

const TrackChannel: React.FC<TrackChannelProps> = ({
  track,
  onUpdate,
  onRemove,
  isSoloActive
}) => {
  const [showEQ, setShowEQ] = useState(false);
  const [showCompression, setShowCompression] = useState(false);
  const [showEffects, setShowEffects] = useState(false);
  const [isEditingName, setIsEditingName] = useState(false);
  const [editedName, setEditedName] = useState(track.name);

  const handleNameSubmit = () => {
    onUpdate(track.id, { name: editedName });
    setIsEditingName(false);
  };

  const isActive = !track.mute && (!isSoloActive || track.solo);

  return (
    <div style={{
      backgroundColor: '#2a2a2a',
      borderRadius: '8px',
      padding: '12px',
      minWidth: '180px',
      border: '1px solid #444444',
      opacity: isActive ? 1 : 0.5
    }}>
      {/* Track Name */}
      <div style={{ marginBottom: '12px' }}>
        {isEditingName ? (
          <input
            type="text"
            value={editedName}
            onChange={(e) => setEditedName(e.target.value)}
            onBlur={handleNameSubmit}
            onKeyDown={(e) => e.key === 'Enter' && handleNameSubmit()}
            autoFocus
            style={{
              width: '100%',
              padding: '4px',
              backgroundColor: '#1a1a1a',
              color: '#ffffff',
              border: '1px solid #4CAF50',
              borderRadius: '4px',
              fontSize: '12px'
            }}
          />
        ) : (
          <div
            onClick={() => setIsEditingName(true)}
            style={{
              fontSize: '12px',
              fontWeight: 'bold',
              color: '#ffffff',
              cursor: 'pointer',
              padding: '4px',
              borderRadius: '4px',
              border: '1px solid transparent',
              ':hover': { border: '1px solid #666666' }
            }}
          >
            {track.name}
          </div>
        )}
      </div>

      {/* Waveform Preview */}
      <div style={{ marginBottom: '12px' }}>
        <Waveform
          data={track.waveformData}
          width={156}
          height={30}
          color={isActive ? '#4CAF50' : '#666666'}
        />
      </div>

      {/* VU Meter and Fader */}
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        gap: '8px',
        marginBottom: '12px'
      }}>
        <VUMeter
          level={track.currentLevel}
          peakLevel={track.peakLevel}
          height={180}
          width={24}
        />
        <VerticalFader
          value={track.level}
          min={-60}
          max={12}
          height={180}
          width={32}
          onChange={(value) => onUpdate(track.id, { level: value })}
        />
      </div>

      {/* Pan Knob */}
      <div style={{ marginBottom: '12px', display: 'flex', justifyContent: 'center' }}>
        <Knob
          value={track.pan}
          min={-100}
          max={100}
          size={45}
          onChange={(value) => onUpdate(track.id, { pan: value })}
          label="Pan"
          unit=""
          color="#2196F3"
        />
      </div>

      {/* Mute/Solo Buttons */}
      <div style={{
        display: 'flex',
        gap: '6px',
        marginBottom: '12px',
        justifyContent: 'center'
      }}>
        <button
          onClick={() => onUpdate(track.id, { mute: !track.mute })}
          style={{
            flex: 1,
            padding: '6px',
            backgroundColor: track.mute ? '#f44336' : '#444444',
            color: '#ffffff',
            border: 'none',
            borderRadius: '4px',
            fontSize: '11px',
            fontWeight: 'bold',
            cursor: 'pointer',
            transition: 'background-color 0.2s'
          }}
        >
          M
        </button>
        <button
          onClick={() => onUpdate(track.id, { solo: !track.solo })}
          style={{
            flex: 1,
            padding: '6px',
            backgroundColor: track.solo ? '#ffeb3b' : '#444444',
            color: track.solo ? '#000000' : '#ffffff',
            border: 'none',
            borderRadius: '4px',
            fontSize: '11px',
            fontWeight: 'bold',
            cursor: 'pointer',
            transition: 'background-color 0.2s'
          }}
        >
          S
        </button>
      </div>

      {/* EQ Section */}
      <div style={{ marginBottom: '8px' }}>
        <button
          onClick={() => setShowEQ(!showEQ)}
          style={{
            width: '100%',
            padding: '6px',
            backgroundColor: '#333333',
            color: '#ffffff',
            border: '1px solid #555555',
            borderRadius: '4px',
            fontSize: '11px',
            cursor: 'pointer',
            fontWeight: 'bold'
          }}
        >
          {showEQ ? '▼' : '▶'} 3-Band EQ
        </button>
        {showEQ && (
          <div style={{
            marginTop: '8px',
            display: 'flex',
            justifyContent: 'space-around',
            padding: '8px',
            backgroundColor: '#1a1a1a',
            borderRadius: '4px'
          }}>
            <Knob
              value={track.eq.low}
              min={-12}
              max={12}
              size={40}
              onChange={(value) => onUpdate(track.id, {
                eq: { ...track.eq, low: value }
              })}
              label="Low"
              unit="dB"
              color="#f44336"
            />
            <Knob
              value={track.eq.mid}
              min={-12}
              max={12}
              size={40}
              onChange={(value) => onUpdate(track.id, {
                eq: { ...track.eq, mid: value }
              })}
              label="Mid"
              unit="dB"
              color="#4CAF50"
            />
            <Knob
              value={track.eq.high}
              min={-12}
              max={12}
              size={40}
              onChange={(value) => onUpdate(track.id, {
                eq: { ...track.eq, high: value }
              })}
              label="High"
              unit="dB"
              color="#2196F3"
            />
          </div>
        )}
      </div>

      {/* Compression Section */}
      <div style={{ marginBottom: '8px' }}>
        <button
          onClick={() => setShowCompression(!showCompression)}
          style={{
            width: '100%',
            padding: '6px',
            backgroundColor: '#333333',
            color: '#ffffff',
            border: '1px solid #555555',
            borderRadius: '4px',
            fontSize: '11px',
            cursor: 'pointer',
            fontWeight: 'bold'
          }}
        >
          {showCompression ? '▼' : '▶'} Compression
        </button>
        {showCompression && (
          <div style={{
            marginTop: '8px',
            padding: '8px',
            backgroundColor: '#1a1a1a',
            borderRadius: '4px'
          }}>
            <div style={{ marginBottom: '8px' }}>
              <label style={{
                display: 'flex',
                alignItems: 'center',
                fontSize: '11px',
                color: '#ffffff',
                cursor: 'pointer'
              }}>
                <input
                  type="checkbox"
                  checked={track.compression.enabled}
                  onChange={(e) => onUpdate(track.id, {
                    compression: { ...track.compression, enabled: e.target.checked }
                  })}
                  style={{ marginRight: '6px' }}
                />
                Enable Compressor
              </label>
            </div>
            <div style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: '8px'
            }}>
              <Knob
                value={track.compression.threshold}
                min={-60}
                max={0}
                size={40}
                onChange={(value) => onUpdate(track.id, {
                  compression: { ...track.compression, threshold: value }
                })}
                label="Threshold"
                unit="dB"
                color="#ff9800"
              />
              <Knob
                value={track.compression.ratio}
                min={1}
                max={20}
                size={40}
                onChange={(value) => onUpdate(track.id, {
                  compression: { ...track.compression, ratio: value }
                })}
                label="Ratio"
                unit=":1"
                color="#ff9800"
              />
              <Knob
                value={track.compression.attack}
                min={0.1}
                max={100}
                size={40}
                onChange={(value) => onUpdate(track.id, {
                  compression: { ...track.compression, attack: value }
                })}
                label="Attack"
                unit="ms"
                color="#ff9800"
              />
              <Knob
                value={track.compression.release}
                min={10}
                max={1000}
                size={40}
                onChange={(value) => onUpdate(track.id, {
                  compression: { ...track.compression, release: value }
                })}
                label="Release"
                unit="ms"
                color="#ff9800"
              />
            </div>
          </div>
        )}
      </div>

      {/* Effects Section */}
      <div style={{ marginBottom: '8px' }}>
        <button
          onClick={() => setShowEffects(!showEffects)}
          style={{
            width: '100%',
            padding: '6px',
            backgroundColor: '#333333',
            color: '#ffffff',
            border: '1px solid #555555',
            borderRadius: '4px',
            fontSize: '11px',
            cursor: 'pointer',
            fontWeight: 'bold'
          }}
        >
          {showEffects ? '▼' : '▶'} Effects Rack
        </button>
        {showEffects && (
          <div style={{
            marginTop: '8px',
            padding: '8px',
            backgroundColor: '#1a1a1a',
            borderRadius: '4px'
          }}>
            <div style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: '8px',
              marginBottom: '8px'
            }}>
              <Knob
                value={track.effects.reverb}
                min={0}
                max={100}
                size={40}
                onChange={(value) => onUpdate(track.id, {
                  effects: { ...track.effects, reverb: value }
                })}
                label="Reverb"
                unit="%"
                color="#9C27B0"
              />
              <Knob
                value={track.effects.reverbSize}
                min={0}
                max={100}
                size={40}
                onChange={(value) => onUpdate(track.id, {
                  effects: { ...track.effects, reverbSize: value }
                })}
                label="Size"
                unit="%"
                color="#9C27B0"
              />
              <Knob
                value={track.effects.delay}
                min={0}
                max={100}
                size={40}
                onChange={(value) => onUpdate(track.id, {
                  effects: { ...track.effects, delay: value }
                })}
                label="Delay"
                unit="%"
                color="#00BCD4"
              />
              <Knob
                value={track.effects.delayTime}
                min={0}
                max={1000}
                size={40}
                onChange={(value) => onUpdate(track.id, {
                  effects: { ...track.effects, delayTime: value }
                })}
                label="Time"
                unit="ms"
                color="#00BCD4"
              />
            </div>
          </div>
        )}
      </div>

      {/* Stereo Link */}
      <div style={{ marginBottom: '8px' }}>
        <label style={{
          display: 'flex',
          alignItems: 'center',
          fontSize: '11px',
          color: '#ffffff',
          cursor: 'pointer'
        }}>
          <input
            type="checkbox"
            checked={track.stereoLinked}
            onChange={(e) => onUpdate(track.id, { stereoLinked: e.target.checked })}
            style={{ marginRight: '6px' }}
          />
          Link Stereo
        </label>
      </div>

      {/* Remove Track Button */}
      <button
        onClick={() => onRemove(track.id)}
        style={{
          width: '100%',
          padding: '6px',
          backgroundColor: '#d32f2f',
          color: '#ffffff',
          border: 'none',
          borderRadius: '4px',
          fontSize: '11px',
          cursor: 'pointer',
          fontWeight: 'bold',
          transition: 'background-color 0.2s'
        }}
        onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#b71c1c'}
        onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#d32f2f'}
      >
        Remove Track
      </button>
    </div>
  );
};

// ============================================================================
// MAIN AUDIO MIXER PANEL COMPONENT
// ============================================================================

const AudioMixerPanel: React.FC = () => {
  const [tracks, setTracks] = useState<AudioTrack[]>([
    {
      id: '1',
      name: 'Voice',
      level: -6,
      pan: 0,
      mute: false,
      solo: false,
      eq: { low: 0, mid: 0, high: 0 },
      compression: {
        threshold: -20,
        ratio: 4,
        attack: 5,
        release: 50,
        enabled: false
      },
      effects: {
        reverb: 0,
        delay: 0,
        delayTime: 200,
        reverbSize: 30
      },
      stereoLinked: false,
      currentLevel: 45,
      peakLevel: 78,
      waveformData: Array.from({ length: 100 }, () => Math.random() * 2 - 1)
    },
    {
      id: '2',
      name: 'Music',
      level: -12,
      pan: 0,
      mute: false,
      solo: false,
      eq: { low: 0, mid: 0, high: 0 },
      compression: {
        threshold: -20,
        ratio: 3,
        attack: 10,
        release: 100,
        enabled: false
      },
      effects: {
        reverb: 0,
        delay: 0,
        delayTime: 200,
        reverbSize: 30
      },
      stereoLinked: true,
      currentLevel: 35,
      peakLevel: 62,
      waveformData: Array.from({ length: 100 }, () => Math.random() * 2 - 1)
    }
  ]);

  const [master, setMaster] = useState<MasterSettings>({
    level: 0,
    limiter: true,
    autoDucking: false,
    duckingThreshold: -30,
    duckingAmount: 6
  });

  const [selectedPreset, setSelectedPreset] = useState<string>('');

  // Simulate real-time level monitoring
  useEffect(() => {
    const interval = setInterval(() => {
      setTracks(prevTracks =>
        prevTracks.map(track => ({
          ...track,
          currentLevel: track.mute ? 0 : Math.random() * 80,
          peakLevel: track.mute ? 0 : Math.random() * 95
        }))
      );
    }, 100);

    return () => clearInterval(interval);
  }, []);

  const updateTrack = useCallback((trackId: string, updates: Partial<AudioTrack>) => {
    setTracks(prevTracks =>
      prevTracks.map(track =>
        track.id === trackId ? { ...track, ...updates } : track
      )
    );
  }, []);

  const removeTrack = useCallback((trackId: string) => {
    setTracks(prevTracks => prevTracks.filter(track => track.id !== trackId));
  }, []);

  const addTrack = useCallback(() => {
    const newTrack: AudioTrack = {
      id: Date.now().toString(),
      name: `Track ${tracks.length + 1}`,
      level: -6,
      pan: 0,
      mute: false,
      solo: false,
      eq: { low: 0, mid: 0, high: 0 },
      compression: {
        threshold: -20,
        ratio: 4,
        attack: 5,
        release: 50,
        enabled: false
      },
      effects: {
        reverb: 0,
        delay: 0,
        delayTime: 200,
        reverbSize: 30
      },
      stereoLinked: false,
      currentLevel: 0,
      peakLevel: 0,
      waveformData: Array.from({ length: 100 }, () => Math.random() * 2 - 1)
    };
    setTracks(prevTracks => [...prevTracks, newTrack]);
  }, [tracks.length]);

  const applyPreset = useCallback((presetName: string) => {
    const preset = AUDIO_PRESETS.find(p => p.name === presetName);
    if (!preset) return;

    setTracks(prevTracks =>
      prevTracks.map(track => ({
        ...track,
        ...preset.settings
      }))
    );
    setSelectedPreset(presetName);
  }, []);

  const normalize = useCallback(() => {
    // Simulate EBU R128 normalization
    const targetLUFS = -23; // EBU R128 standard
    setTracks(prevTracks =>
      prevTracks.map(track => ({
        ...track,
        level: targetLUFS
      }))
    );
    alert('Audio normalized to EBU R128 standard (-23 LUFS)');
  }, []);

  const isSoloActive = useMemo(() => {
    return tracks.some(track => track.solo);
  }, [tracks]);

  return (
    <div style={{
      backgroundColor: '#1a1a1a',
      color: '#ffffff',
      padding: '20px',
      minHeight: '100vh',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
    }}>
      {/* Header */}
      <div style={{
        marginBottom: '20px',
        paddingBottom: '16px',
        borderBottom: '2px solid #333333'
      }}>
        <h1 style={{
          margin: '0 0 16px 0',
          fontSize: '24px',
          fontWeight: 'bold',
          color: '#4CAF50'
        }}>
          Pro Audio Mixer
        </h1>

        {/* Toolbar */}
        <div style={{
          display: 'flex',
          gap: '12px',
          flexWrap: 'wrap',
          alignItems: 'center'
        }}>
          <button
            onClick={addTrack}
            style={{
              padding: '8px 16px',
              backgroundColor: '#4CAF50',
              color: '#ffffff',
              border: 'none',
              borderRadius: '4px',
              fontSize: '13px',
              fontWeight: 'bold',
              cursor: 'pointer',
              transition: 'background-color 0.2s'
            }}
            onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#45a049'}
            onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#4CAF50'}
          >
            + Add Track
          </button>

          <select
            value={selectedPreset}
            onChange={(e) => applyPreset(e.target.value)}
            style={{
              padding: '8px 12px',
              backgroundColor: '#333333',
              color: '#ffffff',
              border: '1px solid #555555',
              borderRadius: '4px',
              fontSize: '13px',
              cursor: 'pointer'
            }}
          >
            <option value="">Select Preset...</option>
            {AUDIO_PRESETS.map(preset => (
              <option key={preset.name} value={preset.name}>
                {preset.name} - {preset.description}
              </option>
            ))}
          </select>

          <button
            onClick={normalize}
            style={{
              padding: '8px 16px',
              backgroundColor: '#2196F3',
              color: '#ffffff',
              border: 'none',
              borderRadius: '4px',
              fontSize: '13px',
              fontWeight: 'bold',
              cursor: 'pointer',
              transition: 'background-color 0.2s'
            }}
            onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#1976D2'}
            onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#2196F3'}
          >
            Normalize (EBU R128)
          </button>

          <label style={{
            display: 'flex',
            alignItems: 'center',
            padding: '8px 12px',
            backgroundColor: '#333333',
            borderRadius: '4px',
            cursor: 'pointer'
          }}>
            <input
              type="checkbox"
              checked={master.autoDucking}
              onChange={(e) => setMaster({ ...master, autoDucking: e.target.checked })}
              style={{ marginRight: '8px' }}
            />
            <span style={{ fontSize: '13px' }}>Auto-Ducking</span>
          </label>

          {master.autoDucking && (
            <>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '12px', color: '#aaaaaa' }}>Threshold:</span>
                <input
                  type="range"
                  min="-60"
                  max="0"
                  value={master.duckingThreshold}
                  onChange={(e) => setMaster({
                    ...master,
                    duckingThreshold: Number(e.target.value)
                  })}
                  style={{ width: '100px' }}
                />
                <span style={{ fontSize: '12px', minWidth: '50px' }}>
                  {master.duckingThreshold}dB
                </span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '12px', color: '#aaaaaa' }}>Amount:</span>
                <input
                  type="range"
                  min="0"
                  max="20"
                  value={master.duckingAmount}
                  onChange={(e) => setMaster({
                    ...master,
                    duckingAmount: Number(e.target.value)
                  })}
                  style={{ width: '100px' }}
                />
                <span style={{ fontSize: '12px', minWidth: '50px' }}>
                  {master.duckingAmount}dB
                </span>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Mixer Channels */}
      <div style={{
        display: 'flex',
        gap: '16px',
        overflowX: 'auto',
        paddingBottom: '20px'
      }}>
        {/* Track Channels */}
        {tracks.map(track => (
          <TrackChannel
            key={track.id}
            track={track}
            onUpdate={updateTrack}
            onRemove={removeTrack}
            isSoloActive={isSoloActive}
          />
        ))}

        {/* Master Channel */}
        <div style={{
          backgroundColor: '#2a2a2a',
          borderRadius: '8px',
          padding: '12px',
          minWidth: '180px',
          border: '2px solid #4CAF50'
        }}>
          <div style={{
            marginBottom: '12px',
            fontSize: '14px',
            fontWeight: 'bold',
            color: '#4CAF50',
            textAlign: 'center'
          }}>
            MASTER
          </div>

          {/* Master VU Meters (Stereo) */}
          <div style={{
            display: 'flex',
            justifyContent: 'center',
            gap: '8px',
            marginBottom: '12px'
          }}>
            <VUMeter
              level={Math.max(...tracks.map(t => t.currentLevel))}
              peakLevel={Math.max(...tracks.map(t => t.peakLevel))}
              height={180}
              width={24}
            />
            <VUMeter
              level={Math.max(...tracks.map(t => t.currentLevel)) - 5}
              peakLevel={Math.max(...tracks.map(t => t.peakLevel)) - 3}
              height={180}
              width={24}
            />
            <VerticalFader
              value={master.level}
              min={-60}
              max={12}
              height={180}
              width={32}
              onChange={(value) => setMaster({ ...master, level: value })}
              label="Master"
            />
          </div>

          {/* Master Limiter */}
          <div style={{ marginBottom: '12px' }}>
            <label style={{
              display: 'flex',
              alignItems: 'center',
              fontSize: '11px',
              color: '#ffffff',
              cursor: 'pointer',
              justifyContent: 'center'
            }}>
              <input
                type="checkbox"
                checked={master.limiter}
                onChange={(e) => setMaster({ ...master, limiter: e.target.checked })}
                style={{ marginRight: '6px' }}
              />
              Master Limiter
            </label>
          </div>

          {/* Master Output Level Display */}
          <div style={{
            padding: '12px',
            backgroundColor: '#1a1a1a',
            borderRadius: '4px',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '10px', color: '#aaaaaa', marginBottom: '4px' }}>
              Output Level
            </div>
            <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#4CAF50' }}>
              {master.level.toFixed(1)} dB
            </div>
            <div style={{ fontSize: '10px', color: '#aaaaaa', marginTop: '4px' }}>
              {master.limiter ? 'Limited' : 'Unlimited'}
            </div>
          </div>
        </div>
      </div>

      {/* Info Panel */}
      <div style={{
        marginTop: '20px',
        padding: '16px',
        backgroundColor: '#2a2a2a',
        borderRadius: '8px',
        border: '1px solid #444444'
      }}>
        <h3 style={{
          margin: '0 0 12px 0',
          fontSize: '14px',
          color: '#4CAF50'
        }}>
          Mixer Status
        </h3>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '12px',
          fontSize: '12px'
        }}>
          <div>
            <span style={{ color: '#aaaaaa' }}>Active Tracks:</span>{' '}
            <span style={{ color: '#ffffff', fontWeight: 'bold' }}>
              {tracks.filter(t => !t.mute).length} / {tracks.length}
            </span>
          </div>
          <div>
            <span style={{ color: '#aaaaaa' }}>Solo Mode:</span>{' '}
            <span style={{
              color: isSoloActive ? '#ffeb3b' : '#ffffff',
              fontWeight: 'bold'
            }}>
              {isSoloActive ? 'ON' : 'OFF'}
            </span>
          </div>
          <div>
            <span style={{ color: '#aaaaaa' }}>Auto-Ducking:</span>{' '}
            <span style={{
              color: master.autoDucking ? '#4CAF50' : '#ffffff',
              fontWeight: 'bold'
            }}>
              {master.autoDucking ? 'ENABLED' : 'DISABLED'}
            </span>
          </div>
          <div>
            <span style={{ color: '#aaaaaa' }}>Master Limiter:</span>{' '}
            <span style={{
              color: master.limiter ? '#4CAF50' : '#ffffff',
              fontWeight: 'bold'
            }}>
              {master.limiter ? 'ON' : 'OFF'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AudioMixerPanel;
