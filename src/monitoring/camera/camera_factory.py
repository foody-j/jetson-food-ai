"""
Camera Factory - Universal camera abstraction supporting USB and GMSL cameras
"""

import cv2
import subprocess
import os
import time
from typing import Optional, Tuple, Dict, Any
from enum import Enum


class CameraType(Enum):
    """Camera type enumeration"""
    USB = "usb"
    GMSL = "gmsl"


class CameraConfig:
    """Camera configuration container"""

    def __init__(
        self,
        camera_type: CameraType = CameraType.USB,
        camera_index: int = 0,
        resolution: Tuple[int, int] = (640, 360),
        fps: int = 30,
        # GMSL-specific settings
        gmsl_mode: int = 2,  # 0=GMSL, 1=GMSL2/6G, 2=GMSL2/3G
        gmsl_resolution_mode: int = 1,  # 0-4 (see GMSL driver docs)
        driver_dir: str = "/app/SG4A-NONX-G2Y-A1_ORIN_NANO_YUV_JP6.2_L4TR36.4.3"
    ):
        self.camera_type = camera_type
        self.camera_index = camera_index
        self.resolution = resolution
        self.fps = fps
        self.gmsl_mode = gmsl_mode
        self.gmsl_resolution_mode = gmsl_resolution_mode
        self.driver_dir = driver_dir

    @classmethod
    def from_dict(cls, config: dict) -> 'CameraConfig':
        """Create config from dictionary"""
        camera_type_str = config.get('camera_type', 'usb').lower()
        camera_type = CameraType.GMSL if camera_type_str == 'gmsl' else CameraType.USB

        return cls(
            camera_type=camera_type,
            camera_index=config.get('camera_index', 0),
            resolution=(
                config.get('resolution', {}).get('width', 640),
                config.get('resolution', {}).get('height', 360)
            ),
            fps=config.get('fps', 30),
            gmsl_mode=config.get('gmsl_mode', 2),
            gmsl_resolution_mode=config.get('gmsl_resolution_mode', 1),
            driver_dir=config.get('gmsl_driver_dir',
                "/app/SG4A-NONX-G2Y-A1_ORIN_NANO_YUV_JP6.2_L4TR36.4.3")
        )


class GMSLDriverManager:
    """GMSL driver loading and management"""

    _drivers_loaded = False
    _load_lock = False

    @classmethod
    def load_drivers(cls, driver_dir: str, camera_configs: list) -> bool:
        """
        Load GMSL drivers if not already loaded

        Args:
            driver_dir: Path to GMSL driver directory
            camera_configs: List of CameraConfig objects for all GMSL cameras

        Returns:
            bool: Success status
        """
        if cls._drivers_loaded:
            print("[GMSL] Drivers already loaded")
            return True

        if cls._load_lock:
            print("[GMSL] Driver loading in progress...")
            # Wait for other loading process
            for _ in range(30):
                time.sleep(0.1)
                if cls._drivers_loaded:
                    return True
            return False

        cls._load_lock = True

        try:
            # Check if drivers are already loaded FIRST
            print(f"[GMSL] Checking if drivers are already loaded...")
            result = subprocess.run(['lsmod'], capture_output=True, text=True)

            max96712_loaded = 'max96712' in result.stdout
            sgx_gmsl2_loaded = 'sgx_yuv_gmsl2' in result.stdout or 'gmsl2' in result.stdout

            if max96712_loaded and sgx_gmsl2_loaded:
                print("[GMSL] All drivers already loaded, skipping driver load")
                cls._drivers_loaded = True
                cls._load_lock = False

                # Still verify devices exist
                print("[GMSL] Verifying camera devices...")
                for i in range(4):
                    device_path = f"/dev/video{i}"
                    if os.path.exists(device_path):
                        print(f"[OK] {device_path} exists")
                    else:
                        print(f"[WARN] {device_path} not found")

                return True

            # Drivers not loaded, need to load them
            ko_dir = os.path.join(driver_dir, "ko")
            print(f"[GMSL] Drivers not loaded, loading from {ko_dir}")

            # Check if driver files exist
            max96712_ko = os.path.join(ko_dir, "max96712.ko")
            sgx_gmsl2_ko = os.path.join(ko_dir, "sgx-yuv-gmsl2.ko")

            if not os.path.exists(max96712_ko):
                print(f"[ERROR] max96712.ko not found: {max96712_ko}")
                cls._load_lock = False
                return False

            if not os.path.exists(sgx_gmsl2_ko):
                print(f"[ERROR] sgx-yuv-gmsl2.ko not found: {sgx_gmsl2_ko}")
                cls._load_lock = False
                return False

            # Load max96712 if needed
            if not max96712_loaded:
                print("[GMSL] Loading max96712.ko...")
                subprocess.run(['sudo', 'insmod', max96712_ko], check=True)
                print("[GMSL] max96712.ko loaded successfully")
            else:
                print("[GMSL] max96712 already loaded")

            # Load camera driver with GMSL modes for all cameras
            if not sgx_gmsl2_loaded:
                # Collect GMSL modes for up to 4 cameras (use mode 2 as default for unused slots)
                gmsl_modes = [2, 2, 2, 2]  # Default: all GMSL2/3G

                for config in camera_configs:
                    if config.camera_type == CameraType.GMSL and config.camera_index < 4:
                        gmsl_modes[config.camera_index] = config.gmsl_mode

                gmsl_mode_str = f"{gmsl_modes[0]},{gmsl_modes[1]},{gmsl_modes[2]},{gmsl_modes[3]}"

                print(f"[GMSL] Loading sgx-yuv-gmsl2.ko with GMSLMODE_1={gmsl_mode_str}...")
                subprocess.run([
                    'sudo', 'insmod', sgx_gmsl2_ko,
                    f'GMSLMODE_1={gmsl_mode_str}'
                ], check=True)
                print("[GMSL] sgx-yuv-gmsl2.ko loaded successfully")
            else:
                print("[GMSL] sgx-yuv-gmsl2 already loaded")

            # Wait for devices to initialize
            time.sleep(2)

            # Configure NVCSI clock
            print("[GMSL] Configuring NVCSI clock...")
            nvcsi_path = "/sys/kernel/debug/bpmp/debug/clk/nvcsi"
            if os.path.exists(nvcsi_path):
                try:
                    subprocess.run(['sudo', 'bash', '-c',
                                  f'echo 1 > {nvcsi_path}/mrq_rate_locked'], check=True)
                    subprocess.run(['sudo', 'bash', '-c',
                                  f'echo 214300000 > {nvcsi_path}/rate'], check=True)
                    print("[GMSL] NVCSI clock configured to 214.3 MHz")
                except Exception as e:
                    print(f"[WARN] NVCSI clock configuration failed: {e}")
            else:
                print("[WARN] NVCSI clock interface not found")

            # Verify devices
            print("[GMSL] Verifying camera devices...")
            for i in range(4):
                device_path = f"/dev/video{i}"
                if os.path.exists(device_path):
                    print(f"[OK] {device_path} exists")
                else:
                    print(f"[WARN] {device_path} not found")

            cls._drivers_loaded = True
            cls._load_lock = False
            return True

        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Failed to load GMSL drivers: {e}")
            cls._load_lock = False
            return False
        except Exception as e:
            print(f"[ERROR] GMSL driver loading error: {e}")
            cls._load_lock = False
            return False

    @classmethod
    def configure_resolution(cls, camera_index: int, resolution_mode: int) -> bool:
        """
        Configure GMSL camera resolution

        Args:
            camera_index: Camera device index (0-3)
            resolution_mode: Resolution mode (0-4)

        Returns:
            bool: Success status
        """
        device_path = f"/dev/video{camera_index}"

        if not os.path.exists(device_path):
            print(f"[ERROR] Camera device {device_path} not found")
            return False

        try:
            print(f"[GMSL] Setting {device_path} to resolution mode {resolution_mode}...")
            subprocess.run([
                'v4l2-ctl',
                '--set-ctrl', f'bypass_mode=0,sensor_mode={resolution_mode}',
                '-d', device_path
            ], check=True, capture_output=True)
            print(f"[GMSL] {device_path} configured successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"[WARN] Failed to configure {device_path}: {e}")
            return False
        except FileNotFoundError:
            print("[WARN] v4l2-ctl not found. Install v4l-utils: sudo apt install v4l-utils")
            return False

    @classmethod
    def unload_drivers(cls) -> bool:
        """Unload GMSL drivers (for cleanup/testing)"""
        try:
            print("[GMSL] Unloading drivers...")
            subprocess.run(['sudo', 'rmmod', 'sgx-yuv-gmsl2'], check=False)
            subprocess.run(['sudo', 'rmmod', 'max96712'], check=False)
            cls._drivers_loaded = False
            print("[GMSL] Drivers unloaded")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to unload drivers: {e}")
            return False


class UniversalCamera:
    """Universal camera class supporting both USB and GMSL cameras"""

    def __init__(self, config: CameraConfig):
        """
        Initialize camera with configuration

        Args:
            config: CameraConfig object
        """
        self.config = config
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_initialized = False
        self.camera_name = f"{config.camera_type.value.upper()} Camera {config.camera_index}"

    def initialize(self) -> bool:
        """
        Initialize camera (load drivers if needed, open camera)

        Returns:
            bool: Success status
        """
        try:
            # If GMSL camera, ensure drivers are loaded
            if self.config.camera_type == CameraType.GMSL:
                if not GMSLDriverManager.load_drivers(
                    self.config.driver_dir,
                    [self.config]
                ):
                    print(f"[ERROR] Failed to load GMSL drivers for {self.camera_name}")
                    return False

                # Configure resolution for GMSL camera
                GMSLDriverManager.configure_resolution(
                    self.config.camera_index,
                    self.config.gmsl_resolution_mode
                )

            # Open camera
            print(f"[카메라] Opening {self.camera_name}...")

            # GMSL cameras need device path (OpenCV will auto-detect backend)
            # USB cameras can use simple index
            if self.config.camera_type == CameraType.GMSL:
                # Use V4L2 backend for GMSL cameras
                device_path = f"/dev/video{self.config.camera_index}"
                print(f"[GMSL] Opening device: {device_path} with V4L2 backend")

                # Retry logic for GMSL cameras (sometimes need multiple attempts)
                max_retries = 3
                for attempt in range(max_retries):
                    self.cap = cv2.VideoCapture(device_path, cv2.CAP_V4L2)
                    if self.cap.isOpened():
                        print(f"[GMSL] Device opened successfully on attempt {attempt + 1}")
                        break
                    else:
                        print(f"[WARN] Attempt {attempt + 1}/{max_retries} failed, retrying...")
                        time.sleep(0.5)

                if not self.cap or not self.cap.isOpened():
                    print(f"[ERROR] Failed to open {device_path} after {max_retries} attempts")
                    return False

                # Set FOURCC to UYVY explicitly
                fourcc = cv2.VideoWriter_fourcc(*'UYVY')
                self.cap.set(cv2.CAP_PROP_FOURCC, fourcc)
                print(f"[GMSL] Set format to UYVY")

                # Set resolution BEFORE checking if opened
                print(f"[GMSL] Setting resolution to {self.config.resolution[0]}x{self.config.resolution[1]}")
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.resolution[0])
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.resolution[1])
                self.cap.set(cv2.CAP_PROP_FPS, self.config.fps)
            else:
                # USB cameras use index
                self.cap = cv2.VideoCapture(self.config.camera_index)

                if not self.cap.isOpened():
                    print(f"[ERROR] Failed to open {self.camera_name}")
                    return False

                # Set resolution for USB cameras
                print(f"[카메라] Setting resolution to {self.config.resolution[0]}x{self.config.resolution[1]}")
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.resolution[0])
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.resolution[1])
                self.cap.set(cv2.CAP_PROP_FPS, self.config.fps)

            # Verify resolution was set correctly
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            if actual_width != self.config.resolution[0] or actual_height != self.config.resolution[1]:
                print(f"[WARN] Resolution mismatch! Requested: {self.config.resolution[0]}x{self.config.resolution[1]}, "
                      f"Got: {actual_width}x{actual_height}")

            self.is_initialized = True
            actual_res = self.get_info()
            print(f"[카메라] {self.camera_name} initialized - "
                  f"Resolution: {actual_res.get('width')}x{actual_res.get('height')} @ {actual_res.get('fps')}fps")
            return True

        except Exception as e:
            print(f"[ERROR] {self.camera_name} initialization failed: {e}")
            return False

    def read_frame(self) -> Tuple[bool, Optional[Any]]:
        """
        Read frame from camera

        Returns:
            tuple: (success, frame)
        """
        if not self.is_initialized or not self.cap:
            return False, None

        ret, frame = self.cap.read()
        return ret, frame if ret else None

    def release(self) -> None:
        """Release camera resources"""
        if self.cap:
            self.cap.release()
            self.cap = None
        self.is_initialized = False
        print(f"[카메라] {self.camera_name} released")

    def get_info(self) -> Dict[str, Any]:
        """Get camera information"""
        if not self.is_initialized or not self.cap:
            return {}

        return {
            'width': int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'fps': int(self.cap.get(cv2.CAP_PROP_FPS)) or 30,
            'type': self.config.camera_type.value
        }

    @property
    def fps(self) -> int:
        """Get FPS"""
        if not self.is_initialized or not self.cap:
            return 30
        return int(self.cap.get(cv2.CAP_PROP_FPS)) or 30

    def __enter__(self):
        """Context manager entry"""
        if not self.initialize():
            raise RuntimeError(f"{self.camera_name} initialization failed")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.release()

    def __del__(self):
        """Destructor"""
        self.release()


def create_camera(config: CameraConfig) -> UniversalCamera:
    """
    Factory function to create camera

    Args:
        config: CameraConfig object

    Returns:
        UniversalCamera instance
    """
    return UniversalCamera(config)


def create_camera_from_dict(config_dict: dict) -> UniversalCamera:
    """
    Factory function to create camera from dictionary

    Args:
        config_dict: Camera configuration dictionary

    Returns:
        UniversalCamera instance
    """
    config = CameraConfig.from_dict(config_dict)
    return UniversalCamera(config)


def get_available_cameras(max_index: int = 10) -> list:
    """
    Get list of available camera devices

    Args:
        max_index: Maximum index to check

    Returns:
        List of available camera indices
    """
    available = []

    for i in range(max_index):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                available.append(i)
        cap.release()

    return available
