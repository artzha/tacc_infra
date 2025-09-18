# TACC Tools Quick Start Guide

This guide will help you get started with TACC Tools for downloading and visualizing ROS bags using Apptainer/Singularity containers.

## Prerequisites

- Python 3.8 or later
- Apptainer/Singularity installed
- SSH access to remote hosts (for downloading)

## Installation

### Basic Installation

```bash
git clone https://github.com/artzha/tacc-tools.git
cd tacc-tools
pip install -e .
```

### Full Installation (Recommended)

```bash
pip install -e ".[ros1,ros2,visualization,remote]"
```

## Building Containers

Build the required containers for operations:

```bash
# Using make
make containers

# Or manually
apptainer build rosbag_downloader.sif tacc_tools/containers/rosbag_downloader.def
apptainer build rosbag_visualizer.sif tacc_tools/containers/rosbag_visualizer.def
```

## Basic Usage Examples

### 1. Download ROS Bags

#### From Remote Host

```python
from tacc_tools import RosbagDownloader

downloader = RosbagDownloader()

# Download all bags from remote directory
success = downloader.download_from_remote(
    remote_host="robot.example.com",
    remote_path="/data/experiments/",
    local_path="./downloaded_bags",
    username="robotuser",
    ssh_key="~/.ssh/robot_key"
)
```

#### From URL

```python
# Download single bag from URL
success = downloader.download_from_url(
    url="https://data.example.com/experiment1.bag",
    local_path="./bags/"
)
```

#### Command Line

```bash
# Download from remote host
tacc-download-rosbag --host robot.example.com \
                     --remote-path /data/bags/ \
                     --local-path ./bags \
                     --username ubuntu \
                     --ssh-key ~/.ssh/robot_key

# List remote bags first
tacc-download-rosbag --host robot.example.com \
                     --remote-path /data/bags/ \
                     --list-only \
                     --username ubuntu
```

### 2. Analyze ROS Bags

#### Get Bag Information

```python
from tacc_tools import RosbagVisualizer

visualizer = RosbagVisualizer()

# Get detailed bag information
info = visualizer.info("experiment1.bag")
print(f"Duration: {info['duration']}")
print(f"Message count: {info['messages']}")
for topic in info['topics']:
    print(f"Topic: {topic['name']} ({topic['message_count']} msgs)")
```

#### Play Bag File

```python
# Play at normal speed
visualizer.play("experiment1.bag")

# Play at 2x speed, only specific topics
visualizer.play("experiment1.bag", 
               topics=["/cmd_vel", "/odom"],
               rate=2.0)
```

#### Convert to CSV

```python
# Convert all topics to CSV
visualizer.convert_to_csv("experiment1.bag", "./csv_output/")

# Convert specific topics only
visualizer.convert_to_csv("experiment1.bag", 
                         "./csv_output/",
                         topics=["/cmd_vel", "/odom"])
```

#### Command Line Analysis

```bash
# Get bag info
tacc-visualize-rosbag --bag experiment1.bag --info

# Play bag at 1.5x speed
tacc-visualize-rosbag --bag experiment1.bag --play --rate 1.5

# Convert to CSV
tacc-visualize-rosbag --bag experiment1.bag --to-csv --output ./csv_data

# Launch RViz
tacc-visualize-rosbag --rviz --config examples/example_config.rviz
```

### 3. Batch Processing

#### Process Multiple Bags

```python
from pathlib import Path
from tacc_tools import RosbagVisualizer

visualizer = RosbagVisualizer()
bag_dir = Path("./downloaded_bags")

for bag_file in bag_dir.glob("*.bag"):
    print(f"Processing {bag_file.name}...")
    
    # Get info
    info = visualizer.info(str(bag_file))
    
    # Convert to CSV  
    csv_dir = bag_dir / "csv" / bag_file.stem
    visualizer.convert_to_csv(str(bag_file), str(csv_dir))
    
    print(f"Completed {bag_file.name}")
```

## Working with Containers

### Direct Container Usage

If you prefer to use containers directly:

```bash
# Download with container
apptainer exec --bind /local/path:/output rosbag_downloader.sif \
    rsync -avz user@host:/remote/bags/ /output/

# Analyze with container
apptainer exec --bind /path/to/bags:/bags rosbag_visualizer.sif \
    rosbag info /bags/experiment1.bag

# Convert to CSV with container
apptainer exec --bind /bags:/bags --bind /output:/output rosbag_visualizer.sif \
    python3 /scripts/bag_to_csv.py /bags/experiment1.bag /output
```

### GUI Applications

For GUI applications like RViz, enable X11 forwarding:

```bash
# Launch RViz with X11 forwarding
apptainer exec --bind /tmp/.X11-unix:/tmp/.X11-unix \
               --env DISPLAY=$DISPLAY \
               rosbag_visualizer.sif rviz2
```

## Configuration

Create a configuration file for common settings:

```yaml
# config/my_config.yaml
containers:
  definition_dir: "tacc_tools/containers"

remote_hosts:
  my_robot:
    host: "192.168.1.100"
    username: "ubuntu"  
    ssh_key: "~/.ssh/robot_key"
    data_path: "/data/rosbags"
    
  lab_server:
    host: "lab.university.edu"
    username: "researcher"
    ssh_key: "~/.ssh/lab_key"
    data_path: "/shared/experiments"
```

## Troubleshooting

### Common Issues

1. **Container build fails**: Ensure Apptainer/Singularity is installed and you have sufficient permissions.

2. **SSH connection fails**: Check SSH key permissions (`chmod 600 ~/.ssh/key`) and network connectivity.

3. **X11 forwarding not working**: Ensure X11 forwarding is enabled and `$DISPLAY` is set properly.

4. **Import errors**: Install missing dependencies with `pip install -e ".[ros1,ros2,visualization,remote]"`.

### Getting Help

- Check the main README.md for detailed documentation
- Look at examples in the `examples/` directory
- Submit issues on GitHub: https://github.com/artzha/tacc-tools/issues

## Next Steps

- Explore the `examples/` directory for more complex usage patterns
- Customize container definitions for your specific ROS setup
- Set up configuration files for your common remote hosts
- Integrate TACC Tools into your research workflows