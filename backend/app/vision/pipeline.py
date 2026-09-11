from __future__ import annotations

import math
import time
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter, ImageStat


ANALYZER_NAME = "shot_dna_classical"
ANALYZER_VERSION = "1.1.0"


def _rounded(value: float) -> float:
    return round(float(value), 4)


def _percentile(histogram: list[int], fraction: float) -> int:
    target, total = sum(histogram) * fraction, 0
    for value, count in enumerate(histogram):
        total += count
        if total >= target:
            return value
    return 255


def _palette(image: Image.Image) -> list[dict]:
    quantized = image.resize((96, 96)).quantize(colors=5, method=Image.Quantize.MEDIANCUT)
    colors, values = quantized.getcolors() or [], quantized.getpalette() or []
    total = sum(count for count, _ in colors) or 1
    return [
        {
            "hex": "#" + "".join(f"{channel:02x}" for channel in values[index * 3:index * 3 + 3]),
            "weight": _rounded(count / total),
        }
        for count, index in sorted(colors, reverse=True)[:5]
    ]


def analyze_image(path: Path) -> dict:
    started = time.perf_counter()
    with Image.open(path) as source:
        image = source.convert("RGB")
        width, height = image.size
        sample = image.copy()
        sample.thumbnail((512, 512))
        rgb_stat = ImageStat.Stat(sample)
        mean_rgb = [round(channel, 2) for channel in rgb_stat.mean]
        hsv_stat = ImageStat.Stat(sample.convert("HSV"))
        gray = sample.convert("L")
        gray_stat, histogram = ImageStat.Stat(gray), gray.histogram()
        brightness = gray_stat.mean[0] / 255
        pixels = max(1, sample.width * sample.height)

        half_width = gray.width // 2
        left = gray.crop((0, 0, half_width, gray.height))
        right = gray.crop((gray.width - half_width, 0, gray.width, gray.height)).transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        symmetry = 1 - ImageStat.Stat(ImageChops.difference(left, right)).mean[0] / 255
        edge_stat = ImageStat.Stat(gray.filter(ImageFilter.FIND_EDGES))
        horizontal_energy = ImageStat.Stat(ImageChops.difference(gray, ImageChops.offset(gray, 1, 0))).mean[0]
        vertical_energy = ImageStat.Stat(ImageChops.difference(gray, ImageChops.offset(gray, 0, 1))).mean[0]
        energy_total = horizontal_energy + vertical_energy
        orientation_confidence = abs(horizontal_energy - vertical_energy) / energy_total if energy_total else 0
        orientation = "vertical" if horizontal_energy > vertical_energy else "horizontal"

        compact = gray.resize((64, 64))
        weighted_x = weighted_y = luminance_sum = 0.0
        for index, value in enumerate(compact.getdata()):
            weighted_x += (index % 64) * value
            weighted_y += (index // 64) * value
            luminance_sum += value
        visual_x = weighted_x / luminance_sum / 63 if luminance_sum else 0.5
        visual_y = weighted_y / luminance_sum / 63 if luminance_sum else 0.5

        results = {
            "dimensions": {"width": width, "height": height, "aspect_ratio": _rounded(width / height)},
            "color": {
                "average_rgb": mean_rgb,
                "saturation": _rounded(hsv_stat.mean[1] / 255),
                "palette": _palette(sample),
                "temperature_bias": _rounded((mean_rgb[0] - mean_rgb[2]) / 255),
            },
            "luminance": {
                "brightness": _rounded(brightness),
                "contrast": _rounded(gray_stat.stddev[0] / 127.5),
                "p10": _percentile(histogram, 0.1),
                "p50": _percentile(histogram, 0.5),
                "p90": _percentile(histogram, 0.9),
                "shadows": _rounded(sum(histogram[:64]) / pixels),
                "highlights": _rounded(sum(histogram[192:]) / pixels),
            },
            "composition": {
                "edge_density": _rounded(edge_stat.mean[0] / 255),
                "symmetry": _rounded(max(0, symmetry)),
                "visual_center": {"x": _rounded(visual_x), "y": _rounded(visual_y)},
                "nearest_third_distance": _rounded(min(math.dist((visual_x, visual_y), point) for point in ((1/3, 1/3), (2/3, 1/3), (1/3, 2/3), (2/3, 2/3)))),
            },
            "quality": {
                "sharpness": _rounded(edge_stat.var[0]),
                "underexposed": brightness < 0.12,
                "overexposed": brightness > 0.9,
            },
            "estimates": {
                "dominant_line_orientation": {"value": orientation if orientation_confidence >= 0.08 else "unknown", "confidence": _rounded(orientation_confidence), "method": "directional_pixel_gradient"},
                "horizon_roll": {"value": "unknown", "confidence": 0.0, "method": "insufficient_geometric_evidence"},
                "shot_scale": {"value": "unknown", "confidence": 0.0, "method": "no_reliable_subject_detected"},
                "camera_elevation": {"value": "unknown", "confidence": 0.0, "method": "insufficient_geometric_evidence"},
            },
        }
    return {"results": results, "execution_ms": round((time.perf_counter() - started) * 1000, 2)}
