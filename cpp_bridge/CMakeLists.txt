cmake_minimum_required(VERSION 3.20)
project(B737AICopilotBridge LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

set(XPLANE_SDK "" CACHE PATH "Path to extracted X-Plane SDK")
if(NOT XPLANE_SDK)
  message(FATAL_ERROR "Set -DXPLANE_SDK=/path/to/XPSDK")
endif()

set(XPLM_INCLUDE "${XPLANE_SDK}/CHeaders/XPLM")
if(NOT EXISTS "${XPLM_INCLUDE}/XPLMPlugin.h")
  message(FATAL_ERROR "Could not find ${XPLM_INCLUDE}/XPLMPlugin.h")
endif()

add_library(B737AICopilotBridge SHARED src/copilot_bridge.cpp)
target_include_directories(B737AICopilotBridge PRIVATE
  "${XPLANE_SDK}/CHeaders/XPLM"
  "${XPLANE_SDK}/CHeaders/Widgets"
)

target_compile_definitions(B737AICopilotBridge PRIVATE
  XPLM200 XPLM210 XPLM300 XPLM301 XPLM303 XPLM400
)

if(WIN32)
  target_compile_definitions(B737AICopilotBridge PRIVATE IBM=1 APL=0 LIN=0)
  target_link_libraries(B737AICopilotBridge PRIVATE
    "${XPLANE_SDK}/Libraries/Win/XPLM_64.lib"
    ws2_32
  )
  set_target_properties(B737AICopilotBridge PROPERTIES PREFIX "" SUFFIX ".xpl" OUTPUT_NAME "win")
elseif(APPLE)
  target_compile_definitions(B737AICopilotBridge PRIVATE IBM=0 APL=1 LIN=0)
  find_library(XPLM_LIBRARY XPLM PATHS "${XPLANE_SDK}/Libraries/Mac" NO_DEFAULT_PATH)
  if(XPLM_LIBRARY)
    target_link_libraries(B737AICopilotBridge PRIVATE "${XPLM_LIBRARY}")
  endif()
  set_target_properties(B737AICopilotBridge PROPERTIES PREFIX "" SUFFIX ".xpl" OUTPUT_NAME "mac")
else()
  target_compile_definitions(B737AICopilotBridge PRIVATE IBM=0 APL=0 LIN=1)
  # X-Plane resolves XPLM symbols at plugin load time on Linux.
  target_link_options(B737AICopilotBridge PRIVATE "-Wl,--unresolved-symbols=ignore-all")
  set_target_properties(B737AICopilotBridge PROPERTIES PREFIX "" SUFFIX ".xpl" OUTPUT_NAME "lin")
endif()

if(MSVC)
  target_compile_options(B737AICopilotBridge PRIVATE /W4 /permissive-)
else()
  target_compile_options(B737AICopilotBridge PRIVATE -Wall -Wextra -Wpedantic)
endif()
