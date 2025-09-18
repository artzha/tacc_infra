# TACC Tools

A comprehensive boilerplate template repository providing helper utility functions for launching Apptainer/Singularity containers for downloading and visualizing ROS bags remotely.

## Features

- **Container Management**: Build and manage Apptainer/Singularity containers for ROS operations
- **Remote Download**: Download ROS bag files from remote hosts using SSH/rsync or URLs
- **Visualization**: Analyze and visualize ROS bag data with containerized tools
- **Cross-Platform**: Works on HPC systems, local machines, and cloud environments
- **ROS 1 & 2 Support**: Compatible with both ROS 1 (.bag) and ROS 2 (.db3) formats

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/artzha/tacc-tools.git
cd tacc-tools

# Install the package
pip install -e .

# Or install with extras for full functionality
pip install -e ".[ros1,ros2,visualization,remote]"
```

### Basic Usage

#### Download ROS Bags

```python
from tacc_tools import RosbagDownloader

# Initialize downloader
downloader = RosbagDownloader()

# Download from remote host
downloader.download_from_remote(
    remote_host="robot.example.com",
    remote_path="/data/bags/",
    local_path="./downloaded_bags",
    username="ubuntu",
    ssh_key="~/.ssh/robot_key"
)

# Download from URL
downloader.download_from_url(
    url="https://example.com/data.bag",
    local_path="./bags/"
)
```

#### Visualize ROS Bags

```python
from tacc_tools import RosbagVisualizer

# Initialize visualizer
visualizer = RosbagVisualizer()

# Get bag information
info = visualizer.info("example.bag")
print(f"Duration: {info['duration']}")
print(f"Topics: {[t['name'] for t in info['topics']]}")

# Play bag file
visualizer.play("example.bag", rate=2.0)

# Convert to CSV
visualizer.convert_to_csv("example.bag", "./csv_output")

# Launch RViz
visualizer.launch_rviz("config.rviz")
```

#### Command Line Tools

```bash
# Download bags from remote host
tacc-download-rosbag --host robot.example.com --remote-path /data/bags/ \
                     --local-path ./bags --username ubuntu --ssh-key ~/.ssh/key

# Visualize bag file
tacc-visualize-rosbag --bag example.bag --info
tacc-visualize-rosbag --bag example.bag --play --rate 1.5
tacc-visualize-rosbag --bag example.bag --to-csv --output ./csv_data
```

## Architecture

### Core Components

1. **ContainerManager**: Manages Apptainer/Singularity container operations
2. **RosbagDownloader**: Handles remote downloading of ROS bag files
3. **RosbagVisualizer**: Provides visualization and analysis capabilities

### Container Definitions

- `rosbag_downloader.def`: Container with tools for downloading (rsync, wget, ssh)
- `rosbag_visualizer.def`: Container with ROS tools for analysis and visualization

### Directory Structure

```
tacc-tools/
├── tacc_tools/              # Main Python package
│   ├── containers/          # Singularity definition files
│   ├── scripts/             # Command-line scripts
│   ├── config/              # Configuration files
│   ├── container_manager.py # Container management
│   ├── rosbag_downloader.py # Download utilities
│   └── rosbag_visualizer.py # Visualization utilities
├── examples/                # Usage examples
├── tests/                   # Unit tests
└── docs/                    # Documentation
```

## Container Usage

### Building Containers

```bash
# Build download container
apptainer build rosbag_downloader.sif tacc_tools/containers/rosbag_downloader.def

# Build visualization container  
apptainer build rosbag_visualizer.sif tacc_tools/containers/rosbag_visualizer.def
```

### Manual Container Usage

```bash
# Download with container
apptainer exec --bind /local/path:/output rosbag_downloader.sif \
    rsync -avz user@host:/remote/path/ /output/

# Analyze bag with container
apptainer exec --bind /path/to/bags:/bags rosbag_visualizer.sif \
    rosbag info /bags/example.bag

# Convert to CSV with container
apptainer exec --bind /bags:/bags --bind /output:/output rosbag_visualizer.sif \
    python3 /scripts/bag_to_csv.py /bags/example.bag /output
```

## Configuration

Configuration can be provided via YAML files:

```yaml
# config/default_config.yaml
containers:
  definition_dir: "containers"
  downloader: "rosbag_downloader"
  visualizer: "rosbag_visualizer"

download:
  ssh:
    port: 22
    timeout: 30
  rsync:
    options: ["-avz", "--progress"]

remote_hosts:
  my_robot:
    host: "robot.example.com"
    username: "ubuntu"
    ssh_key: "~/.ssh/robot_key"
    data_path: "/data/rosbags"
```

## Examples

See the `examples/` directory for complete usage examples:

- `download_example.py`: Demonstrates downloading ROS bags
- `visualization_example.py`: Shows visualization capabilities
- `example_config.rviz`: Sample RViz configuration

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/artzha/tacc-tools.git
cd tacc-tools

# Install in development mode with all extras
pip install -e ".[dev,ros1,ros2,visualization,remote]"

# Run tests
pytest tests/

# Format code
black tacc_tools/

# Lint code
flake8 tacc_tools/
```

### Adding New Features

1. Create new modules in `tacc_tools/`
2. Add container definitions in `tacc_tools/containers/`
3. Update `__init__.py` to export new classes
4. Add tests in `tests/`
5. Update documentation

## Requirements

### System Requirements

- Python >= 3.8
- Apptainer/Singularity (for containerized operations)
- SSH client (for remote operations)

### Python Dependencies

**Core:**
- pyyaml >= 6.0
- pandas >= 1.3.0  
- numpy >= 1.20.0

**Optional:**
- ROS 1: rosbag, rospkg
- ROS 2: rosbag2-py
- Visualization: matplotlib, plotly, seaborn
- Remote: paramiko, scp

## Use Cases

### HPC Environments

Perfect for TACC and other HPC systems where:
- Containers provide isolated ROS environments
- Remote data access is common
- GUI forwarding may be limited

### Research Workflows

- Download experimental data from robots
- Batch process multiple bag files
- Generate visualizations and reports
- Share reproducible analysis environments

### Multi-Platform Development

- Consistent ROS environments across systems
- Portable analysis pipelines
- Easy deployment to different platforms

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

- Issues: https://github.com/artzha/tacc-tools/issues  
- Documentation: https://github.com/artzha/tacc-tools/wiki
- TACC Support: support@tacc.utexas.edu