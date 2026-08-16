# Docker environment (ROS 2 Jazzy)

A self-contained ROS 2 Jazzy workspace for the `sick_safetyscanners2` driver.
Everything — dependencies, build, launch, rviz2 — happens inside the container;
the host only needs Docker.

## Layout

| File | Purpose |
| ---- | ------- |
| `Dockerfile` | Jazzy image with the workspace pre-built at `/ros2_ws` |
| `docker-compose.yml` | Service definition: host networking, source bind mount, X11 |
| `entrypoint.sh` | Sources the ROS underlay + workspace overlay |
| `sick_safetyscanners2.repos` | Source dependencies that have no usable debian yet |

## Quick start

Run from the repository root:

```bash
# Build the image (first run pulls ~1.5 GB and takes a few minutes)
docker compose -f docker/docker-compose.yml build

# Start the container in the background
docker compose -f docker/docker-compose.yml up -d

# Get a shell with the workspace already sourced
docker compose -f docker/docker-compose.yml exec driver bash
```

Inside the container:

```bash
ros2 launch sick_safetyscanners2 sick_safetyscanners2_launch.py
```

The launch files hard-code their parameters and declare no launch arguments, so
`sensor_ip:=…` on the command line is silently ignored. To point the driver at a
different scanner, either edit `launch/sick_safetyscanners2_launch.py` on the
host (the bind mount plus `--symlink-install` makes it effective immediately) or
start the node directly:

```bash
ros2 run sick_safetyscanners2 sick_safetyscanners2_node --ros-args \
    -p sensor_ip:=192.168.1.11 -p host_ip:=192.168.1.9 -p frame_id:=scan
```

One-shot commands without opening a shell:

```bash
docker compose -f docker/docker-compose.yml run --rm driver \
    ros2 launch sick_safetyscanners2 sick_safetyscanners2_launch.py
```

Shut down with `docker compose -f docker/docker-compose.yml down`.

> `docker exec` bypasses the entrypoint, so use a **login** shell (`bash -lc '…'`)
> when scripting against the container — `bash -c` alone leaves ROS unsourced.

## Rebuilding after source changes

The repository is bind-mounted at `/ros2_ws/src/sick_safetyscanners2`, so edits
made on the host are visible immediately. Recompile inside the container:

```bash
docker compose -f docker/docker-compose.yml exec driver \
    bash -lc 'cd /ros2_ws && colcon build --symlink-install --packages-select sick_safetyscanners2'
```

`build/`, `install/` and `log/` live inside the container, never in the host
working tree. Because the image is built with `--symlink-install`, changes to
launch files, rviz configs and URDFs take effect without recompiling at all.

## Visualization

`rviz2` is installed and reaches the host display through `/tmp/.X11-unix`
(verified working under WSLg with hardware OpenGL):

```bash
docker compose -f docker/docker-compose.yml exec driver rviz2
# or the full sensor model:
docker compose -f docker/docker-compose.yml exec driver \
    ros2 launch sick_safetyscanners2 view_nanoscan3.launch.py
```

On a plain X11 host, run `xhost +local:docker` once. For a headless build that
skips rviz2 entirely, build with `INSTALL_GUI=false`.

## Design notes

**Cyclone DDS instead of the Fast DDS default.** Under WSL2 with host
networking, Fast DDS starts nodes correctly but never completes participant
discovery — `ros2 node list` stays empty even for a node running in the same
container, with shared memory or with `FASTDDS_BUILTIN_TRANSPORTS=UDPv4`.
Cyclone DDS works untuned, so the compose file sets
`RMW_IMPLEMENTATION=rmw_cyclonedds_cpp`. Override it per environment:

```bash
RMW_IMPLEMENTATION=rmw_fastrtps_cpp docker compose -f docker/docker-compose.yml up -d
```

**Host networking.** The scanner streams measurement data over UDP to
`host_ip`, so the container has to share the host's interfaces. This also lets
ROS 2 nodes on the host and in other containers see each other.

**`sick_safetyscanners2_interfaces` is built from source.** The released
`ros-jazzy-sick-safetyscanners2-interfaces` debian is 1.0.0, which predates
`StatusOverview.srv`; this branch does not compile against it. Tag 1.0.1 is
checked out via `sick_safetyscanners2.repos`. `sick_safetyscanners_base` comes
from apt (1.0.3) and already provides `requestStatusOverview()`.

**Non-root user.** The container runs as `ros` with the host's uid/gid
(defaults 1000:1000), so files created in the bind mount stay owned by the host
user. Override with `USER_UID` / `USER_GID` build args if yours differ.

## Configuration

Environment variables read by `docker-compose.yml`:

| Variable | Default | Effect |
| -------- | ------- | ------ |
| `ROS_DISTRO` | `jazzy` | ROS 2 distribution and image tag |
| `ROS_DOMAIN_ID` | `0` | DDS domain |
| `RMW_IMPLEMENTATION` | `rmw_cyclonedds_cpp` | DDS vendor |
| `INSTALL_GUI` | `true` | Build arg; `false` skips rviz2 |
| `USER_UID` / `USER_GID` | `1000` | Build args for the in-container user |
| `DISPLAY` | `:0` | X display used by rviz2 |

## Troubleshooting

* **`ros2 node list` is empty** — a DDS discovery problem, not a driver
  problem. Confirm `RMW_IMPLEMENTATION=rmw_cyclonedds_cpp`, and that all
  participants share the same `ROS_DOMAIN_ID`.
* **`Transitioning failed` on lifecycle configure** — expected when no scanner
  answers at `sensor_ip`. Check connectivity from inside the container with
  `ping 192.168.1.11`, and confirm host and sensor share a subnet.
* **No data on `/scan` although the node starts** — the sensor sends UDP to
  `host_ip`; verify it matches a real host address with
  `ip -4 addr` inside the container, then watch the stream with
  `tcpdump -i any udp` (the container already has `NET_ADMIN`/`NET_RAW`).
* **rviz2 cannot open a display** — check `DISPLAY` is exported on the host and
  that `/tmp/.X11-unix` exists.
