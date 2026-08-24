cmake_minimum_required(VERSION 3.22.1)
project(mikoo_jni)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_VISIBILITY_PRESET hidden)
set(CMAKE_VISIBILITY_INLINES_HIDDEN ON)

add_library(mikoo_jni SHARED mikoo_jni.cpp)

target_compile_options(mikoo_jni PRIVATE
    -Wall
    -Wextra
    -Wpedantic
    -fno-exceptions
    -fno-rtti
)

target_link_libraries(mikoo_jni android log)

# Runtime integration point:
# add_subdirectory(<validated-runtime>)
# target_link_libraries(mikoo_jni PRIVATE <validated-runtime-target>)
