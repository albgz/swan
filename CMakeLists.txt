# a CMake script to build SWAN
#
# Copyright (C) 2026  Delft University of Technology

# use of CMake version 3.20 or greater
cmake_minimum_required( VERSION 3.20 )

# by default, the SWAN package will be installed in user's local or home folder
if( WIN32 )
  cmake_path( SET LOCALSWAN $ENV{LOCALAPPDATA}/Programs/wavemodels/swan )
  set( CMAKE_INSTALL_PREFIX "${LOCALSWAN}" CACHE STRING "" )
else()
  set( CMAKE_INSTALL_PREFIX "$ENV{HOME}/wavemodels/swan" CACHE STRING "" )
endif()

# Fortran project for SWAN
project( SWAN Fortran )

# set the SWAN version
set( VERSION 41.51 )

# Use a conventional default for single-configuration generators without
# overriding a build type selected by the caller.
if( NOT CMAKE_CONFIGURATION_TYPES AND NOT CMAKE_BUILD_TYPE )
  set( CMAKE_BUILD_TYPE Release CACHE STRING "Build type" FORCE )
  set_property( CACHE CMAKE_BUILD_TYPE PROPERTY STRINGS Debug Release RelWithDebInfo MinSizeRel )
endif()

# set the executable names
if( WIN32 )
   set( EXE swan )
   set( HEXE hcat )
else()
   set( EXE swan.exe )
   set( HEXE hcat.exe )
endif()

# set the Fortran77 extension
if( WIN32 )
   set( EXTF for )
else()
   set( EXTF f   )
endif()

# Optional build features.
option( OPENMP "Enable OpenMP parallelism" OFF )
option( MPI "Enable MPI parallelism" OFF )
option( JAC "Enable the MPI/Jacobi solver" OFF )
option( METIS "Enable METIS grid partitioning" OFF )
option( FFRO "Enable fixed-front propagation" OFF )
option( NETCDF "Enable NetCDF input/output" OFF )
# Opt-in diagnostics build. Adds compiler warnings and runtime checks for
# language/interface debt without changing the authoritative Release flags.
option( SWAN_DIAGNOSTICS "Enable opt-in Fortran diagnostics (warnings, runtime checks)" OFF )
# JAC uses the MPI implementation, but do not mutate the user's cached MPI
# choice. This keeps JAC=ON followed by JAC=OFF from leaving an accidental MPI
# build behind in the same build tree.
set( SWAN_MPI_ENABLED ${MPI} )
if( JAC )
  set( SWAN_MPI_ENABLED ON )
  message( STATUS "JAC requires MPI support" )
endif()
if( OPENMP AND SWAN_MPI_ENABLED )
  message( FATAL_ERROR "OPENMP cannot be combined with MPI or JAC" )
endif()

# define bin/lib//mod/src directories
set( BIN ${CMAKE_BINARY_DIR}/bin )
set( LIB ${CMAKE_BINARY_DIR}/lib )
set( MOD ${CMAKE_BINARY_DIR}/mod )
set( SRC ${CMAKE_SOURCE_DIR}/src )

# have the bin and lib folders placed in the build folder
set( CMAKE_RUNTIME_OUTPUT_DIRECTORY ${BIN} )
set( CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${LIB} )
set( CMAKE_LIBRARY_OUTPUT_DIRECTORY ${LIB} )

# have the modules placed in the mod folder
set( CMAKE_Fortran_MODULE_DIRECTORY ${MOD} )

# add find modules to the module path
list( APPEND CMAKE_MODULE_PATH "${CMAKE_SOURCE_DIR}/cmake" )
include( "${CMAKE_SOURCE_DIR}/cmake/SwanCompilerOptions.cmake" )

# Perl is required for generating configured Fortran sources.
find_package( Perl REQUIRED )
include( "${CMAKE_SOURCE_DIR}/cmake/SwanSourceSwitch.cmake" )
if( OPENMP )
  find_package( OpenMP REQUIRED COMPONENTS Fortran )
elseif( SWAN_MPI_ENABLED )
  find_package( MPI REQUIRED COMPONENTS Fortran )
endif()

# find Metis
if( METIS )
  find_package( Metis REQUIRED )
endif()

# find netCDF
if( NETCDF )
  # netCDF Fortran library is required
  find_package( NetCDF REQUIRED COMPONENTS Fortran )
endif()

# Build the SWAN library and executable. The source directory owns both targets;
# adding it once avoids duplicate preprocessing and configuration side effects.
add_subdirectory( ${SRC} ${LIB} )

# source preprocessing regression tests
include( CTest )
if( BUILD_TESTING )
  find_package( Python3 QUIET COMPONENTS Interpreter )
  if( Python3_Interpreter_FOUND )
    add_test(
      NAME switch-preprocessor
      COMMAND ${Python3_EXECUTABLE} -m unittest -v tests/test_switch.py
    )
    add_test(
      NAME cmake-configuration
      COMMAND ${Python3_EXECUTABLE} -m unittest -v tests/test_cmake_configuration.py
    )
    set_tests_properties(
      switch-preprocessor cmake-configuration
      PROPERTIES
        WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
        ENVIRONMENT "PYTHONDONTWRITEBYTECODE=1"
    )
  endif()
endif()

# if desired, create the HCAT executable
add_subdirectory( ${SRC}/hcat )
