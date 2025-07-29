# Add our C source file to the build
add_library(usermod_audiodsp INTERFACE)

target_sources(usermod_audiodsp INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}/audiodsp.c
)

# Link our library to the main MicroPython usermod target
target_link_libraries(usermod INTERFACE usermod_audiodsp)