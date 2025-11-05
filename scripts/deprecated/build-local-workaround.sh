#!/bin/bash
# Workaround for iptables error on Jetson when building Docker images
# This is a fallback if you need to build locally

echo "Attempting to build with network workaround..."

# Try building with host network mode (bypasses iptables setup)
DOCKER_BUILDKIT=0 docker build \
    --network=host \
    -t jetson-monitor:latest \
    .

# Note: DOCKER_BUILDKIT=0 disables BuildKit which has stricter network requirements
# --network=host uses the host's network stack, avoiding the iptables raw table issue
