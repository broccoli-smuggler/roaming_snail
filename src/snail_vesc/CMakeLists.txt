cmake_minimum_required(VERSION 3.16)
project(snail_vesc)

if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)

# Pluginlib SystemInterface implementation lands here:
#   find_package(hardware_interface REQUIRED)
#   find_package(pluginlib REQUIRED)
#   find_package(rclcpp REQUIRED)
#   find_package(rclcpp_lifecycle REQUIRED)
#   add_library(${PROJECT_NAME} SHARED src/snail_vesc_system.cpp)
#   ament_target_dependencies(${PROJECT_NAME} hardware_interface pluginlib rclcpp rclcpp_lifecycle)
#   pluginlib_export_plugin_description_file(hardware_interface plugin_description.xml)
#   install(TARGETS ${PROJECT_NAME} LIBRARY DESTINATION lib)
#   install(DIRECTORY include/ DESTINATION include)

install(
  DIRECTORY config launch
  DESTINATION share/${PROJECT_NAME}
  OPTIONAL
)

ament_package()
