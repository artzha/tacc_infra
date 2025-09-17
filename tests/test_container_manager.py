#!/usr/bin/env python3
"""
Tests for ContainerManager class.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from tacc_tools.container_manager import ContainerManager


class TestContainerManager:
    """Test cases for ContainerManager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.container_dir = self.temp_dir / "containers"
        self.container_dir.mkdir()
        
        # Create mock definition files
        (self.container_dir / "test_container.def").write_text("Mock definition")
        (self.container_dir / "another_container.def").write_text("Another definition")
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_init_with_container_dir(self):
        """Test initialization with custom container directory."""
        manager = ContainerManager(self.container_dir)
        assert manager.container_dir == self.container_dir
        assert len(manager.containers) == 2
    
    def test_init_default_container_dir(self):
        """Test initialization with default container directory."""
        manager = ContainerManager()
        expected_dir = Path(__file__).parent.parent / "tacc_tools" / "containers"
        assert manager.container_dir == expected_dir
    
    def test_load_containers(self):
        """Test loading container definitions."""
        manager = ContainerManager(self.container_dir)
        
        assert "test_container" in manager.containers
        assert "another_container" in manager.containers
        assert manager.containers["test_container"].endswith("test_container.def")
    
    def test_list_containers(self):
        """Test listing available containers."""
        manager = ContainerManager(self.container_dir)
        containers = manager.list_containers()
        
        assert isinstance(containers, list)
        assert "test_container" in containers
        assert "another_container" in containers
    
    def test_get_container_info(self):
        """Test getting container information."""
        manager = ContainerManager(self.container_dir)
        info = manager.get_container_info("test_container")
        
        assert info["name"] == "test_container"
        assert info["definition_file"].endswith("test_container.def")
        assert info["exists"] is True
    
    def test_get_container_info_not_found(self):
        """Test getting info for non-existent container."""
        manager = ContainerManager(self.container_dir)
        
        with pytest.raises(ValueError):
            manager.get_container_info("nonexistent")
    
    @patch('subprocess.run')
    def test_build_container_success(self, mock_run):
        """Test successful container build."""
        mock_run.return_value = Mock(returncode=0)
        
        manager = ContainerManager(self.container_dir)
        result = manager.build_container("test_container")
        
        assert result == "test_container.sif"
        mock_run.assert_called_once()
        
        # Check command structure
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "apptainer"
        assert cmd[1] == "build"
        assert "test_container.sif" in cmd
    
    @patch('subprocess.run')
    def test_build_container_with_output_path(self, mock_run):
        """Test container build with custom output path."""
        mock_run.return_value = Mock(returncode=0)
        
        manager = ContainerManager(self.container_dir)
        custom_path = str(self.temp_dir / "custom.sif")
        result = manager.build_container("test_container", custom_path)
        
        assert result == custom_path
    
    @patch('subprocess.run')
    def test_build_container_force_rebuild(self, mock_run):
        """Test container build with force rebuild."""
        mock_run.return_value = Mock(returncode=0)
        
        # Create existing container file
        existing_container = self.temp_dir / "test_container.sif"
        existing_container.touch()
        
        manager = ContainerManager(self.container_dir)
        manager.build_container("test_container", str(existing_container), force_rebuild=True)
        
        cmd = mock_run.call_args[0][0]
        assert "--force" in cmd
    
    @patch('subprocess.run')
    def test_run_container_basic(self, mock_run):
        """Test basic container execution."""
        mock_run.return_value = Mock(returncode=0, stdout="output", stderr="")
        
        manager = ContainerManager(self.container_dir)
        result = manager.run_container("test.sif", ["echo", "hello"])
        
        assert result.returncode == 0
        mock_run.assert_called_once()
        
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "apptainer"
        assert cmd[1] == "exec"
        assert "test.sif" in cmd
        assert "echo" in cmd
        assert "hello" in cmd
    
    @patch('subprocess.run')
    def test_run_container_with_bind_mounts(self, mock_run):
        """Test container execution with bind mounts."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        
        manager = ContainerManager(self.container_dir)
        bind_mounts = {"/host/path": "/container/path"}
        
        manager.run_container("test.sif", ["echo", "test"], bind_mounts=bind_mounts)
        
        cmd = mock_run.call_args[0][0]
        assert "--bind" in cmd
        assert "/host/path:/container/path" in cmd
    
    @patch('subprocess.run')
    def test_run_container_with_environment(self, mock_run):
        """Test container execution with environment variables."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        
        manager = ContainerManager(self.container_dir)
        environment = {"TEST_VAR": "test_value"}
        
        manager.run_container("test.sif", ["echo", "test"], environment=environment)
        
        cmd = mock_run.call_args[0][0]
        assert "--env" in cmd
        assert "TEST_VAR=test_value" in cmd
    
    @patch('subprocess.run')
    def test_run_container_with_workdir(self, mock_run):
        """Test container execution with working directory."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        
        manager = ContainerManager(self.container_dir)
        
        manager.run_container("test.sif", ["pwd"], workdir="/workspace")
        
        cmd = mock_run.call_args[0][0]
        assert "--pwd" in cmd
        assert "/workspace" in cmd