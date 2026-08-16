# Development / runtime image for the sick_safetyscanners2 ROS 2 driver.
#
#   docker compose -f docker/docker-compose.yml build
#
# The build is split so that the expensive apt/rosdep layers are only redone
# when package.xml changes, not on every source edit.

ARG ROS_DISTRO=jazzy
FROM ros:${ROS_DISTRO}-ros-base

ARG ROS_DISTRO
# Host uid/gid, so files written into the bind-mounted source tree stay owned
# by the developer instead of root.
ARG USERNAME=ros
ARG USER_UID=1000
ARG USER_GID=1000
# Set to "false" to skip rviz2 & friends and get a much smaller headless image.
ARG INSTALL_GUI=true

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ENV DEBIAN_FRONTEND=noninteractive \
    ROS_DISTRO=${ROS_DISTRO} \
    ROS_WS=/ros2_ws \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# ---------------------------------------------------------------------------
# Base tooling: build, debug and network inspection (the driver speaks UDP to
# the scanner, so ping/ip/tcpdump earn their place here).
# ---------------------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
        bash-completion \
        build-essential \
        ccache \
        cmake \
        gdb \
        git \
        iproute2 \
        iputils-ping \
        less \
        nano \
        net-tools \
        python3-colcon-clean \
        python3-pip \
        sudo \
        tcpdump \
        wget \
    && rm -rf /var/lib/apt/lists/*

# Cyclone DDS. The Fast DDS default fails to complete participant discovery
# under WSL2 host networking (nodes start, but `ros2 node list` stays empty,
# with or without shared memory), while Cyclone works untuned.
RUN apt-get update && apt-get install -y --no-install-recommends \
        ros-${ROS_DISTRO}-rmw-cyclonedds-cpp \
    && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------------------
# Non-root user. The upstream image already ships an "ubuntu" user on uid 1000,
# so rename that one when the requested uid/gid is already taken.
# ---------------------------------------------------------------------------
RUN set -eux; \
    if getent group "${USER_GID}" >/dev/null; then \
        groupmod -n "${USERNAME}" "$(getent group "${USER_GID}" | cut -d: -f1)"; \
    else \
        groupadd -g "${USER_GID}" "${USERNAME}"; \
    fi; \
    if getent passwd "${USER_UID}" >/dev/null; then \
        old_user="$(getent passwd "${USER_UID}" | cut -d: -f1)"; \
        usermod -l "${USERNAME}" -d "/home/${USERNAME}" -m -s /bin/bash "${old_user}"; \
    else \
        useradd -m -u "${USER_UID}" -g "${USER_GID}" -s /bin/bash "${USERNAME}"; \
    fi; \
    echo "${USERNAME} ALL=(ALL) NOPASSWD:ALL" > "/etc/sudoers.d/${USERNAME}"; \
    chmod 0440 "/etc/sudoers.d/${USERNAME}"

# ---------------------------------------------------------------------------
# Source-only dependencies. sick_safetyscanners_base comes from apt, but the
# released interfaces debian is too old (no StatusOverview.srv), so it is
# checked out into the workspace — see sick_safetyscanners2.repos.
# ---------------------------------------------------------------------------
WORKDIR ${ROS_WS}
COPY docker/sick_safetyscanners2.repos /tmp/deps.repos
RUN mkdir -p src && vcs import src < /tmp/deps.repos

# ---------------------------------------------------------------------------
# Package dependencies, resolved from every package.xml in the workspace.
# Copying only the manifests keeps this expensive layer cached across edits.
# ---------------------------------------------------------------------------
COPY package.xml src/sick_safetyscanners2/package.xml

RUN set -eux; \
    skip_keys=""; \
    if [ "${INSTALL_GUI}" != "true" ]; then skip_keys="rviz2"; fi; \
    apt-get update; \
    rosdep update --rosdistro "${ROS_DISTRO}"; \
    rosdep install --from-paths src --ignore-src -y \
        --rosdistro "${ROS_DISTRO}" \
        --skip-keys "${skip_keys}"; \
    rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------------------
# Source + first build. --symlink-install means the bind-mounted launch files,
# rviz configs and URDFs are picked up live, without reinstalling.
# ---------------------------------------------------------------------------
COPY --chown=${USER_UID}:${USER_GID} . src/sick_safetyscanners2/
RUN chown -R "${USER_UID}:${USER_GID}" "${ROS_WS}"

USER ${USERNAME}

RUN source "/opt/ros/${ROS_DISTRO}/setup.bash" \
    && colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release

# Shells started by `docker exec` bypass the entrypoint, so the environment is
# also wired up through profile.d (login shells) and .bashrc (interactive ones).
USER root
RUN printf '%s\n' \
        'source /opt/ros/'"${ROS_DISTRO}"'/setup.bash' \
        '[ -f '"${ROS_WS}"'/install/setup.bash ] && source '"${ROS_WS}"'/install/setup.bash' \
        > /etc/profile.d/10-ros-workspace.sh \
    && chmod 0644 /etc/profile.d/10-ros-workspace.sh

USER ${USERNAME}
RUN printf '%s\n' \
        'source /etc/profile.d/10-ros-workspace.sh' \
        'cd '"${ROS_WS}" \
        >> "/home/${USERNAME}/.bashrc"

# Qt (rviz2) warns and falls back to a world-readable path without this.
ENV XDG_RUNTIME_DIR=/tmp/runtime-${USERNAME}
RUN mkdir -p "/tmp/runtime-${USERNAME}" && chmod 0700 "/tmp/runtime-${USERNAME}"

COPY --chmod=0755 docker/entrypoint.sh /usr/local/bin/entrypoint.sh
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["bash"]
