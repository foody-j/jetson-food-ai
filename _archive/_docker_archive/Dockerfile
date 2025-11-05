# Dockerfile for Jetson Orin #1 Monitoring System with GMSL Camera Support
# Base: NVIDIA JetPack 6.2 (r36.4.0)
FROM nvcr.io/nvidia/l4t-jetpack:r36.4.0

# Environment variables
ENV TZ=Asia/Seoul
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV YOLO_CONFIG_DIR=/root/.config/Ultralytics

# Set timezone
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone && \
    apt-get update && \
    apt-get install -y tzdata && \
    rm -rf /var/lib/apt/lists/*

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # Python and build tools
    python3-pip \
    python3-dev \
    python3-tk \
    libopenblas-base \
    libopenmpi-dev \
    libjpeg-dev \
    zlib1g-dev \
    libgtk2.0-dev \
    # Korean fonts for GUI
    fonts-nanum \
    fonts-nanum-coding \
    fonts-nanum-extra \
    # OpenCV dependencies
    libopencv-dev \
    python3-opencv \
    # Camera and video tools
    v4l-utils \
    libv4l-dev \
    # GStreamer for video streaming
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    libgstreamer-plugins-bad1.0-dev \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    gstreamer1.0-tools \
    gstreamer1.0-x \
    gstreamer1.0-alsa \
    gstreamer1.0-gl \
    gstreamer1.0-gtk3 \
    # Kernel module tools for GMSL drivers
    kmod \
    sudo \
    # Utilities
    nano \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip3 install --upgrade pip && \
    pip3 install --no-cache-dir \
    opencv-python \
    opencv-contrib-python \
    numpy \
    Pillow \
    ultralytics \
    paho-mqtt \
    psutil

# Create Ultralytics config directory
RUN mkdir -p /root/.config/Ultralytics && chmod -R 777 /root/.config/Ultralytics

# Create application directory
WORKDIR /app

# Copy application files (will be mounted as volume in production)
# Uncomment if you want to bake files into image:
# COPY autostart_autodown/ /app/autostart_autodown/
# COPY src/ /app/src/
# COPY camera_autostart/ /app/camera_autostart/
# COPY SG4A-NONX-G2Y-A1_ORIN_NANO_YUV_JP6.2_L4TR36.4.3/ /app/SG4A-NONX-G2Y-A1_ORIN_NANO_YUV_JP6.2_L4TR36.4.3/

# Create data directories
RUN mkdir -p /app/autostart_autodown/Detection \
    /app/autostart_autodown/StirFry_Data/left \
    /app/autostart_autodown/StirFry_Data/right

# Set up video group for camera access
RUN groupadd -f video && usermod -a -G video root

# Create entrypoint script for GMSL driver loading
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "[Docker] Jetson #1 Monitoring System Starting..."\n\
echo "[Docker] Host: $(hostname)"\n\
echo "[Docker] Date: $(date)"\n\
echo ""\n\
\n\
# Fix X11 permissions\n\
echo "[Docker] Checking X11 configuration..."\n\
if [ -n "$DISPLAY" ]; then\n\
    echo "[OK] DISPLAY=$DISPLAY"\n\
    if [ -n "$XAUTHORITY" ] && [ -f "$XAUTHORITY" ]; then\n\
        echo "[OK] XAUTHORITY=$XAUTHORITY (exists)"\n\
    else\n\
        echo "[WARNING] XAUTHORITY file not found: $XAUTHORITY"\n\
        echo "[INFO] Trying to use default .Xauthority..."\n\
        if [ -f /run/user/1000/.Xauthority ]; then\n\
            export XAUTHORITY=/run/user/1000/.Xauthority\n\
            echo "[OK] Using: $XAUTHORITY"\n\
        fi\n\
    fi\n\
else\n\
    echo "[WARNING] DISPLAY not set!"\n\
fi\n\
echo ""\n\
\n\
# Check if GMSL drivers are loaded on host\n\
echo "[Docker] Checking GMSL drivers..."\n\
if ! lsmod | grep -q "max96712"; then\n\
    echo "[WARNING] GMSL drivers not loaded on host!"\n\
    echo "[INFO] Attempting to load GMSL drivers..."\n\
    if [ -x /app/camera_autostart/camera_driver_autoload.sh ]; then\n\
        /app/camera_autostart/camera_driver_autoload.sh || {\n\
            echo "[ERROR] Driver loading failed!"\n\
            echo "[INFO] Please load drivers on host before starting container"\n\
        }\n\
    else\n\
        echo "[ERROR] Driver script not found: /app/camera_autostart/camera_driver_autoload.sh"\n\
    fi\n\
else\n\
    echo "[OK] GMSL drivers already loaded"\n\
fi\n\
\n\
echo ""\n\
echo "[Docker] Checking camera devices..."\n\
if ls /dev/video* 1> /dev/null 2>&1; then\n\
    ls -l /dev/video*\n\
    echo "[OK] Camera devices found"\n\
else\n\
    echo "[WARNING] No camera devices found!"\n\
    echo "[INFO] Expected: /dev/video0, /dev/video1, /dev/video2"\n\
fi\n\
\n\
echo ""\n\
echo "[Docker] Starting JETSON1_INTEGRATED.py..."\n\
\n\
# Change to application directory\n\
cd /app/autostart_autodown || exit 1\n\
\n\
exec python3 JETSON1_INTEGRATED.py\n\
' > /entrypoint.sh && chmod +x /entrypoint.sh

# Set working directory
WORKDIR /app/autostart_autodown

# Expose MQTT port (if needed)
EXPOSE 1883

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]

