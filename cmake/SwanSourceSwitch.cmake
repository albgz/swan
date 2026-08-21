include_guard(GLOBAL)

function(swan_add_switched_source input output_directory switches output_variable)
  get_filename_component(input_name "${input}" NAME)
  if(input_name MATCHES "\\.ftn90$")
    string(REGEX REPLACE "\\.ftn90$" ".f90" output_name "${input_name}")
  elseif(input_name MATCHES "\\.ftn$")
    if(WIN32)
      string(REGEX REPLACE "\\.ftn$" ".for" output_name "${input_name}")
    else()
      string(REGEX REPLACE "\\.ftn$" ".f" output_name "${input_name}")
    endif()
  else()
    message(FATAL_ERROR "Unsupported SWAN template extension: ${input}")
  endif()

  set(template_copy "${output_directory}/${input_name}")
  set(output "${output_directory}/${output_name}")
  add_custom_command(
    OUTPUT "${output}"
    COMMAND "${CMAKE_COMMAND}" -E make_directory "${output_directory}"
    COMMAND "${CMAKE_COMMAND}" -E copy "${input}" "${template_copy}"
    COMMAND "${CMAKE_COMMAND}" -E rm -f "${output}"
    COMMAND "${PERL_EXECUTABLE}" "${CMAKE_SOURCE_DIR}/switch.pl"
            ${switches} "${template_copy}"
    DEPENDS "${input}" "${CMAKE_SOURCE_DIR}/switch.pl"
    COMMENT "Switching ${input_name}"
    VERBATIM
  )
  set_source_files_properties("${output}" PROPERTIES GENERATED TRUE)
  set("${output_variable}" "${output}" PARENT_SCOPE)
endfunction()
