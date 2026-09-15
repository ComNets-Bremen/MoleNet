idf_build_get_property(component_targets __COMPONENT_TARGETS)

if ("___idf_espressif__esp-dl" IN_LIST component_targets)
    idf_component_get_property(
        espdl_dir
        espressif__esp-dl
        COMPONENT_DIR
    )
elseif("___idf_esp-dl" IN_LIST component_targets)
    idf_component_get_property(
        espdl_dir
        esp-dl
        COMPONENT_DIR
    )
endif()

set(cmake_dir ${espdl_dir}/fbs_loader/cmake)
include(${cmake_dir}/utilities.cmake)

set(embed_files
    models/kws_3class.espdl
    mfcc_params/hann_window.bin
    mfcc_params/mel_filterbank_transposed.bin
    mfcc_params/dct_matrix.bin
)

idf_component_register(
    SRCS "main.cpp"
    INCLUDE_DIRS "."
    REQUIRES
        kissfft
        esp_driver_i2s
        esp_driver_gpio
)

foreach(file ${embed_files})
    target_add_aligned_binary_data(
        ${COMPONENT_LIB}
        ${file}
        BINARY
    )
endforeach()