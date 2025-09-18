"""
ROS bag visualizer utility for remote operations.
"""

import os
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple

from .container_manager import ContainerManager

logger = logging.getLogger(__name__)


class RosbagVisualizer:
    """Handles visualizing ROS bags using containers."""
    
    def __init__(self, container_manager: Optional[ContainerManager] = None):
        """
        Initialize the ROS bag visualizer.
        
        Args:
            container_manager: Container manager instance
        """
        self.container_manager = container_manager or ContainerManager()
        self.visualizer_container = "rosbag_visualizer"
    
    def info(self, bag_path: str, use_container: bool = True) -> Dict[str, any]:
        """
        Get information about a ROS bag file.
        
        Args:
            bag_path: Path to the ROS bag file
            use_container: Whether to use container for analysis
            
        Returns:
            Dictionary containing bag information
        """
        bag_path = Path(bag_path)
        if not bag_path.exists():
            raise FileNotFoundError(f"ROS bag file not found: {bag_path}")
        
        if use_container:
            return self._info_with_container(bag_path)
        else:
            return self._info_direct(bag_path)
    
    def _info_with_container(self, bag_path: Path) -> Dict[str, any]:
        """Get bag info using containerized tools."""
        try:
            container_path = self._ensure_visualizer_container()
            
            # Determine ROS bag type and command
            if bag_path.suffix == '.bag':
                # ROS 1 bag
                command = ["rosbag", "info", f"/bags/{bag_path.name}"]
            else:
                # ROS 2 bag (db3 or directory)
                command = ["ros2", "bag", "info", f"/bags/{bag_path.name}"]
            
            bind_mounts = {str(bag_path.parent): "/bags"}
            
            result = self.container_manager.run_container(
                container_path, command, bind_mounts=bind_mounts
            )
            
            if result.returncode == 0:
                return self._parse_bag_info(result.stdout)
            else:
                logger.error(f"Failed to get bag info: {result.stderr}")
                return {}
                
        except Exception as e:
            logger.error(f"Container bag info failed: {e}")
            return {}
    
    def _info_direct(self, bag_path: Path) -> Dict[str, any]:
        """Get bag info using direct system tools."""
        try:
            if bag_path.suffix == '.bag':
                command = ["rosbag", "info", str(bag_path)]
            else:
                command = ["ros2", "bag", "info", str(bag_path)]
            
            result = subprocess.run(command, capture_output=True, text=True)
            
            if result.returncode == 0:
                return self._parse_bag_info(result.stdout)
            else:
                logger.error(f"Failed to get bag info: {result.stderr}")
                return {}
                
        except Exception as e:
            logger.error(f"Direct bag info failed: {e}")
            return {}
    
    def _parse_bag_info(self, info_output: str) -> Dict[str, any]:
        """Parse rosbag info output into structured data."""
        info = {
            "duration": None,
            "start_time": None,
            "end_time": None,
            "size": None,
            "messages": None,
            "topics": []
        }
        
        lines = info_output.strip().split('\n')
        current_topic = None
        
        for line in lines:
            line = line.strip()
            
            if "duration:" in line:
                info["duration"] = line.split("duration:")[1].strip()
            elif "start:" in line:
                info["start_time"] = line.split("start:")[1].strip()
            elif "end:" in line:
                info["end_time"] = line.split("end:")[1].strip()
            elif "size:" in line:
                info["size"] = line.split("size:")[1].strip()
            elif "messages:" in line:
                info["messages"] = line.split("messages:")[1].strip()
            elif "topic" in line.lower() and "msgs" in line:
                # Parse topic line: "topic: /topic_name  123 msgs: geometry_msgs/Twist"
                parts = line.split()
                if len(parts) >= 4:
                    topic_name = parts[1]
                    msg_count = parts[2]
                    msg_type = parts[4] if len(parts) > 4 else "unknown"
                    info["topics"].append({
                        "name": topic_name,
                        "message_count": msg_count,
                        "message_type": msg_type
                    })
        
        return info
    
    def play(self, bag_path: str, topics: Optional[List[str]] = None,
             rate: float = 1.0, start_time: Optional[float] = None,
             duration: Optional[float] = None, use_container: bool = True) -> bool:
        """
        Play a ROS bag file.
        
        Args:
            bag_path: Path to the ROS bag file
            topics: List of topics to play (None for all)
            rate: Playback rate multiplier
            start_time: Start time offset in seconds
            duration: Duration to play in seconds
            use_container: Whether to use container for playback
            
        Returns:
            True if playback started successfully
        """
        bag_path = Path(bag_path)
        if not bag_path.exists():
            raise FileNotFoundError(f"ROS bag file not found: {bag_path}")
        
        if use_container:
            return self._play_with_container(bag_path, topics, rate, start_time, duration)
        else:
            return self._play_direct(bag_path, topics, rate, start_time, duration)
    
    def _play_with_container(self, bag_path: Path, topics: Optional[List[str]] = None,
                           rate: float = 1.0, start_time: Optional[float] = None,
                           duration: Optional[float] = None) -> bool:
        """Play bag using containerized tools."""
        try:
            container_path = self._ensure_visualizer_container()
            
            if bag_path.suffix == '.bag':
                command = ["rosbag", "play", f"/bags/{bag_path.name}"]
                if rate != 1.0:
                    command.extend(["-r", str(rate)])
                if start_time is not None:
                    command.extend(["-s", str(start_time)])
                if duration is not None:
                    command.extend(["-u", str(duration)])
                if topics:
                    command.extend(["--topics"] + topics)
            else:
                command = ["ros2", "bag", "play", f"/bags/{bag_path.name}"]
                if rate != 1.0:
                    command.extend(["-r", str(rate)])
                if start_time is not None:
                    command.extend(["--start-offset", str(start_time)])
                if duration is not None:
                    command.extend(["--duration", str(duration)])
                if topics:
                    command.extend(["--topics"] + topics)
            
            bind_mounts = {str(bag_path.parent): "/bags"}
            
            # Run in background for playback
            result = self.container_manager.run_container(
                container_path, command, bind_mounts=bind_mounts
            )
            
            logger.info(f"Started bag playback: {bag_path.name}")
            return True
            
        except Exception as e:
            logger.error(f"Container bag playback failed: {e}")
            return False
    
    def _play_direct(self, bag_path: Path, topics: Optional[List[str]] = None,
                    rate: float = 1.0, start_time: Optional[float] = None,
                    duration: Optional[float] = None) -> bool:
        """Play bag using direct system tools."""
        try:
            if bag_path.suffix == '.bag':
                command = ["rosbag", "play", str(bag_path)]
                if rate != 1.0:
                    command.extend(["-r", str(rate)])
                if start_time is not None:
                    command.extend(["-s", str(start_time)])
                if duration is not None:
                    command.extend(["-u", str(duration)])
                if topics:
                    command.extend(["--topics"] + topics)
            else:
                command = ["ros2", "bag", "play", str(bag_path)]
                if rate != 1.0:
                    command.extend(["-r", str(rate)])
                if start_time is not None:
                    command.extend(["--start-offset", str(start_time)])
                if duration is not None:
                    command.extend(["--duration", str(duration)])
                if topics:
                    command.extend(["--topics"] + topics)
            
            # Start playback
            process = subprocess.Popen(command)
            logger.info(f"Started bag playback: {bag_path.name} (PID: {process.pid})")
            return True
            
        except Exception as e:
            logger.error(f"Direct bag playback failed: {e}")
            return False
    
    def convert_to_csv(self, bag_path: str, output_dir: str,
                      topics: Optional[List[str]] = None,
                      use_container: bool = True) -> bool:
        """
        Convert ROS bag topics to CSV files.
        
        Args:
            bag_path: Path to the ROS bag file
            output_dir: Directory to save CSV files
            topics: List of topics to convert (None for all)
            use_container: Whether to use container for conversion
            
        Returns:
            True if conversion successful
        """
        bag_path = Path(bag_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if not bag_path.exists():
            raise FileNotFoundError(f"ROS bag file not found: {bag_path}")
        
        if use_container:
            return self._convert_with_container(bag_path, output_dir, topics)
        else:
            return self._convert_direct(bag_path, output_dir, topics)
    
    def _convert_with_container(self, bag_path: Path, output_dir: Path,
                              topics: Optional[List[str]] = None) -> bool:
        """Convert bag to CSV using containerized tools."""
        try:
            container_path = self._ensure_visualizer_container()
            
            # Use rostopic or custom conversion script
            command = ["python3", "/scripts/bag_to_csv.py", 
                      f"/bags/{bag_path.name}", "/output"]
            
            if topics:
                command.extend(["--topics"] + topics)
            
            bind_mounts = {
                str(bag_path.parent): "/bags",
                str(output_dir): "/output"
            }
            
            result = self.container_manager.run_container(
                container_path, command, bind_mounts=bind_mounts
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully converted bag to CSV: {output_dir}")
                return True
            else:
                logger.error(f"CSV conversion failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Container CSV conversion failed: {e}")
            return False
    
    def _convert_direct(self, bag_path: Path, output_dir: Path,
                       topics: Optional[List[str]] = None) -> bool:
        """Convert bag to CSV using direct system tools."""
        logger.warning("Direct CSV conversion not implemented. Use container mode.")
        return False
    
    def _ensure_visualizer_container(self) -> str:
        """Ensure the visualizer container is available."""
        container_name = self.visualizer_container
        container_path = f"{container_name}.sif"
        
        if not Path(container_path).exists():
            logger.info(f"Building visualizer container: {container_name}")
            container_path = self.container_manager.build_container(container_name)
        
        return container_path
    
    def launch_rviz(self, config_file: Optional[str] = None,
                   use_container: bool = True) -> bool:
        """
        Launch RViz for visualization.
        
        Args:
            config_file: Path to RViz config file
            use_container: Whether to use container for RViz
            
        Returns:
            True if RViz launched successfully
        """
        try:
            if use_container:
                container_path = self._ensure_visualizer_container()
                command = ["rviz"]
                
                bind_mounts = {}
                if config_file:
                    config_path = Path(config_file)
                    bind_mounts[str(config_path.parent)] = "/config"
                    command.extend(["-d", f"/config/{config_path.name}"])
                
                # Enable X11 forwarding for GUI
                environment = {"DISPLAY": os.environ.get("DISPLAY", ":0")}
                
                result = self.container_manager.run_container(
                    container_path, command, 
                    bind_mounts=bind_mounts,
                    environment=environment
                )
            else:
                command = ["rviz"]
                if config_file:
                    command.extend(["-d", config_file])
                
                process = subprocess.Popen(command)
                logger.info(f"Launched RViz (PID: {process.pid})")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to launch RViz: {e}")
            return False