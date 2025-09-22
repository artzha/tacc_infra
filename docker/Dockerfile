# === Base: Ubuntu 20.04 with CUDA preinstalled ===
# Pick a CUDA tag that matches your host driver. 11.8 is broadly compatible.
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu20.04

ENV DEBIAN_FRONTEND=noninteractive \
    TZ=Etc/UTC \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# Basic utilities and Python/pip
RUN apt-get update && apt-get install -y --no-install-recommends \
    apt-transport-https ca-certificates gnupg2 curl wget lsb-release locales tzdata \
    build-essential git \
    python3 python3-pip python3-venv python3-dev \
  && rm -rf /var/lib/apt/lists/* \
  && (command -v python >/dev/null || ln -s /usr/bin/python3 /usr/bin/python) \
  && (command -v pip >/dev/null || ln -s /usr/bin/pip3 /usr/bin/pip) \
  && locale-gen en_US.UTF-8


# --- ROS Noetic (desktop) ---
# Add ROS apt repo + key, then install ros-noetic-desktop and common tools
RUN set -eux; \
    echo "deb http://packages.ros.org/ros/ubuntu $(lsb_release -sc) main" > /etc/apt/sources.list.d/ros1-latest.list; \
    curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key | apt-key add -; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
      ros-noetic-desktop \
      python3-rosdep python3-rosinstall python3-rosinstall-generator python3-wstool \
      ros-noetic-catkin; \
    rm -rf /var/lib/apt/lists/*

# Initialize rosdep (safe to re-run)
RUN rosdep init || true && rosdep update

# Upgrade pip (optional, but nice)
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Make ROS available in interactive shells
SHELL ["/bin/bash", "-lc"]
RUN echo "source /opt/ros/noetic/setup.bash" >> /etc/bash.bashrc

# Default workdir
WORKDIR /root/ws

# CUDA runtime env (good defaults; adjust as needed)
ENV NVIDIA_VISIBLE_DEVICES=all \
    NVIDIA_DRIVER_CAPABILITIES=compute,utility

# Entry shell (interactive)
CMD ["/bin/bash"]
