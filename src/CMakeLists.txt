# Define source switches.
if( WIN32 )
  set( SWITCHES -dos -cvis )
elseif( UNIX )
  set( SWITCHES -unix )
endif()

# Include user-selected source switches.
if( SWAN_MPI_ENABLED )
  if( CMAKE_Fortran_COMPILER_ID MATCHES "GNU" )
    list( APPEND SWITCHES -mpi )
  else()
    list( APPEND SWITCHES -impi -mpi )
  endif()
endif()
if( JAC )
  list( APPEND SWITCHES -jac )
endif()
if( METIS )
  list( APPEND SWITCHES -metis )
endif()
if( FFRO )
  list( APPEND SWITCHES -fixfront )
endif()
if( NETCDF )
  list( APPEND SWITCHES -netcdf )
endif()

# Select the active source list before declaring generation rules. The checked-in
# source lists are the source of truth, so checkout paths containing glob
# metacharacters do not affect template discovery.
set( SWAN_TEMPLATE_SOURCE_DIR "${CMAKE_CURRENT_SOURCE_DIR}" )
set( SWAN_GENERATED_SOURCE_DIR "${CMAKE_BINARY_DIR}/generated" )
set( SRC "${SWAN_GENERATED_SOURCE_DIR}" )
if( NETCDF )
  include( "${SWAN_TEMPLATE_SOURCE_DIR}/srclistnc.cmake" )
  set( SWAN_LIBRARY_SOURCES ${swan_nc_src} )
else()
  include( "${SWAN_TEMPLATE_SOURCE_DIR}/srclist.cmake" )
  set( SWAN_LIBRARY_SOURCES ${swan_src} )
endif()
set( SWAN_MAIN_SOURCE "${SWAN_GENERATED_SOURCE_DIR}/swanmain.${EXTF}" )

# Generate only the sources selected above. Every generated output maps directly
# to a checked-in .ftn/.ftn90 template and depends on both that template and the
# switch processor.
include( "${CMAKE_SOURCE_DIR}/cmake/SwanSourceSwitch.cmake" )
set( SWAN_REQUIRED_GENERATED_SOURCES
     ${SWAN_LIBRARY_SOURCES}
     "${SWAN_MAIN_SOURCE}" )
list( REMOVE_DUPLICATES SWAN_REQUIRED_GENERATED_SOURCES )
set( SWAN_GENERATED_SOURCES )
foreach( generated_source IN LISTS SWAN_REQUIRED_GENERATED_SOURCES )
  get_filename_component( generated_name "${generated_source}" NAME )
  if( generated_name MATCHES "\\.f90$" )
    string( REGEX REPLACE "\\.f90$" ".ftn90" template_name "${generated_name}" )
  elseif( generated_name MATCHES "\\.(f|for)$" )
    string( REGEX REPLACE "\\.(f|for)$" ".ftn" template_name "${generated_name}" )
  else()
    message( FATAL_ERROR "Unsupported generated Fortran source: ${generated_name}" )
  endif()

  set( template "${SWAN_TEMPLATE_SOURCE_DIR}/${template_name}" )
  if( NOT EXISTS "${template}" )
    message( FATAL_ERROR "Missing SWAN source template: ${template}" )
  endif()
  swan_add_switched_source(
    "${template}"
    "${SWAN_GENERATED_SOURCE_DIR}"
    "${SWITCHES}"
    switched_source
  )
  if( NOT switched_source STREQUAL generated_source )
    message( FATAL_ERROR
      "Generated source mismatch: expected ${generated_source}, got ${switched_source}"
    )
  endif()
  list( APPEND SWAN_GENERATED_SOURCES "${switched_source}" )
endforeach()
add_custom_target( swan-generated-sources DEPENDS ${SWAN_GENERATED_SOURCES} )

# Build the SWAN library.
add_library( swan${VERSION} STATIC ${SWAN_LIBRARY_SOURCES} )
target_compile_options( swan${VERSION} PRIVATE ${SWAN_FORTRAN_COMPILE_OPTIONS} )
if( NETCDF )
  target_link_libraries( swan${VERSION} PUBLIC NetCDF::NetCDF_Fortran )
endif()
if( METIS )
  target_include_directories( swan${VERSION} PUBLIC ${Metis_INCLUDE_DIR} )
  target_link_libraries( swan${VERSION} PUBLIC ${Metis_LIBRARIES} )
endif()
if( OPENMP )
  target_link_libraries( swan${VERSION} PUBLIC OpenMP::OpenMP_Fortran )
elseif( SWAN_MPI_ENABLED )
  target_link_libraries( swan${VERSION} PUBLIC MPI::MPI_Fortran )
endif()

# Build the SWAN executable.
add_executable( ${EXE} "${SWAN_MAIN_SOURCE}" )
target_compile_options( ${EXE} PRIVATE ${SWAN_FORTRAN_COMPILE_OPTIONS} )
target_link_libraries( ${EXE} PRIVATE swan${VERSION} )

install( TARGETS ${EXE} DESTINATION bin )
install( TARGETS swan${VERSION} DESTINATION lib )
install( DIRECTORY ${CMAKE_BINARY_DIR}/mod/ DESTINATION mod )
install( DIRECTORY ${CMAKE_SOURCE_DIR}/doc/ DESTINATION doc )
install( DIRECTORY ${CMAKE_SOURCE_DIR}/misc/ DESTINATION misc )
install( DIRECTORY ${CMAKE_SOURCE_DIR}/tools/ DESTINATION tools )
if( WIN32 )
  install( PROGRAMS ${CMAKE_SOURCE_DIR}/bin/swanrun.bat DESTINATION bin )
elseif( UNIX )
  install( PROGRAMS ${CMAKE_SOURCE_DIR}/bin/swanrun DESTINATION bin )
endif()
