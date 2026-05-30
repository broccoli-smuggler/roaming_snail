cmake_minimum_required(VERSION 3.16)
project(snail_gz)

find_package(ament_cmake REQUIRED)

install(
  DIRECTORY launch worlds
  DESTINATION share/${PROJECT_NAME}
  OPTIONAL
)

ament_package()
