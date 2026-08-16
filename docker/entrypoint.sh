#!/usr/bin/env bash
# Sources the ROS 2 underlay plus the workspace overlay (when it has been
# built) and then hands over to whatever command the container was given.
set -e

source "/opt/ros/${ROS_DISTRO}/setup.bash"

if [ -f "${ROS_WS}/install/setup.bash" ]; then
    source "${ROS_WS}/install/setup.bash"
fi

exec "$@"
