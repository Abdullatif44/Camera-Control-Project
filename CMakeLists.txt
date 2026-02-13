cmake_minimum_required(VERSION 3.10)
project(CameraApp)

set(CMAKE_CXX_STANDARD 17)

find_package(OpenCV REQUIRED)

add_executable(CameraApp main.cpp)
target_link_libraries(CameraApp ${OpenCV_LIBS})
