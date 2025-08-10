cmake_minimum_required(VERSION 3.15.0)
project(Game VERSION 0.1.0 LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
add_executable(default_sequential default/default_sequential.cpp)

find_package(OpenMP)
if(OpenMP_CXX_FOUND)
# Auto-add executables for all cpp files under antiLife, inverseLife, and w&pLife.
# The output executable name matches the cpp basename. If OpenMP is found and the
# filename contains 'openMP', link against OpenMP::OpenMP_CXX to enable OpenMP flags.
foreach(LIFE_DIR IN ITEMS antiLife inverseLife "w&pLife" oilsLife invertAmazeLife neonBlobsLife hTreeLife)
	file(GLOB LIFE_SOURCES CONFIGURE_DEPENDS "${CMAKE_SOURCE_DIR}/${LIFE_DIR}/*.cpp")
	foreach(SRC ${LIFE_SOURCES})
		get_filename_component(BASE "${SRC}" NAME_WE)
		# Sanitize target name (for internal CMake target) but keep output name equal to BASE
		string(REGEX REPLACE "[^A-Za-z0-9_]" "_" TARGET_NAME "${LIFE_DIR}_${BASE}")
		add_executable(${TARGET_NAME} "${SRC}")
		set_target_properties(${TARGET_NAME} PROPERTIES OUTPUT_NAME "${BASE}")
		if(OpenMP_CXX_FOUND AND BASE MATCHES "openMP")
			target_link_libraries(${TARGET_NAME} PRIVATE OpenMP::OpenMP_CXX)
		endif()
	endforeach()
endforeach()

else()
	message(STATUS "OpenMP not found; default_openMP target disabled")
endif()


