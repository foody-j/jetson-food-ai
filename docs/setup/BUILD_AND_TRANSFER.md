# Build Docker Image on Another Machine and Transfer to Jetson

## Why This Method?
- Build on a machine with stable internet (faster)
- Avoid iptables kernel module issues on Jetson
- Only transfer the final image (code changes are mounted as volumes anyway)

## Steps

### 1. On Build Machine (with stable internet)

```bash
# Clone the repository
git clone <your-repo-url> jetson-camera-monitor
cd jetson-camera-monitor

# Build the image
docker build -t jetson-monitor:latest .

# Save the image to a tar file
docker save jetson-monitor:latest | gzip > jetson-monitor-latest.tar.gz

# Check the file size
ls -lh jetson-monitor-latest.tar.gz
```

### 2. Transfer to Jetson

**Option A: USB drive**
```bash
# Copy to USB, then on Jetson:
cp /media/usb/jetson-monitor-latest.tar.gz ~/
```

**Option B: SCP (if both machines on same network)**
```bash
# From build machine:
scp jetson-monitor-latest.tar.gz dkuyj@<jetson-ip>:~/jetson-camera-monitor/
```

**Option C: HTTP server (if large file)**
```bash
# On build machine:
python3 -m http.server 8000

# On Jetson:
wget http://<build-machine-ip>:8000/jetson-monitor-latest.tar.gz
```

### 3. On Jetson - Load the Image

```bash
cd ~/jetson-camera-monitor

# Load the image
gunzip -c jetson-monitor-latest.tar.gz | docker load

# Verify it loaded
docker images | grep jetson-monitor

# Clean up the tar file (optional)
rm jetson-monitor-latest.tar.gz
```

### 4. Run as Normal

```bash
# Using docker-compose
docker-compose up

# Or using docker-run.sh
./docker-run.sh
```

## For Code Changes

Since your code is mounted as a volume (see docker-compose.yml), you can:
- Edit code directly on Jetson
- Just restart the container (no rebuild needed)
- Only rebuild the image if you change dependencies (Dockerfile)

## When to Rebuild Image?

Only rebuild when you change:
- System packages (apt-get in Dockerfile)
- Python packages (pip install in Dockerfile)
- Base configuration (ENV variables, timezone, etc.)

For normal code changes in `src/`, `jetson1_monitoring/`, etc.:
- Just edit on Jetson and restart container
- No image rebuild needed!

## Image Size

The saved image will be ~4-6 GB compressed.
Transfer time estimates:
- USB 3.0: ~2-3 minutes
- Gigabit LAN (scp): ~5-10 minutes
- WiFi: 15-30 minutes (depending on speed)
