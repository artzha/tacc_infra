"""
Container Manager for Apptainer/Singularity operations.
"""

import os
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class ContainerManager:
    """Manages Apptainer/Singularity container operations."""
    
    def __init__(self, container_dir: Union[str, Path] = None):
        """
        Initialize the container manager.
        
        Args:
            container_dir: Directory containing container definition files
        """
        self.container_dir = Path(container_dir) if container_dir else Path(__file__).parent / "containers"
        self.containers = {}
        self._load_containers()
    
    def _load_containers(self):
        """Load available container definitions."""
        if self.container_dir.exists():
            for def_file in self.container_dir.glob("*.def"):
                container_name = def_file.stem
                self.containers[container_name] = str(def_file)
    
    def build_container(self, container_name: str, output_path: Optional[str] = None, 
                       force_rebuild: bool = False) -> str:
        """
        Build a Singularity container from definition file.
        
        Args:
            container_name: Name of the container to build
            output_path: Output path for the built container
            force_rebuild: Whether to force rebuild existing container
            
        Returns:
            Path to the built container
        """
        if container_name not in self.containers:
            raise ValueError(f"Container '{container_name}' not found in {self.container_dir}")
        
        def_file = self.containers[container_name]
        if not output_path:
            output_path = f"{container_name}.sif"
        
        output_path = Path(output_path)
        
        if output_path.exists() and not force_rebuild:
            logger.info(f"Container {output_path} already exists. Use force_rebuild=True to rebuild.")
            return str(output_path)
        
        cmd = ["apptainer", "build"]
        if force_rebuild:
            cmd.append("--force")
        cmd.extend([str(output_path), def_file])
        
        logger.info(f"Building container: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info(f"Container built successfully: {output_path}")
            return str(output_path)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to build container: {e.stderr}")
            raise
    
    def run_container(self, container_path: str, command: List[str], 
                     bind_mounts: Optional[Dict[str, str]] = None,
                     environment: Optional[Dict[str, str]] = None,
                     workdir: Optional[str] = None) -> subprocess.CompletedProcess:
        """
        Run a command in a Singularity container.
        
        Args:
            container_path: Path to the container (.sif file)
            command: Command to run inside the container
            bind_mounts: Dictionary of host_path: container_path binds
            environment: Environment variables to set
            workdir: Working directory inside container
            
        Returns:
            CompletedProcess object with execution results
        """
        cmd = ["apptainer", "exec"]
        
        # Add bind mounts
        if bind_mounts:
            for host_path, container_path in bind_mounts.items():
                cmd.extend(["--bind", f"{host_path}:{container_path}"])
        
        # Add environment variables
        if environment:
            for key, value in environment.items():
                cmd.extend(["--env", f"{key}={value}"])
        
        # Add working directory
        if workdir:
            cmd.extend(["--pwd", workdir])
        
        cmd.append(container_path)
        cmd.extend(command)
        
        logger.info(f"Running container command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result
        except Exception as e:
            logger.error(f"Failed to run container: {e}")
            raise
    
    def list_containers(self) -> List[str]:
        """List available container definitions."""
        return list(self.containers.keys())
    
    def get_container_info(self, container_name: str) -> Dict[str, str]:
        """Get information about a container definition."""
        if container_name not in self.containers:
            raise ValueError(f"Container '{container_name}' not found")
        
        def_file = self.containers[container_name]
        return {
            "name": container_name,
            "definition_file": def_file,
            "exists": Path(def_file).exists()
        }