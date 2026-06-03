# Snail dev/runtime image — ROS2 Jazzy + Gazebo Harmonic + ros2_control.
# Builds multi-arch (amd64 for laptop dev, arm64 for Raspberry Pi 5 deploy).
#
# Build:
#   docker buildx build --platform=linux/amd64,linux/arm64 -t snail:latest .
# Run (dev, amd64):
#   docker run -it --rm --net=host -v $PWD:/snail_ws snail:latest

FROM ros:jazzy-ros-base

ENV DEBIAN_FRONTEND=noninteractive
ENV ROS_DISTRO=jazzy

RUN apt-get update && apt-get install -y --no-install-recommends \
      ros-${ROS_DISTRO}-ros-gz \
      ros-${ROS_DISTRO}-gz-ros2-control \
      ros-${ROS_DISTRO}-ros2-control \
      ros-${ROS_DISTRO}-ros2-controllers \
      ros-${ROS_DISTRO}-teleop-twist-keyboard \
      xterm \
      ros-${ROS_DISTRO}-xacro \
      ros-${ROS_DISTRO}-robot-state-publisher \
      ros-${ROS_DISTRO}-joint-state-publisher \
      ros-${ROS_DISTRO}-rviz2 \
      python3-colcon-common-extensions \
      python3-pip \
      python3-can \
      can-utils \
      git \
      vim \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /snail_ws

# Source ROS in interactive shells.
RUN echo 'source /opt/ros/${ROS_DISTRO}/setup.bash' >> /root/.bashrc \
 && echo '[ -f /snail_ws/install/setup.bash ] && source /snail_ws/install/setup.bash' >> /root/.bashrc

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/bin/bash"]
