#!/usr/bin/env python3
"""
Example script demonstrating how to visualize ROS bags using TACC Tools.
"""

import sys
from pathlib import Path

# Add tacc_tools to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tacc_tools import RosbagVisualizer, ContainerManager

def main():
    print("TACC Tools - ROS Bag Visualization Example")
    print("=" * 45)
    
    # Initialize the visualizer
    container_manager = ContainerManager()
    visualizer = RosbagVisualizer(container_manager)
    
    # Example bag file (replace with actual path)
    example_bag = "example.bag"
    
    print(f"\nExample bag file: {example_bag}")
    print("(Replace with actual bag path for real usage)")
    
    # Example 1: Get bag information
    print("\n1. Getting bag information:")
    print("   This would show:")
    print("   - Duration: 120.5 seconds")
    print("   - Topics: /cmd_vel, /odom, /scan")
    print("   - Message count: 12,450")
    print("   [Simulation - replace example_bag with real file]")
    
    # Example 2: Convert to CSV
    print("\n2. Converting to CSV:")
    csv_output = "./csv_output"
    topics = ["/cmd_vel", "/odom"]
    
    print(f"   Output directory: {csv_output}")
    print(f"   Selected topics: {topics}")
    print("   [Simulation - would create CSV files for each topic]")
    
    # Example 3: Play bag
    print("\n3. Playing bag:")
    print("   Rate: 1.5x speed")
    print("   Topics: All topics")
    print("   [Simulation - would start bag playback]")
    
    # Example 4: Launch RViz
    print("\n4. Launching RViz:")
    config_file = "examples/example_config.rviz"
    print(f"   Config file: {config_file}")
    print("   [Simulation - would launch RViz with configuration]")
    
    # Example 5: Container information
    print("\n5. Container information:")
    containers = container_manager.list_containers()
    for container in containers:
        print(f"   Available container: {container}")
    
    print("\nExample completed!")
    print("\nTo run actual visualization:")
    print("1. Replace 'example.bag' with a real bag file path")
    print("2. Uncomment and modify the method calls below")
    print("3. Ensure containers are built if using container mode")
    
    # Uncomment and modify these lines for actual usage:
    # info = visualizer.info(example_bag, use_container=False)
    # print("Bag info:", info)
    
    # success = visualizer.convert_to_csv(example_bag, csv_output, topics=topics)
    # print("CSV conversion success:", success)
    
    # success = visualizer.play(example_bag, rate=1.5)
    # print("Playback started:", success)

if __name__ == '__main__':
    main()