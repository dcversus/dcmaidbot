"""
Test utilities for E2E widget tile testing

This module provides utility functions for:
- Image comparison and visual regression testing
- Screenshot management
- Color analysis
- Performance measurement
- Test data generation
"""

import hashlib
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from PIL import Image, ImageChops, ImageDraw


@dataclass
class TestScreenshot:
    """Metadata for a test screenshot"""

    name: str
    path: Path
    timestamp: float
    test_name: str
    widget_id: Optional[str] = None
    state: Optional[str] = None  # 'hover', 'click', 'idle', etc.
    description: Optional[str] = None
    dimensions: Optional[Tuple[int, int]] = None
    file_hash: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


@dataclass
class ImageComparisonResult:
    """Result of image comparison"""

    similarity_score: float  # 0.0 = identical, 1.0 = completely different
    difference_pixels: int
    total_pixels: int
    difference_percentage: float
    is_acceptable: bool
    comparison_method: str
    metadata: Dict[str, Any]


class ScreenshotManager:
    """Manages test screenshots with metadata"""

    def __init__(self, base_dir: Path = None):
        self.base_dir = base_dir or Path("test_screenshots")
        self.base_dir.mkdir(exist_ok=True)
        self.metadata_file = self.base_dir / "screenshots.json"
        self.screenshots: Dict[str, TestScreenshot] = {}
        self.load_metadata()

    def load_metadata(self):
        """Load screenshot metadata from JSON file"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, "r") as f:
                    data = json.load(f)
                    for name, screenshot_data in data.items():
                        screenshot = TestScreenshot(**screenshot_data)
                        screenshot.path = Path(screenshot.path)
                        self.screenshots[name] = screenshot
            except Exception as e:
                print(f"Warning: Could not load screenshot metadata: {e}")

    def save_metadata(self):
        """Save screenshot metadata to JSON file"""
        try:
            data = {
                name: screenshot.to_dict()
                for name, screenshot in self.screenshots.items()
            }
            with open(self.metadata_file, "w") as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"Warning: Could not save screenshot metadata: {e}")

    def add_screenshot(
        self,
        name: str,
        path: Path,
        test_name: str,
        widget_id: str = None,
        state: str = None,
        description: str = None,
    ) -> TestScreenshot:
        """Add a screenshot with metadata"""
        # Get image dimensions
        dimensions = None
        file_hash = None
        if path.exists():
            with Image.open(path) as img:
                dimensions = img.size
            # Calculate file hash
            with open(path, "rb") as f:
                file_hash = hashlib.md5(f.read()).hexdigest()

        screenshot = TestScreenshot(
            name=name,
            path=path,
            timestamp=time.time(),
            test_name=test_name,
            widget_id=widget_id,
            state=state,
            description=description,
            dimensions=dimensions,
            file_hash=file_hash,
        )

        self.screenshots[name] = screenshot
        self.save_metadata()
        return screenshot

    def get_screenshot(self, name: str) -> Optional[TestScreenshot]:
        """Get screenshot by name"""
        return self.screenshots.get(name)

    def find_screenshots(
        self, test_name: str = None, widget_id: str = None, state: str = None
    ) -> List[TestScreenshot]:
        """Find screenshots matching criteria"""
        results = []
        for screenshot in self.screenshots.values():
            if test_name and screenshot.test_name != test_name:
                continue
            if widget_id and screenshot.widget_id != widget_id:
                continue
            if state and screenshot.state != state:
                continue
            results.append(screenshot)
        return results


class ImageComparator:
    """Advanced image comparison for visual regression testing"""

    @staticmethod
    def calculate_ssim(img1: Image.Image, img2: Image.Image) -> float:
        """Calculate Structural Similarity Index (SSIM)"""
        # Convert to grayscale
        img1_gray = img1.convert("L")
        img2_gray = img2.convert("L")

        # Resize to same dimensions
        min_width = min(img1_gray.width, img2_gray.width)
        min_height = min(img1_gray.height, img2_gray.height)

        img1_resized = img1_gray.resize((min_width, min_height))
        img2_resized = img2_gray.resize((min_width, min_height))

        # Convert to numpy arrays
        img1_array = np.array(img1_resized, dtype=np.float64)
        img2_array = np.array(img2_resized, dtype=np.float64)

        # Calculate SSIM components
        mu1 = np.mean(img1_array)
        mu2 = np.mean(img2_array)

        sigma1_sq = np.var(img1_array)
        sigma2_sq = np.var(img2_array)
        sigma12 = np.mean((img1_array - mu1) * (img2_array - mu2))

        # SSIM constants
        c1 = (0.01 * 255) ** 2
        c2 = (0.03 * 255) ** 2

        # Calculate SSIM
        numerator = (2 * mu1 * mu2 + c1) * (2 * sigma12 + c2)
        denominator = (mu1**2 + mu2**2 + c1) * (sigma1_sq + sigma2_sq + c2)

        ssim = numerator / denominator
        return float(ssim)

    @staticmethod
    def calculate_mse(img1: Image.Image, img2: Image.Image) -> float:
        """Calculate Mean Squared Error between images"""
        # Convert to same size and format
        img1_resized = img1.resize((img2.width, img2.height))
        img1_rgb = img1_resized.convert("RGB")
        img2_rgb = img2.convert("RGB")

        # Convert to numpy arrays
        arr1 = np.array(img1_rgb, dtype=np.float64)
        arr2 = np.array(img2_rgb, dtype=np.float64)

        # Calculate MSE
        mse = np.mean((arr1 - arr2) ** 2)
        return float(mse)

    @staticmethod
    def create_difference_image(img1: Image.Image, img2: Image.Image) -> Image.Image:
        """Create a visual difference image"""
        # Convert to same size
        img1_resized = img1.resize((img2.width, img2.height))

        # Calculate difference
        diff = ImageChops.difference(img1_resized, img2)

        # Enhance differences for visibility
        diff_enhanced = ImageChops.multiply(diff, diff)

        return diff_enhanced

    @staticmethod
    def compare_images(
        img1_path: Path, img2_path: Path, threshold: float = 0.1
    ) -> ImageComparisonResult:
        """Compare two images with multiple metrics"""
        try:
            with Image.open(img1_path) as img1, Image.open(img2_path) as img2:
                # Calculate metrics
                ssim = ImageComparator.calculate_ssim(img1, img2)
                mse = ImageComparator.calculate_mse(img1, img2)

                # Convert SSIM to difference score (0 = identical, 1 = completely different)
                difference_score = 1.0 - ssim

                # Calculate pixel differences
                diff_img = ImageComparator.create_difference_image(img1, img2)
                diff_array = np.array(diff_img.convert("L"))
                diff_pixels = np.sum(
                    diff_array > 30
                )  # Threshold for "different" pixels
                total_pixels = diff_array.size
                diff_percentage = (diff_pixels / total_pixels) * 100

                # Determine if acceptable
                is_acceptable = (
                    difference_score < threshold and diff_percentage < 5.0
                )  # Less than 5% different pixels

                return ImageComparisonResult(
                    similarity_score=difference_score,
                    difference_pixels=diff_pixels,
                    total_pixels=total_pixels,
                    difference_percentage=diff_percentage,
                    is_acceptable=is_acceptable,
                    comparison_method="SSIM+MSE",
                    metadata={
                        "ssim": ssim,
                        "mse": mse,
                        "img1_size": img1.size,
                        "img2_size": img2.size,
                    },
                )
        except Exception as e:
            return ImageComparisonResult(
                similarity_score=1.0,  # Worst case
                difference_pixels=0,
                total_pixels=0,
                difference_percentage=100.0,
                is_acceptable=False,
                comparison_method="ERROR",
                metadata={"error": str(e)},
            )


class ColorAnalyzer:
    """Analyze colors in widget tiles for validation"""

    @staticmethod
    def get_dominant_colors(
        image_path: Path, num_colors: int = 5
    ) -> List[Tuple[int, int, int]]:
        """Get dominant colors from an image using k-means clustering"""
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                img_rgb = img.convert("RGB")

                # Resize for faster processing
                img_small = img_rgb.resize((150, 150))

                # Get pixel data
                pixels = np.array(img_small)
                pixels = pixels.reshape((-1, 3))

                # Use simple k-means (scikit-learn not available)
                # For now, return color quantization
                from sklearn.cluster import KMeans

                kmeans = KMeans(n_clusters=num_colors, random_state=42)
                kmeans.fit(pixels)

                colors = kmeans.cluster_centers_.astype(int)
                return [tuple(color) for color in colors]
        except ImportError:
            # Fallback: use PIL's quantize method
            with Image.open(image_path) as img:
                img_rgb = img.convert("RGB")
                img_quantized = img_rgb.quantize(colors=num_colors)
                palette = img_quantized.getpalette()
                colors = []
                for i in range(0, len(palette), 3):
                    if len(colors) >= num_colors:
                        break
                    colors.append((palette[i], palette[i + 1], palette[i + 2]))
                return colors
        except Exception as e:
            print(f"Error analyzing colors: {e}")
            return []

    @staticmethod
    def check_transparency(image_path: Path) -> Dict[str, Any]:
        """Check transparency properties of an image"""
        try:
            with Image.open(image_path) as img:
                if img.mode != "RGBA":
                    return {"has_transparency": False, "mode": img.mode}

                # Convert to numpy array
                img_array = np.array(img)
                alpha_channel = img_array[:, :, 3]

                # Calculate transparency statistics
                total_pixels = alpha_channel.size
                transparent_pixels = np.sum(alpha_channel == 0)
                semi_transparent_pixels = np.sum(
                    (alpha_channel > 0) & (alpha_channel < 255)
                )
                opaque_pixels = np.sum(alpha_channel == 255)

                return {
                    "has_transparency": True,
                    "mode": img.mode,
                    "total_pixels": total_pixels,
                    "transparent_pixels": transparent_pixels,
                    "semi_transparent_pixels": semi_transparent_pixels,
                    "opaque_pixels": opaque_pixels,
                    "transparency_percentage": (transparent_pixels / total_pixels)
                    * 100,
                    "semi_transparency_percentage": (
                        semi_transparent_pixels / total_pixels
                    )
                    * 100,
                }
        except Exception as e:
            return {"has_transparency": False, "error": str(e)}


class PerformanceProfiler:
    """Profile performance of tile operations"""

    def __init__(self):
        self.measurements: List[Dict[str, Any]] = []

    def start_measurement(self, name: str, metadata: Dict[str, Any] = None) -> str:
        """Start a performance measurement"""
        measurement_id = f"{name}_{time.time()}"
        measurement = {
            "id": measurement_id,
            "name": name,
            "start_time": time.time(),
            "end_time": None,
            "duration": None,
            "metadata": metadata or {},
        }
        self.measurements.append(measurement)
        return measurement_id

    def end_measurement(self, measurement_id: str) -> Optional[float]:
        """End a performance measurement and return duration"""
        for measurement in self.measurements:
            if measurement["id"] == measurement_id and measurement["end_time"] is None:
                measurement["end_time"] = time.time()
                measurement["duration"] = (
                    measurement["end_time"] - measurement["start_time"]
                )
                return measurement["duration"]
        return None

    def get_measurements(self, name: str = None) -> List[Dict[str, Any]]:
        """Get measurements, optionally filtered by name"""
        if name:
            return [m for m in self.measurements if m["name"] == name]
        return self.measurements

    def get_average_duration(self, name: str) -> Optional[float]:
        """Get average duration for a measurement name"""
        measurements = self.get_measurements(name)
        completed = [m for m in measurements if m["duration"] is not None]
        if completed:
            return sum(m["duration"] for m in completed) / len(completed)
        return None

    def export_report(self, output_path: Path) -> None:
        """Export performance report to JSON"""
        try:
            with open(output_path, "w") as f:
                json.dump(self.measurements, f, indent=2, default=str)
        except Exception as e:
            print(f"Error exporting performance report: {e}")


def create_test_widget_data(num_widgets: int = 5) -> Dict[str, Any]:
    """Create test widget data for testing"""
    return {
        "locations": [
            {
                "id": "test_location",
                "name": "Test Location",
                "description": "Automated test location",
                "scene": {
                    "base": "static/world/test_scene.png",
                    "tiles": {"idle": "static/world/test_scene.png"},
                },
                "widgets": [
                    {
                        "id": f"test_widget_{i}",
                        "name": f"Test Widget {i}",
                        "type": [
                            "poster",
                            "changelog_book",
                            "family_photo",
                            "clock",
                            "plant",
                        ][i % 5],
                        "position": {"x": 128 + (i * 64), "y": 128 + (i * 32)},
                        "size": {"width": 128, "height": 128},
                        "tiles": {
                            "hover": f"static/world/test_widget_{i}_hover.png",
                            "click": f"static/world/test_widget_{i}_click.png",
                        },
                        "interactions": {
                            "hover": f"Hover action for widget {i}",
                            "click": f"Click action for widget {i}",
                        },
                    }
                    for i in range(num_widgets)
                ],
            }
        ]
    }


def create_test_image(
    width: int,
    height: int,
    color: Tuple[int, int, int],
    alpha: int = 255,
    pattern: str = "solid",
) -> Image.Image:
    """Create a test image with specified parameters"""
    img = Image.new("RGBA", (width, height), color + (alpha,))

    if pattern == "checkerboard":
        draw = ImageDraw.Draw(img)
        square_size = 16
        for x in range(0, width, square_size * 2):
            for y in range(0, height, square_size * 2):
                draw.rectangle(
                    [x, y, x + square_size, y + square_size],
                    fill=(255, 255, 255, alpha),
                )
                draw.rectangle(
                    [
                        x + square_size,
                        y + square_size,
                        x + square_size * 2,
                        y + square_size * 2,
                    ],
                    fill=(255, 255, 255, alpha),
                )
    elif pattern == "gradient":
        # Create a simple gradient
        pixels = np.array(img)
        for y in range(height):
            alpha_value = int(alpha * (1 - y / height))
            pixels[y, :, 3] = alpha_value
        img = Image.fromarray(pixels)

    return img


# Global instances for convenience
screenshot_manager = ScreenshotManager()
performance_profiler = PerformanceProfiler()
