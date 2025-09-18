"""
ROS bag downloader utility for remote operations.
"""

import os
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Union
from urllib.parse import urlparse

from .container_manager import ContainerManager

logger = logging.getLogger(__name__)


class RosbagDownloader:
    """Handles downloading ROS bags remotely using containers."""
    
    def __init__(self, container_manager: Optional[ContainerManager] = None):
        """
        Initialize the ROS bag downloader.
        
        Args:
            container_manager: Container manager instance
        """
        self.container_manager = container_manager or ContainerManager()
        self.download_container = "rosbag_downloader"
    
    def download_from_remote(self, remote_host: str, remote_path: str, 
                           local_path: str, username: Optional[str] = None,
                           ssh_key: Optional[str] = None,
                           use_container: bool = True) -> bool:
        """
        Download ROS bag files from remote host.
        
        Args:
            remote_host: Remote hostname or IP address
            remote_path: Path to ROS bag files on remote host
            local_path: Local destination path
            username: SSH username for remote connection
            ssh_key: Path to SSH private key
            use_container: Whether to use container for download
            
        Returns:
            True if download successful, False otherwise
        """
        local_path = Path(local_path)
        local_path.mkdir(parents=True, exist_ok=True)
        
        if use_container:
            return self._download_with_container(
                remote_host, remote_path, local_path, username, ssh_key
            )
        else:
            return self._download_direct(
                remote_host, remote_path, local_path, username, ssh_key
            )
    
    def _download_with_container(self, remote_host: str, remote_path: str,
                               local_path: Path, username: Optional[str] = None,
                               ssh_key: Optional[str] = None) -> bool:
        """Download using containerized tools."""
        try:
            # Build container if needed
            container_path = self._ensure_download_container()
            
            # Prepare command
            command = ["rsync", "-avz", "--progress"]
            
            if ssh_key:
                command.extend(["-e", f"ssh -i {ssh_key}"])
            
            # Build source path
            source = f"{remote_host}:{remote_path}"
            if username:
                source = f"{username}@{source}"
            
            command.extend([source, "/output/"])
            
            # Set up bind mounts
            bind_mounts = {str(local_path): "/output"}
            if ssh_key:
                ssh_key_path = Path(ssh_key)
                bind_mounts[str(ssh_key_path.parent)] = "/ssh_keys"
                # Update ssh key path in command
                command = [cmd.replace(ssh_key, f"/ssh_keys/{ssh_key_path.name}") 
                          for cmd in command]
            
            # Run in container
            result = self.container_manager.run_container(
                container_path, command, bind_mounts=bind_mounts
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully downloaded ROS bags to {local_path}")
                return True
            else:
                logger.error(f"Download failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Container download failed: {e}")
            return False
    
    def _download_direct(self, remote_host: str, remote_path: str,
                        local_path: Path, username: Optional[str] = None,
                        ssh_key: Optional[str] = None) -> bool:
        """Download using direct system tools."""
        try:
            command = ["rsync", "-avz", "--progress"]
            
            if ssh_key:
                command.extend(["-e", f"ssh -i {ssh_key}"])
            
            source = f"{remote_host}:{remote_path}"
            if username:
                source = f"{username}@{source}"
            
            command.extend([source, str(local_path)])
            
            logger.info(f"Running direct download: {' '.join(command)}")
            result = subprocess.run(command, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Successfully downloaded ROS bags to {local_path}")
                return True
            else:
                logger.error(f"Download failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Direct download failed: {e}")
            return False
    
    def _ensure_download_container(self) -> str:
        """Ensure the download container is available."""
        container_name = self.download_container
        container_path = f"{container_name}.sif"
        
        if not Path(container_path).exists():
            logger.info(f"Building download container: {container_name}")
            container_path = self.container_manager.build_container(container_name)
        
        return container_path
    
    def download_from_url(self, url: str, local_path: str,
                         use_container: bool = True) -> bool:
        """
        Download ROS bag from URL.
        
        Args:
            url: URL to download from
            local_path: Local destination path
            use_container: Whether to use container for download
            
        Returns:
            True if download successful, False otherwise
        """
        local_path = Path(local_path)
        local_path.mkdir(parents=True, exist_ok=True)
        
        try:
            if use_container:
                container_path = self._ensure_download_container()
                command = ["wget", "-P", "/output", url]
                bind_mounts = {str(local_path): "/output"}
                
                result = self.container_manager.run_container(
                    container_path, command, bind_mounts=bind_mounts
                )
            else:
                command = ["wget", "-P", str(local_path), url]
                result = subprocess.run(command, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Successfully downloaded from {url} to {local_path}")
                return True
            else:
                logger.error(f"URL download failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"URL download failed: {e}")
            return False
    
    def list_remote_bags(self, remote_host: str, remote_path: str,
                        username: Optional[str] = None,
                        ssh_key: Optional[str] = None) -> List[str]:
        """
        List ROS bag files on remote host.
        
        Args:
            remote_host: Remote hostname or IP address
            remote_path: Path to search for ROS bag files
            username: SSH username for remote connection
            ssh_key: Path to SSH private key
            
        Returns:
            List of ROS bag file paths
        """
        try:
            ssh_cmd = ["ssh"]
            if ssh_key:
                ssh_cmd.extend(["-i", ssh_key])
            
            target = remote_host
            if username:
                target = f"{username}@{target}"
            
            ssh_cmd.append(target)
            ssh_cmd.append(f"find {remote_path} -name '*.bag' -o -name '*.db3'")
            
            result = subprocess.run(ssh_cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                bags = [line.strip() for line in result.stdout.split('\n') if line.strip()]
                return bags
            else:
                logger.error(f"Failed to list remote bags: {result.stderr}")
                return []
                
        except Exception as e:
            logger.error(f"Failed to list remote bags: {e}")
            return []