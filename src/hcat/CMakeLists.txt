# HCAT is only used by MPI builds.
if( NOT SWAN_MPI_ENABLED )
  return()
endif()

if( WIN32 )
  set( HSWITCH -dos -cvis )
elseif( UNIX )
  set( HSWITCH -unix )
endif()

set( HCAT_GENERATED_DIRECTORY "${CMAKE_BINARY_DIR}/generated/hcat" )
swan_add_switched_source(
  "${CMAKE_CURRENT_SOURCE_DIR}/swanhcat.ftn"
  "${HCAT_GENERATED_DIRECTORY}"
  "${HSWITCH}"
  swanhcat
)
add_custom_target( swan-hcat-generated-source DEPENDS "${swanhcat}" )

add_executable( ${HEXE} "${swanhcat}" )
target_compile_options( ${HEXE} PRIVATE ${SWAN_FORTRAN_COMPILE_OPTIONS} )
target_link_libraries( ${HEXE} PRIVATE MPI::MPI_Fortran )
install( TARGETS ${HEXE} RUNTIME DESTINATION bin )
