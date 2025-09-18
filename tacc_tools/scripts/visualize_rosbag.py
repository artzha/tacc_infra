#!/usr/bin/env python3
"""
Command-line script for visualizing ROS bags.
"""

import argparse
import logging
import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from ..rosbag_visualizer import RosbagVisualizer
    from ..container_manager import ContainerManager
except ImportError:
    # Fallback for direct script execution
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from rosbag_visualizer import RosbagVisualizer
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
        description='Visualize and analyze ROS bag files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Get bag information
  python3 visualize_rosbag.py --bag example.bag --info

  # Play bag at 2x speed
  python3 visualize_rosbag.py --bag example.bag --play --rate 2.0

  # Convert specific topics to CSV
  python3 visualize_rosbag.py --bag example.bag --to-csv --output ./csv_data \\
                              --topics /cmd_vel /odom

  # Launch RViz
  python3 visualize_rosbag.py --rviz --config my_config.rviz
        """
    )

    # Input options
    input_group = parser.add_argument_group('Input options')
    input_group.add_argument('--bag', help='Path to ROS bag file')
    input_group.add_argument('--container-dir', 
                            help='Directory containing container definitions')

    # Action options
    action_group = parser.add_argument_group('Action options')
    action_group.add_argument('--info', action='store_true',
                             help='Show bag information')
    action_group.add_argument('--play', action='store_true',
                             help='Play the bag file')
    action_group.add_argument('--to-csv', action='store_true',
                             help='Convert bag topics to CSV files')
    action_group.add_argument('--rviz', action='store_true',
                             help='Launch RViz for visualization')

    # Playback options
    play_group = parser.add_argument_group('Playback options')
    play_group.add_argument('--rate', type=float, default=1.0,
                           help='Playback rate multiplier (default: 1.0)')
    play_group.add_argument('--start-time', type=float,
                           help='Start time offset in seconds')
    play_group.add_argument('--duration', type=float,
                           help='Duration to play in seconds')
    play_group.add_argument('--topics', nargs='+',
                           help='Specific topics to play/convert')

    # Output options
    output_group = parser.add_argument_group('Output options')
    output_group.add_argument('--output', help='Output directory for CSV files')
    output_group.add_argument('--config', help='RViz configuration file')

    # General options
    parser.add_argument('--no-container', action='store_true',
                       help='Use direct tools instead of container')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')

    args = parser.parse_args()

    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    # Validate arguments
    actions = [args.info, args.play, args.to_csv, args.rviz]
    if sum(actions) == 0:
        parser.error("At least one action must be specified: --info, --play, --to-csv, or --rviz")
    
    if (args.info or args.play or args.to_csv) and not args.bag:
        parser.error("--bag is required for info, play, and to-csv actions")
    
    if args.to_csv and not args.output:
        parser.error("--output is required when using --to-csv")

    try:
        # Initialize components
        container_manager = ContainerManager(args.container_dir) if args.container_dir else ContainerManager()
        visualizer = RosbagVisualizer(container_manager)

        if args.info:
            logger.info(f"Getting information for bag: {args.bag}")
            info = visualizer.info(args.bag, use_container=not args.no_container)
            
            if info:
                print("\n=== ROS Bag Information ===")
                print(json.dumps(info, indent=2))
            else:
                logger.error("Failed to get bag information")
                sys.exit(1)

        if args.play:
            logger.info(f"Playing bag: {args.bag}")
            success = visualizer.play(
                args.bag, 
                topics=args.topics,
                rate=args.rate,
                start_time=args.start_time,
                duration=args.duration,
                use_container=not args.no_container
            )
            
            if not success:
                logger.error("Failed to start bag playback")
                sys.exit(1)

        if args.to_csv:
            logger.info(f"Converting bag to CSV: {args.bag}")
            success = visualizer.convert_to_csv(
                args.bag, args.output,
                topics=args.topics,
                use_container=not args.no_container
            )
            
            if success:
                logger.info(f"CSV files saved to: {args.output}")
            else:
                logger.error("Failed to convert bag to CSV")
                sys.exit(1)

        if args.rviz:
            logger.info("Launching RViz")
            success = visualizer.launch_rviz(
                config_file=args.config,
                use_container=not args.no_container
            )
            
            if not success:
                logger.error("Failed to launch RViz")
                sys.exit(1)

    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()