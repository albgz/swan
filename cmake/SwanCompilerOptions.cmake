set(SWAN_FORTRAN_COMPILE_OPTIONS)

if(CMAKE_Fortran_COMPILER_ID MATCHES "GNU")
  if(SWAN_DIAGNOSTICS)
    # Opt-in diagnostics configuration: surface language and interface debt.
    # The global -w suppression is replaced by explicit diagnostics, and
    # runtime bounds/initialization checks are enabled. This configuration
    # must not be used for the authoritative performance baseline.
    list(APPEND SWAN_FORTRAN_COMPILE_OPTIONS
         -Wall -Wextra -Wimplicit-interface -Wimplicit-procedure
         -Wsurprising -Wconversion-extra -Warray-temporaries
         -fcheck=all -fbacktrace
         -fno-second-underscore -ffree-line-length-none)
  else()
    list(APPEND SWAN_FORTRAN_COMPILE_OPTIONS
         -w -fno-second-underscore -ffree-line-length-none)
    if(WIN32 AND CMAKE_Fortran_COMPILER_VERSION VERSION_GREATER_EQUAL 7)
      list(APPEND SWAN_FORTRAN_COMPILE_OPTIONS -fdec)
    endif()
  endif()
elseif(CMAKE_Fortran_COMPILER_ID MATCHES "Intel")
  if(UNIX)
    list(APPEND SWAN_FORTRAN_COMPILE_OPTIONS
         -W0 -assume byterecl -traceback
         -diag-disable 8290 -diag-disable 8291 -diag-disable 8293)
  elseif(WIN32)
    list(APPEND SWAN_FORTRAN_COMPILE_OPTIONS
         /assume:byterecl /traceback /nowarn /nologo
         /Qdiag-disable:8290 /Qdiag-disable:8291 /Qdiag-disable:8293)
  endif()
elseif(CMAKE_Fortran_COMPILER_ID MATCHES "PGI|NVHPC")
  # No compatibility options are required.
elseif(CMAKE_Fortran_COMPILER_ID MATCHES "Fujitsu")
  list(APPEND SWAN_FORTRAN_COMPILE_OPTIONS -nwo)
elseif(CMAKE_Fortran_COMPILER_ID MATCHES "XL")
  list(APPEND SWAN_FORTRAN_COMPILE_OPTIONS -qstrict -qalign=4k -w)
else()
  message(FATAL_ERROR
          "Current Fortran compiler ${CMAKE_Fortran_COMPILER} is not supported")
endif()
