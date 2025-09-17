#!/usr/bin/env python3
"""
Command-line script for downloading ROS bags remotely.
"""

import argparse
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from rosbag_downloader import RosbagDownloader
from container_manager import ContainerManager

def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def main():
    parser = argparse.ArgumentParser(
        description='Download ROS bag files from remote hosts',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download from remote host with SSH key
  python3 download_rosbag.py --host robot.example.com --remote-path /data/bags/ \\
                             --local-path ./downloaded_bags --username ubuntu \\
                             --ssh-key ~/.ssh/id_rsa

  # Download from URL
  python3 download_rosbag.py --url https://example.com/data.bag --local-path ./bags/

  # List remote bags before downloading
  python3 download_rosbag.py --host robot.example.com --remote-path /data/bags/ \\
                             --list-only --username ubuntu
        """
    )

    # Connection options
    conn_group = parser.add_argument_group('Connection options')
    conn_group.add_argument('--host', help='Remote hostname or IP address')
    conn_group.add_argument('--username', help='SSH username')
    conn_group.add_argument('--ssh-key', help='Path to SSH private key file')
    conn_group.add_argument('--url', help='URL to download from')

    # Path options
    path_group = parser.add_argument_group('Path options')
    path_group.add_argument('--remote-path', help='Remote path to ROS bag files')
    path_group.add_argument('--local-path', required=True, 
                           help='Local destination path')

    # Action options
    action_group = parser.add_argument_group('Action options')
    action_group.add_argument('--list-only', action='store_true',
                             help='Only list remote bags, do not download')
    action_group.add_argument('--no-container', action='store_true',
                             help='Use direct tools instead of container')

    # General options
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--container-dir', 
                       help='Directory containing container definitions')

    args = parser.parse_args()

    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    # Validate arguments
    if not args.url and not args.host:
        parser.error("Either --url or --host must be specified")
    
    if args.host and not args.remote_path:
        parser.error("--remote-path is required when using --host")

    try:
        # Initialize components
        container_manager = ContainerManager(args.container_dir) if args.container_dir else ContainerManager()
        downloader = RosbagDownloader(container_manager)

        if args.list_only:
            if not args.host:
                logger.error("--list-only requires --host")
                sys.exit(1)
            
            logger.info(f"Listing ROS bags on {args.host}:{args.remote_path}")
            bags = downloader.list_remote_bags(
                args.host, args.remote_path, 
                args.username, args.ssh_key
            )
            
            if bags:
                logger.info(f"Found {len(bags)} ROS bag files:")
                for bag in bags:
                    print(f"  {bag}")
            else:
                logger.info("No ROS bag files found")
        
        elif args.url:
            logger.info(f"Downloading from URL: {args.url}")
            success = downloader.download_from_url(
                args.url, args.local_path, 
                use_container=not args.no_container
            )
            
            if success:
                logger.info("Download completed successfully")
            else:
                logger.error("Download failed")
                sys.exit(1)
        
        else:
            logger.info(f"Downloading from {args.host}:{args.remote_path}")
            success = downloader.download_from_remote(
                args.host, args.remote_path, args.local_path,
                args.username, args.ssh_key,
                use_container=not args.no_container
            )
            
            if success:
                logger.info("Download completed successfully")
            else:
                logger.error("Download failed")
                sys.exit(1)

    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()