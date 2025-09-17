#!/usr/bin/env python3
"""
Example script demonstrating how to download ROS bags using TACC Tools.
"""

import sys
from pathlib import Path

# Add tacc_tools to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tacc_tools import RosbagDownloader, ContainerManager

def main():
    print("TACC Tools - ROS Bag Download Example")
    print("=" * 40)
    
    # Initialize the downloader
    container_manager = ContainerManager()
    downloader = RosbagDownloader(container_manager)
    
    # Example 1: List available containers
    print("\n1. Available containers:")
    containers = container_manager.list_containers()
    for container in containers:
        print(f"   - {container}")
    
    # Example 2: List remote bags (simulated)
    print("\n2. Listing remote bags (example):")
    print("   Would connect to: robot.example.com:/data/bags/")
    print("   Found bags:")
    print("   - /data/bags/experiment_1.bag")
    print("   - /data/bags/experiment_2.bag")
    
    # Example 3: Download from URL (example)
    print("\n3. Download from URL (example):")
    url = "https://example.com/sample.bag"
    local_path = "./downloaded_bags"
    
    print(f"   Downloading: {url}")
    print(f"   To: {local_path}")
    print("   [This is a simulation - no actual download]")
    
    # Example 4: Download from remote host (example)
    print("\n4. Download from remote host (example):")
    remote_host = "robot.example.com"
    remote_path = "/data/bags/"
    username = "ubuntu"
    ssh_key = "~/.ssh/robot_key"
    
    print(f"   Host: {remote_host}")
    print(f"   Remote path: {remote_path}")
    print(f"   Username: {username}")
    print(f"   SSH key: {ssh_key}")
    print("   [This is a simulation - no actual download]")
    
    print("\nExample completed!")
    print("\nTo run actual downloads, modify the parameters above")
    print("and call the appropriate downloader methods.")

if __name__ == '__main__':
    main()