cmake_minimum_required(VERSION 3.15.0)
project(Game VERSION 0.1.0 LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(OpenMP)
if(OpenMP_CXX_FOUND)
# filename contains 'openMP', link against OpenMP::OpenMP_CXX to enable OpenMP flags.
foreach(LIFE_DIR IN ITEMS antiLife inverseLife wnpLife oilsLife invertAmazeLife neonBlobsLife hTreeLife fuzzLife gnarlLife customLife)
	file(GLOB LIFE_SOURCES CONFIGURE_DEPENDS "${CMAKE_SOURCE_DIR}/${LIFE_DIR}/*.cpp")
	foreach(SRC ${LIFE_SOURCES})
		get_filename_component(BASE "${SRC}" NAME_WE)
		string(REGEX REPLACE "[^A-Za-z0-9_]" "_" TARGET_NAME "${LIFE_DIR}_${BASE}")
		add_executable(${TARGET_NAME} "${SRC}")
		set_target_properties(${TARGET_NAME} PROPERTIES OUTPUT_NAME "${BASE}")
		if(OpenMP_CXX_FOUND AND BASE MATCHES "openMP")
			target_link_libraries(${TARGET_NAME} PRIVATE OpenMP::OpenMP_CXX)
		endif()
	endforeach()
endforeach()

add_executable(default_sequential default/default_sequential.cpp)
else()
	message(STATUS "OpenMP not found; default_openMP target disabled")
endif()


