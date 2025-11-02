#!/bin/bash
# Setup X11 for Docker GUI applications

echo "Setting up X11 forwarding for Docker..."

# Create .docker.xauth file if it doesn't exist
XAUTH=/tmp/.docker.xauth
if [ ! -f $XAUTH ]; then
    touch $XAUTH
fi

# Generate xauth key
xauth nlist $DISPLAY | sed -e 's/^..../ffff/' | xauth -f $XAUTH nmerge -

# Set proper permissions
chmod 644 $XAUTH

# Allow connections from local
xhost +local:docker

echo "✓ X11 setup complete!"
echo "Now you can run GUI applications in Docker"
