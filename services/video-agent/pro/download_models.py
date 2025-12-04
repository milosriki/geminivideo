"""
Model Downloader for Smart Crop System

Downloads required models:
- OpenCV DNN Face Detection (Caffe ResNet-based)
- YOLO Object Detection models

Author: Pro Video Agent
"""

import urllib.request
import os
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelDownloader:
    """Download and setup detection models"""

    def __init__(self, models_dir: str = "models"):
        self.models_dir = Path(models_dir)
        self.face_dir = self.models_dir / "face_detection"
        self.yolo_dir = self.models_dir / "yolo"

    def setup_directories(self):
        """Create model directories"""
        self.face_dir.mkdir(parents=True, exist_ok=True)
        self.yolo_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created model directories: {self.models_dir}")

    def download_file(self, url: str, destination: Path, description: str = ""):
        """Download file with progress"""
        if destination.exists():
            logger.info(f"✓ {description} already exists: {destination}")
            return True

        try:
            logger.info(f"Downloading {description}...")
            logger.info(f"  URL: {url}")
            logger.info(f"  Destination: {destination}")

            def progress_callback(block_num, block_size, total_size):
                downloaded = block_num * block_size
                if total_size > 0:
                    percent = min(downloaded * 100 / total_size, 100)
                    mb_downloaded = downloaded / (1024 * 1024)
                    mb_total = total_size / (1024 * 1024)
                    print(f"\r  Progress: {percent:.1f}% ({mb_downloaded:.1f}/{mb_total:.1f} MB)", end='')

            urllib.request.urlretrieve(url, destination, progress_callback)
            print()  # New line after progress
            logger.info(f"✓ Downloaded {description}")
            return True

        except Exception as e:
            logger.error(f"✗ Failed to download {description}: {e}")
            return False

    def download_face_detection_models(self) -> bool:
        """Download OpenCV DNN face detection models (Caffe ResNet-based)"""
        logger.info("\n" + "="*60)
        logger.info("Downloading Face Detection Models (ResNet-10 SSD)")
        logger.info("="*60)

        base_url = "https://raw.githubusercontent.com/opencv/opencv_3rdparty/dnn_samples_face_detector_20170830"

        models = {
            "deploy.prototxt": {
                "url": f"{base_url}/deploy.prototxt",
                "path": self.face_dir / "deploy.prototxt"
            },
            "res10_300x300_ssd_iter_140000.caffemodel": {
                "url": f"{base_url}/res10_300x300_ssd_iter_140000.caffemodel",
                "path": self.face_dir / "res10_300x300_ssd_iter_140000.caffemodel"
            }
        }

        success = True
        for name, info in models.items():
            if not self.download_file(info["url"], info["path"], name):
                success = False

        return success

    def download_yolo_models(self, model_type: str = "yolov3-tiny") -> bool:
        """
        Download YOLO models

        Args:
            model_type: yolov3, yolov3-tiny, yolov4, yolov4-tiny
        """
        logger.info("\n" + "="*60)
        logger.info(f"Downloading YOLO Models ({model_type})")
        logger.info("="*60)

        # YOLO model URLs
        base_url = "https://raw.githubusercontent.com/pjreddie/darknet/master"

        if model_type == "yolov3":
            weights_url = "https://pjreddie.com/media/files/yolov3.weights"
            cfg_url = f"{base_url}/cfg/yolov3.cfg"
        elif model_type == "yolov3-tiny":
            weights_url = "https://pjreddie.com/media/files/yolov3-tiny.weights"
            cfg_url = f"{base_url}/cfg/yolov3-tiny.cfg"
        elif model_type == "yolov4":
            weights_url = "https://github.com/AlexeyAB/darknet/releases/download/darknet_yolo_v3_optimal/yolov4.weights"
            cfg_url = "https://raw.githubusercontent.com/AlexeyAB/darknet/master/cfg/yolov4.cfg"
        elif model_type == "yolov4-tiny":
            weights_url = "https://github.com/AlexeyAB/darknet/releases/download/darknet_yolo_v4_pre/yolov4-tiny.weights"
            cfg_url = "https://raw.githubusercontent.com/AlexeyAB/darknet/master/cfg/yolov4-tiny.cfg"
        else:
            logger.error(f"Unknown model type: {model_type}")
            return False

        # COCO class names
        names_url = f"{base_url}/data/coco.names"

        models = {
            f"{model_type}.weights": {
                "url": weights_url,
                "path": self.yolo_dir / f"{model_type}.weights"
            },
            f"{model_type}.cfg": {
                "url": cfg_url,
                "path": self.yolo_dir / f"{model_type}.cfg"
            },
            "coco.names": {
                "url": names_url,
                "path": self.yolo_dir / "coco.names"
            }
        }

        success = True
        for name, info in models.items():
            if not self.download_file(info["url"], info["path"], name):
                success = False

        return success

    def verify_models(self) -> dict:
        """Verify that all models are downloaded"""
        logger.info("\n" + "="*60)
        logger.info("Verifying Models")
        logger.info("="*60)

        status = {
            "face_detection": False,
            "yolo": False
        }

        # Check face detection models
        face_files = [
            self.face_dir / "deploy.prototxt",
            self.face_dir / "res10_300x300_ssd_iter_140000.caffemodel"
        ]

        if all(f.exists() for f in face_files):
            status["face_detection"] = True
            logger.info("✓ Face detection models: OK")
        else:
            logger.warning("✗ Face detection models: MISSING")

        # Check YOLO models (check for any YOLO version)
        yolo_files = list(self.yolo_dir.glob("*.weights"))
        cfg_files = list(self.yolo_dir.glob("*.cfg"))
        names_file = self.yolo_dir / "coco.names"

        if yolo_files and cfg_files and names_file.exists():
            status["yolo"] = True
            logger.info(f"✓ YOLO models: OK ({len(yolo_files)} model(s) found)")
        else:
            logger.warning("✗ YOLO models: MISSING")

        return status

    def download_all(self, include_yolo: bool = True):
        """Download all required models"""
        logger.info("\n" + "="*60)
        logger.info("Smart Crop Model Downloader")
        logger.info("="*60)

        self.setup_directories()

        # Download face detection models (required)
        face_success = self.download_face_detection_models()

        # Download YOLO models (optional)
        yolo_success = True
        if include_yolo:
            yolo_success = self.download_yolo_models(model_type="yolov3-tiny")

        # Verify
        status = self.verify_models()

        # Summary
        logger.info("\n" + "="*60)
        logger.info("Download Summary")
        logger.info("="*60)
        logger.info(f"Face Detection: {'✓ Ready' if status['face_detection'] else '✗ Failed'}")
        logger.info(f"YOLO Detection: {'✓ Ready' if status['yolo'] else '✗ Failed/Skipped'}")

        if status["face_detection"]:
            logger.info("\n✓ Smart Crop system is ready to use!")
        else:
            logger.warning("\n✗ Some models failed to download")
            logger.info("The system will fall back to Haar Cascade face detection")

        return status


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Download models for Smart Crop system"
    )
    parser.add_argument(
        "--models-dir",
        default="models",
        help="Directory to store models (default: models)"
    )
    parser.add_argument(
        "--no-yolo",
        action="store_true",
        help="Skip YOLO download (face detection only)"
    )
    parser.add_argument(
        "--yolo-model",
        default="yolov3-tiny",
        choices=["yolov3", "yolov3-tiny", "yolov4", "yolov4-tiny"],
        help="YOLO model to download (default: yolov3-tiny)"
    )

    args = parser.parse_args()

    downloader = ModelDownloader(models_dir=args.models_dir)
    downloader.setup_directories()

    # Download face detection
    downloader.download_face_detection_models()

    # Download YOLO if requested
    if not args.no_yolo:
        downloader.download_yolo_models(model_type=args.yolo_model)

    # Verify
    downloader.verify_models()


if __name__ == "__main__":
    main()
