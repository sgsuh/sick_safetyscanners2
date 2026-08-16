"""Launch the driver either standalone or as a composable node.

Unlike sick_safetyscanners2_launch.py, every relevant setting is exposed as a
launch argument, so no file has to be edited to point the driver at a scanner:

    ros2 launch sick_safetyscanners2 sick_safetyscanners2_composable_launch.py \
        sensor_ip:=192.168.1.11 host_ip:=192.168.1.9

Setting use_composition:=true loads the driver into an already running
component container instead, which enables zero copy intra process transport
of the scan messages:

    ros2 launch sick_safetyscanners2 sick_safetyscanners2_composable_launch.py \
        use_composition:=true container_name:=drivers_container
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import LoadComposableNodes, Node
from launch_ros.descriptions import ComposableNode


def launch_setup(context, *args, **kwargs):
    # Map the fully qualified tf topics to relative ones, so that the node's
    # namespace gets prepended. There is currently no better alternative:
    # https://github.com/ros/geometry2/issues/32
    # https://github.com/ros/robot_state_publisher/pull/30
    transform_remappings = [("/tf", "tf"), ("/tf_static", "tf_static")]

    parameters = [
        {"frame_id": LaunchConfiguration("frame_id"),
         "sensor_ip": LaunchConfiguration("sensor_ip"),
         "host_ip": LaunchConfiguration("host_ip"),
         "interface_ip": LaunchConfiguration("interface_ip"),
         "host_udp_port": 0,
         "channel": 0,
         "channel_enabled": True,
         "skip": LaunchConfiguration("skip"),
         "min_range": LaunchConfiguration("min_range"),
         "max_range": LaunchConfiguration("max_range"),
         "angle_start": LaunchConfiguration("angle_start"),
         "angle_end": LaunchConfiguration("angle_end"),
         "time_offset": LaunchConfiguration("time_offset"),
         "general_system_state": True,
         "derived_settings": True,
         "measurement_data": True,
         "intrusion_data": True,
         "application_io_data": True,
         "use_persistent_config": False,
         "min_intensities": 0.0}
    ]

    remappings = transform_remappings + [("scan", LaunchConfiguration("topic"))]

    return [
        Node(
            condition=UnlessCondition(LaunchConfiguration("use_composition")),
            package="sick_safetyscanners2",
            executable="sick_safetyscanners2_node",
            namespace=LaunchConfiguration("namespace"),
            name=LaunchConfiguration("node_name"),
            arguments=["--ros-args", "--log-level",
                       LaunchConfiguration("log_level")],
            output="screen",
            emulate_tty=True,
            parameters=parameters,
            remappings=remappings,
        ),
        LoadComposableNodes(
            condition=IfCondition(LaunchConfiguration("use_composition")),
            target_container=LaunchConfiguration("container_name"),
            composable_node_descriptions=[
                ComposableNode(
                    package="sick_safetyscanners2",
                    plugin="sick::SickSafetyscannersRos2",
                    namespace=LaunchConfiguration("namespace"),
                    name=LaunchConfiguration("node_name"),
                    parameters=parameters,
                    remappings=remappings,
                    extra_arguments=[{"use_intra_process_comms": True}],
                )
            ],
        ),
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument("namespace", default_value=""),
        DeclareLaunchArgument("node_name", default_value="sick_safetyscanners2_node"),
        DeclareLaunchArgument("topic", default_value="scan"),
        DeclareLaunchArgument("frame_id", default_value="scan"),

        DeclareLaunchArgument("sensor_ip", default_value="192.168.1.11"),
        DeclareLaunchArgument("host_ip", default_value="192.168.1.9"),
        DeclareLaunchArgument("interface_ip", default_value="0.0.0.0"),

        DeclareLaunchArgument("skip", default_value="0"),
        # Zero keeps the range reported by the sensor's type code.
        DeclareLaunchArgument("min_range", default_value="0.0"),
        DeclareLaunchArgument("max_range", default_value="0.0"),
        # Equal start and end angle means the full scan is used.
        DeclareLaunchArgument("angle_start", default_value="0.0"),
        DeclareLaunchArgument("angle_end", default_value="0.0"),
        DeclareLaunchArgument("time_offset", default_value="0.0"),

        DeclareLaunchArgument("use_composition", default_value="false"),
        DeclareLaunchArgument("container_name", default_value="drivers_container"),
        DeclareLaunchArgument("log_level", default_value="info"),

        OpaqueFunction(function=launch_setup),
    ])
