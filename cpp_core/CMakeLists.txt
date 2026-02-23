cmake_minimum_required(VERSION 3.10)
project(3DGS_Optimizer)

# Use C++17 and enable aggressive optimizations for memory processing
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O3 -Wall -Wextra")

# Include directory for the header-only happly library
include_directories(include)

add_executable(gaussian_pruner src/gaussian_pruner.cpp)
