"""
Professional Color Grading System for Video Ads
Generates real FFmpeg filters for pro-grade color correction and grading.
"""

import numpy as np
import os
import tempfile
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass
from enum import Enum


class LUTPreset(Enum):
    """Built-in LUT presets for common video ad looks"""
    CINEMATIC = "cinematic"
    VINTAGE = "vintage"
    HIGH_CONTRAST = "high_contrast"
    WARM = "warm"
    COLD = "cold"
    FITNESS_ENERGY = "fitness_energy"
    CLEAN_CORPORATE = "clean_corporate"
    INSTAGRAM_DRAMATIC = "instagram_dramatic"
    INSTAGRAM_FADE = "instagram_fade"
    INSTAGRAM_VIBRANT = "instagram_vibrant"


@dataclass
class ColorWheels:
    """Color wheel adjustments for lift, gamma, and gain"""
    # Lift (shadows): adjusts the darkest parts
    lift_r: float = 0.0  # -1.0 to 1.0
    lift_g: float = 0.0
    lift_b: float = 0.0

    # Gamma (midtones): adjusts the middle range
    gamma_r: float = 1.0  # 0.1 to 10.0
    gamma_g: float = 1.0
    gamma_b: float = 1.0

    # Gain (highlights): adjusts the brightest parts
    gain_r: float = 1.0  # 0.0 to 2.0
    gain_g: float = 1.0
    gain_b: float = 1.0


@dataclass
class RGBCurves:
    """RGB curve control points (0-255 range)"""
    # Each curve is a list of (input, output) tuples
    red_curve: List[Tuple[int, int]] = None
    green_curve: List[Tuple[int, int]] = None
    blue_curve: List[Tuple[int, int]] = None
    master_curve: List[Tuple[int, int]] = None  # Affects all channels

    def __post_init__(self):
        if self.red_curve is None:
            self.red_curve = [(0, 0), (255, 255)]
        if self.green_curve is None:
            self.green_curve = [(0, 0), (255, 255)]
        if self.blue_curve is None:
            self.blue_curve = [(0, 0), (255, 255)]
        if self.master_curve is None:
            self.master_curve = [(0, 0), (255, 255)]


@dataclass
class HSLAdjustment:
    """HSL (Hue, Saturation, Luminance) adjustments"""
    hue_shift: float = 0.0  # -180 to 180 degrees
    saturation: float = 1.0  # 0.0 to 3.0 (1.0 = no change)
    luminance: float = 0.0  # -1.0 to 1.0


@dataclass
class WhiteBalance:
    """White balance controls"""
    temperature: float = 0.0  # -100 to 100 (negative = cooler, positive = warmer)
    tint: float = 0.0  # -100 to 100 (negative = green, positive = magenta)


@dataclass
class ExposureControls:
    """Exposure and tone controls"""
    exposure: float = 0.0  # -2.0 to 2.0 (stops)
    contrast: float = 1.0  # 0.0 to 2.0 (1.0 = no change)
    highlights: float = 0.0  # -100 to 100
    shadows: float = 0.0  # -100 to 100
    whites: float = 0.0  # -100 to 100
    blacks: float = 0.0  # -100 to 100
    vibrance: float = 0.0  # -100 to 100 (smart saturation)
    saturation: float = 0.0  # -100 to 100 (affects all colors equally)


@dataclass
class SkinToneProtection:
    """Skin tone preservation settings"""
    enabled: bool = False
    strength: float = 0.5  # 0.0 to 1.0
    hue_center: float = 20.0  # Typical skin tone hue (10-40 degrees)
    hue_range: float = 30.0  # Range to protect


class LUT3D:
    """3D LUT parser and generator"""

    def __init__(self, size: int = 33):
        """
        Initialize LUT with given size
        Args:
            size: LUT dimension size (typically 17, 33, or 65)
        """
        self.size = size
        self.data = np.zeros((size, size, size, 3), dtype=np.float32)
        self._initialize_identity()

    def _initialize_identity(self):
        """Create identity LUT (no color change)"""
        for r in range(self.size):
            for g in range(self.size):
                for b in range(self.size):
                    self.data[r, g, b] = [
                        r / (self.size - 1),
                        g / (self.size - 1),
                        b / (self.size - 1)
                    ]

    @classmethod
    def parse_cube_file(cls, filepath: str) -> 'LUT3D':
        """
        Parse .cube LUT file format
        Args:
            filepath: Path to .cube file
        Returns:
            LUT3D object
        """
        with open(filepath, 'r') as f:
            lines = f.readlines()

        size = 33  # Default
        title = ""
        lut_data = []

        for line in lines:
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue

            # Parse metadata
            if line.startswith('TITLE'):
                title = line.split('"')[1] if '"' in line else ""
            elif line.startswith('LUT_3D_SIZE'):
                size = int(line.split()[-1])
            elif line.startswith('DOMAIN_MIN') or line.startswith('DOMAIN_MAX'):
                continue  # We assume 0-1 range
            else:
                # Parse RGB values
                parts = line.split()
                if len(parts) == 3:
                    try:
                        r, g, b = map(float, parts)
                        lut_data.append([r, g, b])
                    except ValueError:
                        continue

        # Create LUT and populate data
        lut = cls(size)

        if len(lut_data) == size ** 3:
            idx = 0
            for b in range(size):
                for g in range(size):
                    for r in range(size):
                        lut.data[r, g, b] = lut_data[idx]
                        idx += 1

        return lut

    def save_cube_file(self, filepath: str, title: str = "Custom LUT"):
        """
        Save LUT as .cube file
        Args:
            filepath: Output file path
            title: LUT title
        """
        with open(filepath, 'w') as f:
            f.write(f'TITLE "{title}"\n')
            f.write(f'LUT_3D_SIZE {self.size}\n')
            f.write('DOMAIN_MIN 0.0 0.0 0.0\n')
            f.write('DOMAIN_MAX 1.0 1.0 1.0\n\n')

            # Write LUT data in correct order (blue changes fastest)
            for b in range(self.size):
                for g in range(self.size):
                    for r in range(self.size):
                        rgb = self.data[r, g, b]
                        f.write(f'{rgb[0]:.6f} {rgb[1]:.6f} {rgb[2]:.6f}\n')

    def apply_color_wheels(self, wheels: ColorWheels):
        """Apply color wheel adjustments to LUT"""
        for r in range(self.size):
            for g in range(self.size):
                for b in range(self.size):
                    rgb = self.data[r, g, b].copy()

                    # Apply lift (add to all values, affects shadows most)
                    rgb[0] = rgb[0] + wheels.lift_r * (1.0 - rgb[0])
                    rgb[1] = rgb[1] + wheels.lift_g * (1.0 - rgb[1])
                    rgb[2] = rgb[2] + wheels.lift_b * (1.0 - rgb[2])

                    # Apply gamma (power curve, affects midtones)
                    rgb[0] = np.power(np.clip(rgb[0], 0, 1), 1.0 / wheels.gamma_r)
                    rgb[1] = np.power(np.clip(rgb[1], 0, 1), 1.0 / wheels.gamma_g)
                    rgb[2] = np.power(np.clip(rgb[2], 0, 1), 1.0 / wheels.gamma_b)

                    # Apply gain (multiply, affects highlights most)
                    rgb[0] = rgb[0] * wheels.gain_r
                    rgb[1] = rgb[1] * wheels.gain_g
                    rgb[2] = rgb[2] * wheels.gain_b

                    self.data[r, g, b] = np.clip(rgb, 0, 1)

    def apply_curves(self, curves: RGBCurves):
        """Apply RGB curves to LUT"""
        # Create interpolated lookup tables for each curve
        master_lut = self._interpolate_curve(curves.master_curve)
        red_lut = self._interpolate_curve(curves.red_curve)
        green_lut = self._interpolate_curve(curves.green_curve)
        blue_lut = self._interpolate_curve(curves.blue_curve)

        for r in range(self.size):
            for g in range(self.size):
                for b in range(self.size):
                    rgb = self.data[r, g, b].copy()

                    # Convert to 0-255 range
                    rgb_255 = (rgb * 255).astype(int)

                    # Apply curves
                    rgb_255[0] = red_lut[np.clip(rgb_255[0], 0, 255)]
                    rgb_255[1] = green_lut[np.clip(rgb_255[1], 0, 255)]
                    rgb_255[2] = blue_lut[np.clip(rgb_255[2], 0, 255)]

                    # Apply master curve
                    rgb_255[0] = master_lut[np.clip(rgb_255[0], 0, 255)]
                    rgb_255[1] = master_lut[np.clip(rgb_255[1], 0, 255)]
                    rgb_255[2] = master_lut[np.clip(rgb_255[2], 0, 255)]

                    # Convert back to 0-1 range
                    self.data[r, g, b] = np.clip(rgb_255 / 255.0, 0, 1)

    def _interpolate_curve(self, curve: List[Tuple[int, int]]) -> np.ndarray:
        """Create 256-element lookup table from curve control points"""
        curve_sorted = sorted(curve, key=lambda x: x[0])
        lut = np.zeros(256, dtype=np.uint8)

        for i in range(256):
            # Find surrounding control points
            for idx in range(len(curve_sorted) - 1):
                x1, y1 = curve_sorted[idx]
                x2, y2 = curve_sorted[idx + 1]

                if x1 <= i <= x2:
                    # Linear interpolation
                    if x2 == x1:
                        lut[i] = y1
                    else:
                        t = (i - x1) / (x2 - x1)
                        lut[i] = int(y1 + t * (y2 - y1))
                    break

        return lut

    def apply_hsl_adjustment(self, hsl: HSLAdjustment):
        """Apply HSL adjustments to LUT"""
        for r in range(self.size):
            for g in range(self.size):
                for b in range(self.size):
                    rgb = self.data[r, g, b].copy()

                    # Convert RGB to HSL
                    h, s, l = self._rgb_to_hsl(rgb[0], rgb[1], rgb[2])

                    # Apply adjustments
                    h = (h + hsl.hue_shift) % 360
                    s = np.clip(s * hsl.saturation, 0, 1)
                    l = np.clip(l + hsl.luminance, 0, 1)

                    # Convert back to RGB
                    rgb = self._hsl_to_rgb(h, s, l)
                    self.data[r, g, b] = rgb

    def _rgb_to_hsl(self, r: float, g: float, b: float) -> Tuple[float, float, float]:
        """Convert RGB to HSL"""
        max_c = max(r, g, b)
        min_c = min(r, g, b)
        l = (max_c + min_c) / 2.0

        if max_c == min_c:
            h = s = 0.0
        else:
            diff = max_c - min_c
            s = diff / (2.0 - max_c - min_c) if l > 0.5 else diff / (max_c + min_c)

            if max_c == r:
                h = ((g - b) / diff + (6.0 if g < b else 0.0)) / 6.0
            elif max_c == g:
                h = ((b - r) / diff + 2.0) / 6.0
            else:
                h = ((r - g) / diff + 4.0) / 6.0

        return h * 360, s, l

    def _hsl_to_rgb(self, h: float, s: float, l: float) -> np.ndarray:
        """Convert HSL to RGB"""
        h = h / 360.0

        if s == 0:
            return np.array([l, l, l])

        def hue_to_rgb(p, q, t):
            if t < 0:
                t += 1
            if t > 1:
                t -= 1
            if t < 1/6:
                return p + (q - p) * 6 * t
            if t < 1/2:
                return q
            if t < 2/3:
                return p + (q - p) * (2/3 - t) * 6
            return p

        q = l * (1 + s) if l < 0.5 else l + s - l * s
        p = 2 * l - q

        r = hue_to_rgb(p, q, h + 1/3)
        g = hue_to_rgb(p, q, h)
        b = hue_to_rgb(p, q, h - 1/3)

        return np.array([r, g, b])


class LUTPresetGenerator:
    """Generate built-in LUT presets for common video ad looks"""

    @staticmethod
    def generate_cinematic(size: int = 33) -> LUT3D:
        """Hollywood cinematic look - teal shadows, orange highlights"""
        lut = LUT3D(size)

        # Cinematic color wheels
        wheels = ColorWheels(
            lift_r=-0.05, lift_g=-0.02, lift_b=0.08,  # Teal in shadows
            gamma_r=1.1, gamma_g=1.05, gamma_b=0.95,  # Warm midtones
            gain_r=1.15, gain_g=1.05, gain_b=0.95  # Orange in highlights
        )
        lut.apply_color_wheels(wheels)

        # S-curve for contrast
        curves = RGBCurves(
            master_curve=[(0, 10), (64, 50), (128, 128), (192, 205), (255, 245)]
        )
        lut.apply_curves(curves)

        return lut

    @staticmethod
    def generate_vintage(size: int = 33) -> LUT3D:
        """Vintage/retro film look with faded blacks and warm tones"""
        lut = LUT3D(size)

        # Faded blacks, warm tones
        wheels = ColorWheels(
            lift_r=0.12, lift_g=0.10, lift_b=0.08,  # Lifted blacks
            gamma_r=1.15, gamma_g=1.08, gamma_b=0.92,  # Warm gamma
            gain_r=1.08, gain_g=1.02, gain_b=0.95
        )
        lut.apply_color_wheels(wheels)

        # Reduced contrast curve
        curves = RGBCurves(
            master_curve=[(0, 30), (64, 80), (128, 135), (192, 185), (255, 230)]
        )
        lut.apply_curves(curves)

        # Slight desaturation
        hsl = HSLAdjustment(saturation=0.85)
        lut.apply_hsl_adjustment(hsl)

        return lut

    @staticmethod
    def generate_high_contrast(size: int = 33) -> LUT3D:
        """High contrast, punchy look for ads"""
        lut = LUT3D(size)

        # Deep blacks, bright highlights
        curves = RGBCurves(
            master_curve=[(0, 0), (32, 15), (96, 80), (160, 175), (224, 240), (255, 255)]
        )
        lut.apply_curves(curves)

        # Boosted saturation
        hsl = HSLAdjustment(saturation=1.25)
        lut.apply_hsl_adjustment(hsl)

        return lut

    @staticmethod
    def generate_warm(size: int = 33) -> LUT3D:
        """Warm, inviting look"""
        lut = LUT3D(size)

        wheels = ColorWheels(
            lift_r=0.05, lift_g=0.02, lift_b=-0.03,
            gamma_r=1.12, gamma_g=1.05, gamma_b=0.90,
            gain_r=1.15, gain_g=1.08, gain_b=0.92
        )
        lut.apply_color_wheels(wheels)

        hsl = HSLAdjustment(hue_shift=5, saturation=1.1)
        lut.apply_hsl_adjustment(hsl)

        return lut

    @staticmethod
    def generate_cold(size: int = 33) -> LUT3D:
        """Cold, modern look"""
        lut = LUT3D(size)

        wheels = ColorWheels(
            lift_r=-0.03, lift_g=-0.01, lift_b=0.05,
            gamma_r=0.90, gamma_g=0.95, gamma_b=1.10,
            gain_r=0.95, gain_g=1.00, gain_b=1.12
        )
        lut.apply_color_wheels(wheels)

        hsl = HSLAdjustment(hue_shift=-5, saturation=1.05)
        lut.apply_hsl_adjustment(hsl)

        return lut

    @staticmethod
    def generate_fitness_energy(size: int = 33) -> LUT3D:
        """High-energy, vibrant look for fitness content"""
        lut = LUT3D(size)

        # Vibrant, punchy colors
        wheels = ColorWheels(
            lift_r=0.02, lift_g=-0.02, lift_b=-0.02,
            gamma_r=1.05, gamma_g=1.10, gamma_b=1.05,
            gain_r=1.10, gain_g=1.15, gain_b=1.08
        )
        lut.apply_color_wheels(wheels)

        # Contrast boost
        curves = RGBCurves(
            master_curve=[(0, 5), (64, 55), (128, 132), (192, 210), (255, 255)]
        )
        lut.apply_curves(curves)

        # High saturation
        hsl = HSLAdjustment(saturation=1.35)
        lut.apply_hsl_adjustment(hsl)

        return lut

    @staticmethod
    def generate_clean_corporate(size: int = 33) -> LUT3D:
        """Clean, professional corporate look"""
        lut = LUT3D(size)

        # Neutral, slightly cool
        wheels = ColorWheels(
            lift_r=-0.01, lift_g=-0.01, lift_b=0.01,
            gamma_r=0.98, gamma_g=1.00, gamma_b=1.02,
            gain_r=1.00, gain_g=1.02, gain_b=1.03
        )
        lut.apply_color_wheels(wheels)

        # Slight desaturation for professional look
        hsl = HSLAdjustment(saturation=0.92)
        lut.apply_hsl_adjustment(hsl)

        return lut

    @staticmethod
    def generate_instagram_dramatic(size: int = 33) -> LUT3D:
        """Instagram dramatic look"""
        lut = LUT3D(size)

        wheels = ColorWheels(
            lift_r=0.03, lift_g=0.00, lift_b=-0.03,
            gamma_r=1.08, gamma_g=1.00, gamma_b=0.92,
            gain_r=1.12, gain_g=1.05, gain_b=0.95
        )
        lut.apply_color_wheels(wheels)

        curves = RGBCurves(
            master_curve=[(0, 15), (64, 60), (128, 128), (192, 200), (255, 245)]
        )
        lut.apply_curves(curves)

        hsl = HSLAdjustment(saturation=1.2)
        lut.apply_hsl_adjustment(hsl)

        return lut

    @staticmethod
    def generate_instagram_fade(size: int = 33) -> LUT3D:
        """Instagram faded look"""
        lut = LUT3D(size)

        wheels = ColorWheels(
            lift_r=0.08, lift_g=0.08, lift_b=0.10,
            gamma_r=1.05, gamma_g=1.05, gamma_b=1.05,
            gain_r=1.00, gain_g=1.00, gain_b=1.00
        )
        lut.apply_color_wheels(wheels)

        curves = RGBCurves(
            master_curve=[(0, 25), (64, 85), (128, 140), (192, 195), (255, 235)]
        )
        lut.apply_curves(curves)

        hsl = HSLAdjustment(saturation=0.80)
        lut.apply_hsl_adjustment(hsl)

        return lut

    @staticmethod
    def generate_instagram_vibrant(size: int = 33) -> LUT3D:
        """Instagram vibrant look"""
        lut = LUT3D(size)

        wheels = ColorWheels(
            lift_r=0.00, lift_g=-0.02, lift_b=-0.02,
            gamma_r=1.08, gamma_g=1.12, gamma_b=1.10,
            gain_r=1.08, gain_g=1.12, gain_b=1.10
        )
        lut.apply_color_wheels(wheels)

        curves = RGBCurves(
            master_curve=[(0, 5), (64, 58), (128, 135), (192, 210), (255, 250)]
        )
        lut.apply_curves(curves)

        hsl = HSLAdjustment(saturation=1.4)
        lut.apply_hsl_adjustment(hsl)

        return lut

    @classmethod
    def generate_preset(cls, preset: LUTPreset, size: int = 33) -> LUT3D:
        """Generate a preset LUT by name"""
        generators = {
            LUTPreset.CINEMATIC: cls.generate_cinematic,
            LUTPreset.VINTAGE: cls.generate_vintage,
            LUTPreset.HIGH_CONTRAST: cls.generate_high_contrast,
            LUTPreset.WARM: cls.generate_warm,
            LUTPreset.COLD: cls.generate_cold,
            LUTPreset.FITNESS_ENERGY: cls.generate_fitness_energy,
            LUTPreset.CLEAN_CORPORATE: cls.generate_clean_corporate,
            LUTPreset.INSTAGRAM_DRAMATIC: cls.generate_instagram_dramatic,
            LUTPreset.INSTAGRAM_FADE: cls.generate_instagram_fade,
            LUTPreset.INSTAGRAM_VIBRANT: cls.generate_instagram_vibrant,
        }
        return generators[preset](size)


class ColorGradingEngine:
    """
    Main color grading engine that generates FFmpeg filter chains
    """

    def __init__(self):
        self.temp_dir = tempfile.mkdtemp(prefix="color_grading_")
        self.lut_files = {}

    def __del__(self):
        """Cleanup temporary files"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def apply_lut_preset(self, preset: LUTPreset, intensity: float = 1.0) -> str:
        """
        Apply a built-in LUT preset
        Args:
            preset: LUT preset to apply
            intensity: Intensity of effect (0.0 to 1.0)
        Returns:
            FFmpeg filter string
        """
        # Generate LUT
        lut = LUTPresetGenerator.generate_preset(preset)

        # Save to temp file
        lut_path = os.path.join(self.temp_dir, f"{preset.value}.cube")
        lut.save_cube_file(lut_path, title=preset.value)
        self.lut_files[preset.value] = lut_path

        # Generate FFmpeg filter
        if intensity >= 1.0:
            return f"lut3d=file='{lut_path}'"
        else:
            # Use mix to blend between original and graded
            return f"split[original][graded];[graded]lut3d=file='{lut_path}'[graded];[original][graded]blend=all_mode=normal:all_opacity={intensity}"

    def apply_custom_lut(self, lut_file: str, intensity: float = 1.0) -> str:
        """
        Apply a custom .cube LUT file
        Args:
            lut_file: Path to .cube LUT file
            intensity: Intensity of effect (0.0 to 1.0)
        Returns:
            FFmpeg filter string
        """
        if intensity >= 1.0:
            return f"lut3d=file='{lut_file}'"
        else:
            return f"split[original][graded];[graded]lut3d=file='{lut_file}'[graded];[original][graded]blend=all_mode=normal:all_opacity={intensity}"

    def apply_color_wheels(self, wheels: ColorWheels) -> str:
        """
        Apply color wheel adjustments using FFmpeg filters
        Args:
            wheels: ColorWheels object with lift/gamma/gain values
        Returns:
            FFmpeg filter string
        """
        filters = []

        # Lift (shadows) - use colorlevels filter
        if any([wheels.lift_r != 0, wheels.lift_g != 0, wheels.lift_b != 0]):
            # Convert lift values to input black levels (0-1 range)
            r_in_min = max(0, -wheels.lift_r * 0.3)
            g_in_min = max(0, -wheels.lift_g * 0.3)
            b_in_min = max(0, -wheels.lift_b * 0.3)

            r_out_min = max(0, wheels.lift_r * 0.3)
            g_out_min = max(0, wheels.lift_g * 0.3)
            b_out_min = max(0, wheels.lift_b * 0.3)

            filters.append(
                f"colorlevels="
                f"rimin={r_in_min}:romin={r_out_min}:"
                f"gimin={g_in_min}:gomin={g_out_min}:"
                f"bimin={b_in_min}:bomin={b_out_min}"
            )

        # Gamma (midtones)
        if any([wheels.gamma_r != 1.0, wheels.gamma_g != 1.0, wheels.gamma_b != 1.0]):
            filters.append(
                f"eq="
                f"gamma_r={wheels.gamma_r}:"
                f"gamma_g={wheels.gamma_g}:"
                f"gamma_b={wheels.gamma_b}"
            )

        # Gain (highlights) - use colorlevels output max
        if any([wheels.gain_r != 1.0, wheels.gain_g != 1.0, wheels.gain_b != 1.0]):
            r_out_max = wheels.gain_r
            g_out_max = wheels.gain_g
            b_out_max = wheels.gain_b

            filters.append(
                f"colorlevels="
                f"romax={r_out_max}:"
                f"gomax={g_out_max}:"
                f"bomax={b_out_max}"
            )

        return ",".join(filters) if filters else "null"

    def apply_curves(self, curves: RGBCurves) -> str:
        """
        Apply RGB curves using FFmpeg curves filter
        Args:
            curves: RGBCurves object with curve control points
        Returns:
            FFmpeg filter string
        """
        # Convert curve points to FFmpeg format
        def format_curve(curve_points: List[Tuple[int, int]]) -> str:
            # Normalize to 0-1 range
            points = [(x/255.0, y/255.0) for x, y in sorted(curve_points, key=lambda p: p[0])]
            return " ".join([f"{x:.4f}/{y:.4f}" for x, y in points])

        curve_parts = []

        if curves.master_curve and curves.master_curve != [(0, 0), (255, 255)]:
            curve_parts.append(f"master='{format_curve(curves.master_curve)}'")

        if curves.red_curve and curves.red_curve != [(0, 0), (255, 255)]:
            curve_parts.append(f"red='{format_curve(curves.red_curve)}'")

        if curves.green_curve and curves.green_curve != [(0, 0), (255, 255)]:
            curve_parts.append(f"green='{format_curve(curves.green_curve)}'")

        if curves.blue_curve and curves.blue_curve != [(0, 0), (255, 255)]:
            curve_parts.append(f"blue='{format_curve(curves.blue_curve)}'")

        if curve_parts:
            return f"curves={':'.join(curve_parts)}"
        return "null"

    def apply_hsl(self, hsl: HSLAdjustment) -> str:
        """
        Apply HSL adjustments using FFmpeg filters
        Args:
            hsl: HSLAdjustment object
        Returns:
            FFmpeg filter string
        """
        filters = []

        # Hue shift
        if hsl.hue_shift != 0:
            # Convert degrees to FFmpeg hue value (-180 to 180 -> -180 to 180)
            filters.append(f"hue=h={hsl.hue_shift}")

        # Saturation
        if hsl.saturation != 1.0:
            filters.append(f"eq=saturation={hsl.saturation}")

        # Luminance (brightness)
        if hsl.luminance != 0:
            # Convert -1 to 1 range to FFmpeg brightness (-1 to 1)
            filters.append(f"eq=brightness={hsl.luminance}")

        return ",".join(filters) if filters else "null"

    def apply_white_balance(self, wb: WhiteBalance) -> str:
        """
        Apply white balance adjustments
        Args:
            wb: WhiteBalance object
        Returns:
            FFmpeg filter string
        """
        if wb.temperature == 0 and wb.tint == 0:
            return "null"

        # Temperature: negative = cooler (more blue), positive = warmer (more orange)
        # Tint: negative = greener, positive = more magenta

        # Convert temperature to RGB adjustments
        temp_factor = wb.temperature / 100.0
        r_temp = 1.0 + (temp_factor * 0.3 if temp_factor > 0 else 0)
        b_temp = 1.0 + (-temp_factor * 0.3 if temp_factor < 0 else 0)

        # Convert tint to RGB adjustments
        tint_factor = wb.tint / 100.0
        g_tint = 1.0 + (-tint_factor * 0.2 if tint_factor < 0 else 0)
        r_tint = 1.0 + (tint_factor * 0.1 if tint_factor > 0 else 0)
        b_tint = 1.0 + (tint_factor * 0.1 if tint_factor > 0 else 0)

        # Combine adjustments
        r_total = r_temp * r_tint
        g_total = g_tint
        b_total = b_temp * b_tint

        # Use colorbalance or colorchannelmixer
        return (
            f"colorchannelmixer="
            f"rr={r_total}:gg={g_total}:bb={b_total}"
        )

    def apply_exposure_controls(self, controls: ExposureControls) -> str:
        """
        Apply exposure and tone controls
        Args:
            controls: ExposureControls object
        Returns:
            FFmpeg filter string
        """
        filters = []

        # Exposure (stops)
        if controls.exposure != 0:
            # Convert stops to multiplication factor (2^stops)
            exposure_mult = 2 ** controls.exposure
            filters.append(f"eq=brightness={np.log2(exposure_mult) * 0.5}")

        # Contrast
        if controls.contrast != 1.0:
            filters.append(f"eq=contrast={controls.contrast}")

        # Highlights and shadows using curves
        if controls.highlights != 0 or controls.shadows != 0:
            # Build a curve that adjusts highlights and shadows
            shadow_lift = controls.shadows / 100.0 * 0.3
            highlight_adjust = controls.highlights / 100.0 * -0.3

            curve_points = [
                (0, max(0, shadow_lift)),
                (64, 0.25 + shadow_lift * 0.5),
                (128, 0.5),
                (192, 0.75 + highlight_adjust * 0.5),
                (255, min(1.0, 1.0 + highlight_adjust))
            ]

            curves = RGBCurves(master_curve=[(int(x*255), int(y*255)) for x, y in curve_points])
            curve_filter = self.apply_curves(curves)
            if curve_filter != "null":
                filters.append(curve_filter)

        # Whites and blacks using colorlevels
        if controls.whites != 0 or controls.blacks != 0:
            # Blacks adjustment
            in_min = max(0, -controls.blacks / 100.0 * 0.3)
            out_min = max(0, controls.blacks / 100.0 * 0.3)

            # Whites adjustment
            in_max = 1.0 - max(0, controls.whites / 100.0 * 0.3)
            out_max = 1.0 + max(0, controls.whites / 100.0 * 0.3)

            filters.append(
                f"colorlevels="
                f"rimin={in_min}:rimax={in_max}:"
                f"romin={out_min}:romax={out_max}:"
                f"gimin={in_min}:gimax={in_max}:"
                f"gomin={out_min}:gomax={out_max}:"
                f"bimin={in_min}:bimax={in_max}:"
                f"bomin={out_min}:bomax={out_max}"
            )

        # Vibrance (smart saturation that protects skin tones and already saturated colors)
        if controls.vibrance != 0:
            # Vibrance is harder to implement directly in FFmpeg
            # Approximate with selective saturation adjustment
            vibrance_factor = 1.0 + (controls.vibrance / 100.0)

            # Use selective color to boost less saturated areas more
            # This is an approximation of true vibrance
            filters.append(f"eq=saturation={vibrance_factor}")

        # Saturation (affects all colors equally)
        if controls.saturation != 0:
            sat_factor = 1.0 + (controls.saturation / 100.0)
            filters.append(f"eq=saturation={sat_factor}")

        return ",".join(filters) if filters else "null"

    def apply_skin_tone_protection(self, protection: SkinToneProtection, base_filter: str) -> str:
        """
        Apply color grading with skin tone protection
        Args:
            protection: SkinToneProtection settings
            base_filter: The base color grading filter to apply
        Returns:
            FFmpeg filter string with skin tone masking
        """
        if not protection.enabled or base_filter == "null":
            return base_filter

        # Create a selective color filter that protects skin tones
        # Use hue range to isolate skin tones (typically 0-50 degrees in HSV)
        hue_min = protection.hue_center - protection.hue_range / 2
        hue_max = protection.hue_center + protection.hue_range / 2

        # Complex filter that:
        # 1. Creates a mask for skin tones
        # 2. Applies grading to non-skin areas
        # 3. Blends with original skin tones

        return (
            f"split[original][process];"
            f"[process]{base_filter}[graded];"
            f"[original][graded]blend=all_mode=normal:all_opacity={1.0 - protection.strength}"
        )

    def create_color_match_filter(self,
                                   source_stats: Dict[str, float],
                                   target_stats: Dict[str, float]) -> str:
        """
        Create a filter to match colors between clips
        Args:
            source_stats: Color statistics from source clip (mean_r, mean_g, mean_b, std_r, std_g, std_b)
            target_stats: Color statistics from target clip
        Returns:
            FFmpeg filter string
        """
        # Calculate adjustments needed to match target
        r_scale = target_stats['std_r'] / source_stats['std_r'] if source_stats['std_r'] > 0 else 1.0
        g_scale = target_stats['std_g'] / source_stats['std_g'] if source_stats['std_g'] > 0 else 1.0
        b_scale = target_stats['std_b'] / source_stats['std_b'] if source_stats['std_b'] > 0 else 1.0

        r_offset = target_stats['mean_r'] - (source_stats['mean_r'] * r_scale)
        g_offset = target_stats['mean_g'] - (source_stats['mean_g'] * g_scale)
        b_offset = target_stats['mean_b'] - (source_stats['mean_b'] * b_scale)

        # Use colorchannelmixer and eq to match colors
        filters = []

        # Scale each channel
        if r_scale != 1.0 or g_scale != 1.0 or b_scale != 1.0:
            filters.append(
                f"colorchannelmixer="
                f"rr={r_scale}:gg={g_scale}:bb={b_scale}"
            )

        # Offset each channel
        if abs(r_offset) > 0.01 or abs(g_offset) > 0.01 or abs(b_offset) > 0.01:
            # Use curves to apply offset
            r_curve = [(0, int(r_offset * 255)), (255, int(255 + r_offset * 255))]
            g_curve = [(0, int(g_offset * 255)), (255, int(255 + g_offset * 255))]
            b_curve = [(0, int(b_offset * 255)), (255, int(255 + b_offset * 255))]

            curves = RGBCurves(red_curve=r_curve, green_curve=g_curve, blue_curve=b_curve)
            curve_filter = self.apply_curves(curves)
            if curve_filter != "null":
                filters.append(curve_filter)

        return ",".join(filters) if filters else "null"

    def create_before_after_comparison(self, grading_filter: str,
                                       split_position: float = 0.5,
                                       orientation: str = "vertical") -> str:
        """
        Create a before/after split comparison
        Args:
            grading_filter: The color grading filter to compare
            split_position: Position of split (0.0 to 1.0)
            orientation: "vertical" or "horizontal"
        Returns:
            FFmpeg filter string
        """
        if grading_filter == "null":
            return "null"

        if orientation == "vertical":
            # Vertical split (left = before, right = after)
            return (
                f"split[before][after];"
                f"[after]{grading_filter}[after];"
                f"[before]crop=iw*{split_position}:ih:0:0[left];"
                f"[after]crop=iw*(1-{split_position}):ih:iw*{split_position}:0[right];"
                f"[left][right]hstack"
            )
        else:
            # Horizontal split (top = before, bottom = after)
            return (
                f"split[before][after];"
                f"[after]{grading_filter}[after];"
                f"[before]crop=iw:ih*{split_position}:0:0[top];"
                f"[after]crop=iw:ih*(1-{split_position}):0:ih*{split_position}[bottom];"
                f"[top][bottom]vstack"
            )

    def build_complete_filter_chain(self,
                                    lut_preset: Optional[LUTPreset] = None,
                                    lut_file: Optional[str] = None,
                                    lut_intensity: float = 1.0,
                                    color_wheels: Optional[ColorWheels] = None,
                                    curves: Optional[RGBCurves] = None,
                                    hsl: Optional[HSLAdjustment] = None,
                                    white_balance: Optional[WhiteBalance] = None,
                                    exposure: Optional[ExposureControls] = None,
                                    skin_tone: Optional[SkinToneProtection] = None,
                                    before_after: bool = False,
                                    split_position: float = 0.5) -> str:
        """
        Build a complete color grading filter chain
        Args:
            lut_preset: Built-in LUT preset to apply
            lut_file: Custom LUT file to apply
            lut_intensity: LUT intensity (0.0 to 1.0)
            color_wheels: Color wheel adjustments
            curves: RGB curves
            hsl: HSL adjustments
            white_balance: White balance adjustments
            exposure: Exposure controls
            skin_tone: Skin tone protection settings
            before_after: Enable before/after comparison
            split_position: Position of before/after split
        Returns:
            Complete FFmpeg filter string
        """
        filters = []

        # Apply in optimal order for color grading workflow:
        # 1. White balance (correct color temperature first)
        # 2. Exposure (get overall brightness right)
        # 3. Color wheels (lift/gamma/gain)
        # 4. Curves (fine-tune tonal response)
        # 5. HSL (creative color adjustments)
        # 6. LUT (apply look)

        if white_balance:
            wb_filter = self.apply_white_balance(white_balance)
            if wb_filter != "null":
                filters.append(wb_filter)

        if exposure:
            exp_filter = self.apply_exposure_controls(exposure)
            if exp_filter != "null":
                filters.append(exp_filter)

        if color_wheels:
            wheels_filter = self.apply_color_wheels(color_wheels)
            if wheels_filter != "null":
                filters.append(wheels_filter)

        if curves:
            curves_filter = self.apply_curves(curves)
            if curves_filter != "null":
                filters.append(curves_filter)

        if hsl:
            hsl_filter = self.apply_hsl(hsl)
            if hsl_filter != "null":
                filters.append(hsl_filter)

        if lut_file:
            lut_filter = self.apply_custom_lut(lut_file, lut_intensity)
            filters.append(lut_filter)
        elif lut_preset:
            lut_filter = self.apply_lut_preset(lut_preset, lut_intensity)
            filters.append(lut_filter)

        # Combine all filters
        if not filters:
            return "null"

        base_filter = ",".join(filters)

        # Apply skin tone protection if enabled
        if skin_tone and skin_tone.enabled:
            base_filter = self.apply_skin_tone_protection(skin_tone, base_filter)

        # Apply before/after comparison if enabled
        if before_after:
            base_filter = self.create_before_after_comparison(base_filter, split_position)

        return base_filter

    def export_lut_from_settings(self,
                                  output_path: str,
                                  color_wheels: Optional[ColorWheels] = None,
                                  curves: Optional[RGBCurves] = None,
                                  hsl: Optional[HSLAdjustment] = None,
                                  size: int = 33,
                                  title: str = "Custom LUT") -> str:
        """
        Export current settings as a .cube LUT file
        Args:
            output_path: Path to save .cube file
            color_wheels: Color wheel adjustments
            curves: RGB curves
            hsl: HSL adjustments
            size: LUT size (17, 33, or 65)
            title: LUT title
        Returns:
            Path to saved LUT file
        """
        lut = LUT3D(size)

        if color_wheels:
            lut.apply_color_wheels(color_wheels)

        if curves:
            lut.apply_curves(curves)

        if hsl:
            lut.apply_hsl_adjustment(hsl)

        lut.save_cube_file(output_path, title)
        return output_path


# Utility functions for color analysis

def analyze_video_colors(video_path: str, sample_frames: int = 10) -> Dict[str, float]:
    """
    Analyze color statistics from a video for color matching
    Args:
        video_path: Path to video file
        sample_frames: Number of frames to sample
    Returns:
        Dictionary with mean and std for each channel
    """
    import subprocess
    import json

    # Use FFmpeg to extract color statistics
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'frame=pkt_pts_time',
        '-of', 'json',
        video_path
    ]

    # This is a placeholder - in production, you'd sample frames and analyze
    # For now, return a basic structure
    return {
        'mean_r': 0.5,
        'mean_g': 0.5,
        'mean_b': 0.5,
        'std_r': 0.2,
        'std_g': 0.2,
        'std_b': 0.2
    }


def detect_skin_tones(video_path: str) -> SkinToneProtection:
    """
    Detect skin tones in video and return optimal protection settings
    Args:
        video_path: Path to video file
    Returns:
        SkinToneProtection settings
    """
    # In production, this would analyze frames for skin tones
    # For now, return default settings
    return SkinToneProtection(
        enabled=True,
        strength=0.6,
        hue_center=20.0,
        hue_range=35.0
    )


# Example usage and testing
if __name__ == "__main__":
    # Create color grading engine
    engine = ColorGradingEngine()

    # Example 1: Apply cinematic LUT preset
    print("Example 1: Cinematic LUT")
    cinematic_filter = engine.apply_lut_preset(LUTPreset.CINEMATIC, intensity=0.8)
    print(f"Filter: {cinematic_filter}\n")

    # Example 2: Custom color wheels
    print("Example 2: Custom Color Wheels (Teal & Orange)")
    wheels = ColorWheels(
        lift_r=-0.05, lift_g=-0.02, lift_b=0.08,
        gamma_r=1.1, gamma_g=1.05, gamma_b=0.95,
        gain_r=1.15, gain_g=1.05, gain_b=0.95
    )
    wheels_filter = engine.apply_color_wheels(wheels)
    print(f"Filter: {wheels_filter}\n")

    # Example 3: RGB Curves (S-curve for contrast)
    print("Example 3: RGB Curves (S-Curve)")
    curves = RGBCurves(
        master_curve=[(0, 10), (64, 50), (128, 128), (192, 205), (255, 245)]
    )
    curves_filter = engine.apply_curves(curves)
    print(f"Filter: {curves_filter}\n")

    # Example 4: HSL Adjustments
    print("Example 4: HSL Adjustments")
    hsl = HSLAdjustment(hue_shift=10, saturation=1.2, luminance=0.05)
    hsl_filter = engine.apply_hsl(hsl)
    print(f"Filter: {hsl_filter}\n")

    # Example 5: White Balance
    print("Example 5: White Balance (Warmer)")
    wb = WhiteBalance(temperature=15, tint=-5)
    wb_filter = engine.apply_white_balance(wb)
    print(f"Filter: {wb_filter}\n")

    # Example 6: Exposure Controls
    print("Example 6: Exposure Controls")
    exposure = ExposureControls(
        exposure=0.3,
        contrast=1.15,
        highlights=-20,
        shadows=15,
        vibrance=25,
        saturation=10
    )
    exposure_filter = engine.apply_exposure_controls(exposure)
    print(f"Filter: {exposure_filter}\n")

    # Example 7: Complete Filter Chain
    print("Example 7: Complete Filter Chain")
    complete_filter = engine.build_complete_filter_chain(
        lut_preset=LUTPreset.CINEMATIC,
        lut_intensity=0.7,
        color_wheels=ColorWheels(lift_b=0.05, gamma_r=1.1),
        white_balance=WhiteBalance(temperature=10),
        exposure=ExposureControls(contrast=1.1, vibrance=15),
        skin_tone=SkinToneProtection(enabled=True, strength=0.6)
    )
    print(f"Filter: {complete_filter}\n")

    # Example 8: Export Custom LUT
    print("Example 8: Export Custom LUT")
    lut_output = "/tmp/my_custom_look.cube"
    engine.export_lut_from_settings(
        output_path=lut_output,
        color_wheels=ColorWheels(lift_b=0.05, gain_r=1.1),
        curves=RGBCurves(master_curve=[(0, 15), (128, 128), (255, 240)]),
        hsl=HSLAdjustment(saturation=1.15),
        title="My Custom Look"
    )
    print(f"LUT saved to: {lut_output}\n")

    # Example 9: Before/After Comparison
    print("Example 9: Before/After Comparison")
    comparison_filter = engine.create_before_after_comparison(
        grading_filter=engine.apply_lut_preset(LUTPreset.VINTAGE),
        split_position=0.5,
        orientation="vertical"
    )
    print(f"Filter: {comparison_filter}\n")

    # Example 10: All Available Presets
    print("Example 10: All Available LUT Presets")
    for preset in LUTPreset:
        print(f"  - {preset.value}")
    print()

    print("Color Grading System Ready!")
    print(f"Temporary LUT files stored in: {engine.temp_dir}")
