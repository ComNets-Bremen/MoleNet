#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <math.h>
#include <limits.h>

#include <vector>

#include "esp_log.h"
#include "esp_timer.h"
#include "esp_err.h"

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#include "driver/gpio.h"
#include "driver/i2s_std.h"

#include "kiss_fft.h"
#include "kiss_fftr.h"

#include "dl_model_base.hpp"
#include "dl_tensor_base.hpp"


// ============================================================
// TAG
// ============================================================

static const char *TAG = "KWS_LIVE";


// ============================================================
// AUDIO CONFIGURATION
// ============================================================

static constexpr int SAMPLE_RATE = 16000;

// Model/MFCC receives exactly one second.
static constexpr int AUDIO_SAMPLES = 16000;

// Record two seconds so the user does not need to hit
// an exact one-second timing window.
static constexpr int CAPTURE_SECONDS = 2;

static constexpr int CAPTURE_SAMPLES =
    SAMPLE_RATE * CAPTURE_SECONDS;


// Speech-window search:
// 100 ms energy window
// 25 ms hop

static constexpr int ENERGY_WINDOW_SAMPLES =
    SAMPLE_RATE / 10;

static constexpr int ENERGY_HOP_SAMPLES =
    SAMPLE_RATE / 40;


// ============================================================
// MFCC CONFIGURATION
// ============================================================

static constexpr int N_FFT = 1024;

static constexpr int WIN_LENGTH = 800;

static constexpr int HOP_LENGTH = 160;

static constexpr int N_MELS = 128;

static constexpr int N_MFCC = 40;

static constexpr int N_FRAMES = 101;

static constexpr int N_FREQ =
    N_FFT / 2 + 1;

static constexpr int WINDOW_OFFSET =
    (N_FFT - WIN_LENGTH) / 2;


// ============================================================
// AUDIO QUALITY SETTINGS
// ============================================================

// Quiet-room RMS was around 0.010.
//
// Reject recordings below 0.030.

static constexpr float SILENCE_RMS_THRESHOLD =
    0.030f;


// Treat values close to full scale as clipping.

static constexpr float CLIP_LEVEL =
    0.98f;


// Reject if more than 1% of selected samples are clipped.

static constexpr float MAX_CLIPPED_FRACTION =
    0.01f;


// Do hardware action only when prediction >= 70%.

static constexpr float MIN_CONFIDENCE =
    0.70f;


// ============================================================
// LAST AUDIO STATISTICS
// ============================================================

static float last_audio_rms =
    0.0f;

static float last_audio_peak =
    0.0f;

static float last_clipped_fraction =
    0.0f;

static float last_selected_start_seconds =
    0.0f;


// ============================================================
// MOLeNET V7.1 + INMP441
// ============================================================
//
// SCK = GPIO40
// WS  = GPIO41
// SD  = GPIO42
//
// L/R = GND
//
// LEFT I2S channel
//
// ============================================================

static constexpr gpio_num_t MIC_BCLK =
    GPIO_NUM_40;

static constexpr gpio_num_t MIC_WS =
    GPIO_NUM_41;

static constexpr gpio_num_t MIC_SD =
    GPIO_NUM_42;


// ============================================================
// I2S HANDLE
// ============================================================

static i2s_chan_handle_t mic_rx_handle =
    nullptr;


// ============================================================
// EMBEDDED ESP-DL MODEL
// ============================================================

extern const uint8_t kws_model[]
    asm("_binary_kws_3class_espdl_start");


// ============================================================
// EMBEDDED MFCC PARAMETERS
// ============================================================

extern const uint8_t hann_window_bin[]
    asm("_binary_hann_window_bin_start");

extern const uint8_t mel_filterbank_transposed_bin[]
    asm("_binary_mel_filterbank_transposed_bin_start");

extern const uint8_t dct_matrix_bin[]
    asm("_binary_dct_matrix_bin_start");


// ============================================================
// CLASS LABELS
// ============================================================

static const char *CLASS_NAMES[3] =
{
    "YES",
    "NO",
    "UP"
};


// ============================================================
// MOLeNET V7.1 ONBOARD ACTION LED
// ============================================================
//
// D6 = GPIO38
//
// GPIO HIGH -> LED ON
// GPIO LOW  -> LED OFF
//
// Actions:
//
// YES -> ON
// NO  -> OFF
// UP  -> blink 3 times
//
// ============================================================

static constexpr gpio_num_t ACTION_LED =
    GPIO_NUM_38;


static bool action_led_state =
    false;


// ============================================================
// INITIALIZE ACTION LED
// ============================================================

static void init_action_led()
{
    gpio_config_t cfg = {};

    cfg.pin_bit_mask =
        (1ULL << ACTION_LED);

    cfg.mode =
        GPIO_MODE_OUTPUT;

    cfg.pull_up_en =
        GPIO_PULLUP_DISABLE;

    cfg.pull_down_en =
        GPIO_PULLDOWN_DISABLE;

    cfg.intr_type =
        GPIO_INTR_DISABLE;


    ESP_ERROR_CHECK(
        gpio_config(
            &cfg
        )
    );


    // Start OFF.

    gpio_set_level(
        ACTION_LED,
        0
    );


    action_led_state =
        false;


    ESP_LOGI(
        TAG,
        "Onboard action LED initialized on GPIO38 / D6"
    );
}


// ============================================================
// LED ON
// ============================================================

static void action_led_on()
{
    gpio_set_level(
        ACTION_LED,
        1
    );


    action_led_state =
        true;


    ESP_LOGI(
        TAG,
        "ACTION: YES -> D6 LED ON"
    );
}


// ============================================================
// LED OFF
// ============================================================

static void action_led_off()
{
    gpio_set_level(
        ACTION_LED,
        0
    );


    action_led_state =
        false;


    ESP_LOGI(
        TAG,
        "ACTION: NO -> D6 LED OFF"
    );
}


// ============================================================
// LED BLINK
// ============================================================

static void action_led_blink_three_times()
{
    // Remember previous state.

    const bool previous_state =
        action_led_state;


    ESP_LOGI(
        TAG,
        "ACTION: UP -> D6 LED BLINK 3 TIMES"
    );


    for (
        int i = 0;
        i < 3;
        i++
    )
    {
        gpio_set_level(
            ACTION_LED,
            1
        );


        vTaskDelay(
            pdMS_TO_TICKS(
                250
            )
        );


        gpio_set_level(
            ACTION_LED,
            0
        );


        vTaskDelay(
            pdMS_TO_TICKS(
                250
            )
        );
    }


    // Restore state from before blinking.

    gpio_set_level(
        ACTION_LED,
        previous_state ? 1 : 0
    );


    action_led_state =
        previous_state;
}


// ============================================================
// INITIALIZE INMP441
// ============================================================

static void init_microphone()
{
    ESP_LOGI(
        TAG,
        "Initializing INMP441..."
    );


    // ========================================================
    // I2S RX CHANNEL
    // ========================================================

    i2s_chan_config_t chan_cfg =
        I2S_CHANNEL_DEFAULT_CONFIG(
            I2S_NUM_1,
            I2S_ROLE_MASTER
        );


    ESP_ERROR_CHECK(
        i2s_new_channel(
            &chan_cfg,
            nullptr,
            &mic_rx_handle
        )
    );


    // ========================================================
    // I2S STANDARD CONFIG
    // ========================================================

    i2s_std_config_t rx_cfg = {};


    rx_cfg.clk_cfg =
        I2S_STD_CLK_DEFAULT_CONFIG(
            SAMPLE_RATE
        );


    rx_cfg.clk_cfg.mclk_multiple =
        I2S_MCLK_MULTIPLE_256;


    rx_cfg.slot_cfg =
        I2S_STD_PHILIPS_SLOT_DEFAULT_CONFIG(
            I2S_DATA_BIT_WIDTH_32BIT,
            I2S_SLOT_MODE_MONO
        );


    // ========================================================
    // MATCH WORKING MOLeNET / XIAOZHI CONFIG
    // ========================================================

    rx_cfg.slot_cfg.slot_mask =
        I2S_STD_SLOT_LEFT;


    rx_cfg.slot_cfg.ws_width =
        I2S_DATA_BIT_WIDTH_32BIT;


    rx_cfg.slot_cfg.ws_pol =
        false;


    rx_cfg.slot_cfg.bit_shift =
        true;


#ifdef I2S_HW_VERSION_2

    rx_cfg.slot_cfg.left_align =
        true;


    rx_cfg.slot_cfg.big_endian =
        false;


    rx_cfg.slot_cfg.bit_order_lsb =
        false;

#endif


    // ========================================================
    // GPIO
    // ========================================================

    rx_cfg.gpio_cfg.mclk =
        I2S_GPIO_UNUSED;


    rx_cfg.gpio_cfg.bclk =
        MIC_BCLK;


    rx_cfg.gpio_cfg.ws =
        MIC_WS;


    rx_cfg.gpio_cfg.dout =
        I2S_GPIO_UNUSED;


    rx_cfg.gpio_cfg.din =
        MIC_SD;


    rx_cfg.gpio_cfg.invert_flags.mclk_inv =
        false;


    rx_cfg.gpio_cfg.invert_flags.bclk_inv =
        false;


    rx_cfg.gpio_cfg.invert_flags.ws_inv =
        false;


    // ========================================================
    // INITIALIZE
    // ========================================================

    ESP_ERROR_CHECK(
        i2s_channel_init_std_mode(
            mic_rx_handle,
            &rx_cfg
        )
    );


    ESP_ERROR_CHECK(
        i2s_channel_enable(
            mic_rx_handle
        )
    );


    ESP_LOGI(
        TAG,
        "INMP441 initialized successfully."
    );


    ESP_LOGI(
        TAG,
        "Sample rate : %d Hz",
        SAMPLE_RATE
    );


    ESP_LOGI(
        TAG,
        "SCK/BCLK    : GPIO%d",
        MIC_BCLK
    );


    ESP_LOGI(
        TAG,
        "WS          : GPIO%d",
        MIC_WS
    );


    ESP_LOGI(
        TAG,
        "SD          : GPIO%d",
        MIC_SD
    );


    ESP_LOGI(
        TAG,
        "Channel     : LEFT"
    );
}


// ============================================================
// RECORD TWO SECONDS
// ============================================================

static bool record_two_seconds(
    int16_t *capture
)
{
    static constexpr int BLOCK_SIZE =
        512;


    int32_t raw_buffer[
        BLOCK_SIZE
    ];


    int collected =
        0;


    ESP_LOGI(
        TAG,
        "========================================"
    );


    ESP_LOGI(
        TAG,
        "RECORDING NOW"
    );


    ESP_LOGI(
        TAG,
        "Say ONE word: YES, NO or UP"
    );


    ESP_LOGI(
        TAG,
        "You have %d seconds.",
        CAPTURE_SECONDS
    );


    ESP_LOGI(
        TAG,
        "========================================"
    );


    while (
        collected <
        CAPTURE_SAMPLES
    )
    {
        const int remaining =
            CAPTURE_SAMPLES -
            collected;


        const int requested =
            remaining < BLOCK_SIZE
            ?
            remaining
            :
            BLOCK_SIZE;


        size_t bytes_read =
            0;


        esp_err_t err =
            i2s_channel_read(
                mic_rx_handle,
                raw_buffer,
                requested *
                    sizeof(int32_t),
                &bytes_read,
                portMAX_DELAY
            );


        if (
            err !=
            ESP_OK
        )
        {
            ESP_LOGE(
                TAG,
                "I2S read failed: %s",
                esp_err_to_name(err)
            );


            return false;
        }


        const int samples_read =
            bytes_read /
            sizeof(int32_t);


        if (
            samples_read <=
            0
        )
        {
            ESP_LOGE(
                TAG,
                "No microphone samples received."
            );


            return false;
        }


        // ====================================================
        // 32-BIT I2S -> SIGNED 16-BIT PCM
        // ========================================================

        for (
            int i = 0;
            i < samples_read;
            i++
        )
        {
            int32_t value =
                raw_buffer[i] >> 16;


            if (
                value >
                INT16_MAX
            )
            {
                value =
                    INT16_MAX;
            }


            if (
                value <
                INT16_MIN
            )
            {
                value =
                    INT16_MIN;
            }


            capture[
                collected
            ] =
                static_cast<int16_t>(
                    value
                );


            collected++;


            if (
                collected >=
                CAPTURE_SAMPLES
            )
            {
                break;
            }
        }
    }


    ESP_LOGI(
        TAG,
        "Two-second capture complete."
    );


    ESP_LOGI(
        TAG,
        "Captured samples : %d",
        collected
    );


    return true;
}


// ============================================================
// SELECT BEST ONE-SECOND SPEECH WINDOW
// ============================================================

static bool select_best_one_second(
    const int16_t *capture,
    float *audio
)
{
    if (
        CAPTURE_SAMPLES <
        AUDIO_SAMPLES
    )
    {
        ESP_LOGE(
            TAG,
            "Capture buffer is shorter than model window."
        );


        return false;
    }


    double best_energy =
        -1.0;


    int best_energy_start =
        0;


    // ========================================================
    // FIND HIGHEST ENERGY REGION
    // ========================================================

    for (
        int start = 0;
        start + ENERGY_WINDOW_SAMPLES <= CAPTURE_SAMPLES;
        start += ENERGY_HOP_SAMPLES
    )
    {
        double sum_squared =
            0.0;


        for (
            int i = 0;
            i < ENERGY_WINDOW_SAMPLES;
            i++
        )
        {
            const double sample =
                static_cast<double>(
                    capture[
                        start + i
                    ]
                );


            sum_squared +=
                sample *
                sample;
        }


        const double mean_energy =
            sum_squared /
            ENERGY_WINDOW_SAMPLES;


        if (
            mean_energy >
            best_energy
        )
        {
            best_energy =
                mean_energy;


            best_energy_start =
                start;
        }
    }


    const int best_energy_center =
        best_energy_start +
        ENERGY_WINDOW_SAMPLES / 2;


    int selected_start =
        best_energy_center -
        AUDIO_SAMPLES / 2;


    if (
        selected_start <
        0
    )
    {
        selected_start =
            0;
    }


    const int latest_start =
        CAPTURE_SAMPLES -
        AUDIO_SAMPLES;


    if (
        selected_start >
        latest_start
    )
    {
        selected_start =
            latest_start;
    }


    // ========================================================
    // COPY SELECTED ONE-SECOND REGION
    // ========================================================

    for (
        int i = 0;
        i < AUDIO_SAMPLES;
        i++
    )
    {
        audio[i] =
            static_cast<float>(
                capture[
                    selected_start + i
                ]
            )
            /
            32768.0f;
    }


    // ========================================================
    // REMOVE DC OFFSET
    // ========================================================

    double mean =
        0.0;


    for (
        int i = 0;
        i < AUDIO_SAMPLES;
        i++
    )
    {
        mean +=
            audio[i];
    }


    mean /=
        AUDIO_SAMPLES;


    for (
        int i = 0;
        i < AUDIO_SAMPLES;
        i++
    )
    {
        audio[i] -=
            static_cast<float>(
                mean
            );
    }


    // ========================================================
    // MEASURE SELECTED WINDOW
    // ========================================================

    float minimum =
        1.0f;


    float maximum =
        -1.0f;


    float peak =
        0.0f;


    double sum_squared =
        0.0;


    int clipped_samples =
        0;


    for (
        int i = 0;
        i < AUDIO_SAMPLES;
        i++
    )
    {
        const float sample =
            audio[i];


        if (
            sample <
            minimum
        )
        {
            minimum =
                sample;
        }


        if (
            sample >
            maximum
        )
        {
            maximum =
                sample;
        }


        const float absolute =
            fabsf(
                sample
            );


        if (
            absolute >
            peak
        )
        {
            peak =
                absolute;
        }


        if (
            absolute >=
            CLIP_LEVEL
        )
        {
            clipped_samples++;
        }


        sum_squared +=
            static_cast<double>(
                sample
            )
            *
            static_cast<double>(
                sample
            );
    }


    const float rms =
        sqrtf(
            static_cast<float>(
                sum_squared /
                AUDIO_SAMPLES
            )
        );


    last_audio_rms =
        rms;


    last_audio_peak =
        peak;


    last_clipped_fraction =
        static_cast<float>(
            clipped_samples
        )
        /
        static_cast<float>(
            AUDIO_SAMPLES
        );


    last_selected_start_seconds =
        static_cast<float>(
            selected_start
        )
        /
        static_cast<float>(
            SAMPLE_RATE
        );


    ESP_LOGI(
        TAG,
        "========================================"
    );


    ESP_LOGI(
        TAG,
        "AUTO SPEECH WINDOW"
    );


    ESP_LOGI(
        TAG,
        "Selected start : %.3f s",
        last_selected_start_seconds
    );


    ESP_LOGI(
        TAG,
        "Selected end   : %.3f s",
        last_selected_start_seconds +
            1.0f
    );


    ESP_LOGI(
        TAG,
        "Audio min      : %.6f",
        minimum
    );


    ESP_LOGI(
        TAG,
        "Audio max      : %.6f",
        maximum
    );


    ESP_LOGI(
        TAG,
        "Audio peak     : %.6f",
        last_audio_peak
    );


    ESP_LOGI(
        TAG,
        "Audio RMS      : %.6f",
        last_audio_rms
    );


    ESP_LOGI(
        TAG,
        "Clipped        : %.2f %%",
        last_clipped_fraction *
            100.0f
    );


    ESP_LOGI(
        TAG,
        "========================================"
    );


    return true;
}


// ============================================================
// TORCHAUDIO REFLECT PADDING
// ============================================================

static inline float get_reflected_sample(
    const float *audio,
    int index
)
{
    if (
        index < 0
    )
    {
        index =
            -index;
    }


    if (
        index >=
        AUDIO_SAMPLES
    )
    {
        index =
            2 *
            AUDIO_SAMPLES
            -
            2
            -
            index;
    }


    return audio[
        index
    ];
}


// ============================================================
// EXACT THESIS MFCC
// ============================================================

static bool compute_mfcc(
    const float *audio,
    float *output_mfcc
)
{
    ESP_LOGI(
        TAG,
        "Calculating MFCC..."
    );


    const int64_t start_us =
        esp_timer_get_time();


    const float *hann =
        reinterpret_cast<const float *>(
            hann_window_bin
        );


    const float *mel_filterbank =
        reinterpret_cast<const float *>(
            mel_filterbank_transposed_bin
        );


    const float *dct =
        reinterpret_cast<const float *>(
            dct_matrix_bin
        );


    // ========================================================
    // FFT CONFIG
    // ========================================================

    kiss_fftr_cfg fft_cfg =
        kiss_fftr_alloc(
            N_FFT,
            0,
            nullptr,
            nullptr
        );


    if (
        fft_cfg == nullptr
    )
    {
        ESP_LOGE(
            TAG,
            "Could not allocate FFT."
        );


        return false;
    }


    // ========================================================
    // WORKING BUFFERS
    // ========================================================

    std::vector<kiss_fft_scalar>
        fft_input(
            N_FFT
        );


    std::vector<kiss_fft_cpx>
        fft_output(
            N_FREQ
        );


    std::vector<float>
        power(
            N_FREQ
        );


    std::vector<float>
        mel_db(
            N_MELS *
            N_FRAMES
        );


    float global_max_db =
        -1.0e30f;


    // ========================================================
    // PROCESS 101 FRAMES
    // ========================================================

    for (
        int frame = 0;
        frame < N_FRAMES;
        frame++
    )
    {
        const int frame_start =
            frame *
            HOP_LENGTH
            -
            N_FFT / 2;


        // ====================================================
        // BUILD FFT FRAME
        // ========================================================

        for (
            int n = 0;
            n < N_FFT;
            n++
        )
        {
            if (
                n < WINDOW_OFFSET
                ||
                n >=
                WINDOW_OFFSET +
                WIN_LENGTH
            )
            {
                fft_input[n] =
                    0.0f;
            }

            else
            {
                const int audio_index =
                    frame_start + n;


                const float sample =
                    get_reflected_sample(
                        audio,
                        audio_index
                    );


                const int hann_index =
                    n -
                    WINDOW_OFFSET;


                fft_input[n] =
                    sample *
                    hann[
                        hann_index
                    ];
            }
        }


        // ====================================================
        // FFT
        // ========================================================

        kiss_fftr(
            fft_cfg,
            fft_input.data(),
            fft_output.data()
        );


        // ====================================================
        // POWER SPECTRUM
        // ========================================================

        for (
            int k = 0;
            k < N_FREQ;
            k++
        )
        {
            const float real =
                fft_output[k].r;


            const float imag =
                fft_output[k].i;


            power[k] =
                real * real
                +
                imag * imag;
        }


        // ====================================================
        // MEL FILTERBANK
        // ========================================================

        for (
            int mel = 0;
            mel < N_MELS;
            mel++
        )
        {
            float mel_energy =
                0.0f;


            const float *filter =
                &mel_filterbank[
                    mel *
                    N_FREQ
                ];


            for (
                int k = 0;
                k < N_FREQ;
                k++
            )
            {
                mel_energy +=
                    power[k]
                    *
                    filter[k];
            }


            if (
                mel_energy <
                1.0e-10f
            )
            {
                mel_energy =
                    1.0e-10f;
            }


            const float db =
                10.0f *
                log10f(
                    mel_energy
                );


            mel_db[
                mel *
                N_FRAMES
                +
                frame
            ] = db;


            if (
                db >
                global_max_db
            )
            {
                global_max_db =
                    db;
            }
        }


        if (
            (frame % 8) == 7
        )
        {
            vTaskDelay(1);
        }
    }


    free(
        fft_cfg
    );


    // ========================================================
    // TORCHAUDIO TOP_DB = 80
    // ========================================================

    const float minimum_db =
        global_max_db
        -
        80.0f;


    for (
        int i = 0;
        i <
        N_MELS *
        N_FRAMES;
        i++
    )
    {
        if (
            mel_db[i] <
            minimum_db
        )
        {
            mel_db[i] =
                minimum_db;
        }
    }


    // ========================================================
    // DCT-II
    // ========================================================

    for (
        int mfcc = 0;
        mfcc < N_MFCC;
        mfcc++
    )
    {
        for (
            int frame = 0;
            frame < N_FRAMES;
            frame++
        )
        {
            float sum =
                0.0f;


            for (
                int mel = 0;
                mel < N_MELS;
                mel++
            )
            {
                const float mel_value =
                    mel_db[
                        mel *
                        N_FRAMES
                        +
                        frame
                    ];


                const float dct_value =
                    dct[
                        mel *
                        N_MFCC
                        +
                        mfcc
                    ];


                sum +=
                    mel_value *
                    dct_value;
            }


            output_mfcc[
                mfcc *
                N_FRAMES
                +
                frame
            ] = sum;
        }


        if (
            (mfcc % 8) == 7
        )
        {
            vTaskDelay(1);
        }
    }


    // ========================================================
    // TIMING
    // ========================================================

    const int64_t end_us =
        esp_timer_get_time();


    const double elapsed_ms =
        static_cast<double>(
            end_us -
            start_us
        )
        /
        1000.0;


    ESP_LOGI(
        TAG,
        "MFCC complete."
    );


    ESP_LOGI(
        TAG,
        "Mel dB range: %.4f to %.4f",
        minimum_db,
        global_max_db
    );


    ESP_LOGI(
        TAG,
        "MFCC processing time: %.2f ms",
        elapsed_ms
    );


    return true;
}


// ============================================================
// RUN ESP-DL MODEL
// ============================================================

static void run_model(
    dl::Model *model,
    const float *mfcc
)
{
    ESP_LOGI(
        TAG,
        "Running keyword model..."
    );


    const int64_t start_us =
        esp_timer_get_time();


    dl::TensorBase *model_input =
        model->get_input();


    dl::TensorBase *model_output =
        model->get_output();


    if (
        model_input == nullptr
        ||
        model_output == nullptr
    )
    {
        ESP_LOGE(
            TAG,
            "Could not get model tensors."
        );


        return;
    }


    // ========================================================
    // ASSIGN FLOAT MFCC
    // ========================================================

    const bool input_ok =
        model_input->assign(
            model_input->get_shape(),
            mfcc,
            0,
            dl::DATA_TYPE_FLOAT
        );


    if (
        !input_ok
    )
    {
        ESP_LOGE(
            TAG,
            "Could not assign model input."
        );


        return;
    }


    // ========================================================
    // INFERENCE
    // ========================================================

    model->run();


    // ========================================================
    // CONVERT OUTPUT TO FLOAT
    // ========================================================

    dl::TensorBase float_output(
        model_output->get_shape(),
        nullptr,
        0,
        dl::DATA_TYPE_FLOAT
    );


    const bool output_ok =
        float_output.assign(
            model_output
        );


    if (
        !output_ok
    )
    {
        ESP_LOGE(
            TAG,
            "Could not convert output."
        );


        return;
    }


    float *logits =
        float_output
            .get_element_ptr<float>();


    // ========================================================
    // SOFTMAX
    // ========================================================

    float max_logit =
        logits[0];


    for (
        int i = 1;
        i < 3;
        i++
    )
    {
        if (
            logits[i] >
            max_logit
        )
        {
            max_logit =
                logits[i];
        }
    }


    float probabilities[3];


    float total =
        0.0f;


    for (
        int i = 0;
        i < 3;
        i++
    )
    {
        probabilities[i] =
            expf(
                logits[i] -
                max_logit
            );


        total +=
            probabilities[i];
    }


    for (
        int i = 0;
        i < 3;
        i++
    )
    {
        probabilities[i] /=
            total;
    }


    // ========================================================
    // WINNER
    // ========================================================

    int prediction =
        0;


    for (
        int i = 1;
        i < 3;
        i++
    )
    {
        if (
            probabilities[i] >
            probabilities[
                prediction
            ]
        )
        {
            prediction =
                i;
        }
    }


    const float confidence =
        probabilities[
            prediction
        ];


    const int64_t end_us =
        esp_timer_get_time();


    const double inference_ms =
        static_cast<double>(
            end_us -
            start_us
        )
        /
        1000.0;


    // ========================================================
    // PRINT RESULT
    // ========================================================

    printf("\n");


    printf(
        "========================================\n"
    );


    printf(
        "LIVE KEYWORD RESULT\n"
    );


    printf(
        "========================================\n"
    );


    printf(
        "YES  : %6.2f %%\n",
        probabilities[0] *
            100.0f
    );


    printf(
        "NO   : %6.2f %%\n",
        probabilities[1] *
            100.0f
    );


    printf(
        "UP   : %6.2f %%\n",
        probabilities[2] *
            100.0f
    );


    printf("\n");


    if (
        confidence >=
        MIN_CONFIDENCE
    )
    {
        printf(
            "Prediction : %s\n",
            CLASS_NAMES[
                prediction
            ]
        );
    }

    else
    {
        printf(
            "Prediction : UNKNOWN\n"
        );
    }


    printf(
        "Confidence : %.2f %%\n",
        confidence *
            100.0f
    );


    printf(
        "Audio RMS  : %.6f\n",
        last_audio_rms
    );


    printf(
        "Audio peak : %.6f\n",
        last_audio_peak
    );


    printf(
        "Window     : %.3f - %.3f s\n",
        last_selected_start_seconds,
        last_selected_start_seconds +
            1.0f
    );


    printf(
        "Inference  : %.2f ms\n",
        inference_ms
    );


    printf(
        "========================================\n"
    );


    printf("\n");


    // ========================================================
    // HARDWARE ACTION
    // ========================================================

    if (
        confidence >=
        MIN_CONFIDENCE
    )
    {
        if (
            prediction == 0
        )
        {
            // YES

            action_led_on();
        }

        else if (
            prediction == 1
        )
        {
            // NO

            action_led_off();
        }

        else if (
            prediction == 2
        )
        {
            // UP

            action_led_blink_three_times();
        }
    }

    else
    {
        ESP_LOGI(
            TAG,
            "Confidence %.2f%% too low. No LED action.",
            confidence *
                100.0f
        );
    }
}


// ============================================================
// MAIN
// ============================================================

extern "C" void app_main(void)
{
    // ========================================================
    // STARTUP INFORMATION
    // ========================================================

    ESP_LOGI(
        TAG,
        "========================================"
    );


    ESP_LOGI(
        TAG,
        "LIVE KEYWORD SPOTTING"
    );


    ESP_LOGI(
        TAG,
        "MoleNet V7.1 + INMP441"
    );


    ESP_LOGI(
        TAG,
        "YES / NO / UP"
    );


    ESP_LOGI(
        TAG,
        "========================================"
    );


    ESP_LOGI(
        TAG,
        "Capture     : %d seconds",
        CAPTURE_SECONDS
    );


    ESP_LOGI(
        TAG,
        "Model audio : 16 kHz / 1 second"
    );


    ESP_LOGI(
        TAG,
        "MFCC        : 40 x 101"
    );


    ESP_LOGI(
        TAG,
        "Silence RMS : %.6f",
        SILENCE_RMS_THRESHOLD
    );


    ESP_LOGI(
        TAG,
        "Confidence  : %.0f %%",
        MIN_CONFIDENCE *
            100.0f
    );


    // ========================================================
    // MICROPHONE
    // ========================================================

    init_microphone();


    // ========================================================
    // ACTION LED
    // ========================================================

    init_action_led();


    // ========================================================
    // STARTUP LED TEST
    // ========================================================
    //
    // D6 / GPIO38 should blink 5 times.
    //
    // THIS TELLS YOU EXACTLY WHICH PHYSICAL LED IS CONTROLLED.
    //
    // After the test it is left OFF.
    //
    // ========================================================

    ESP_LOGI(
        TAG,
        "========================================"
    );


    ESP_LOGI(
        TAG,
        "Testing D6 / GPIO38 LED..."
    );


    for (
        int i = 0;
        i < 5;
        i++
    )
    {
        gpio_set_level(
            ACTION_LED,
            1
        );


        vTaskDelay(
            pdMS_TO_TICKS(
                500
            )
        );


        gpio_set_level(
            ACTION_LED,
            0
        );


        vTaskDelay(
            pdMS_TO_TICKS(
                500
            )
        );
    }


    action_led_state =
        false;


    gpio_set_level(
        ACTION_LED,
        0
    );


    ESP_LOGI(
        TAG,
        "D6 / GPIO38 LED test complete."
    );


    ESP_LOGI(
        TAG,
        "D6 should now be OFF."
    );


    ESP_LOGI(
        TAG,
        "========================================"
    );


    // ========================================================
    // LOAD MODEL
    // ========================================================

    ESP_LOGI(
        TAG,
        "Loading ESP-DL model..."
    );


    dl::Model *model =
        new dl::Model(
            (const char *)kws_model,
            fbs::MODEL_LOCATION_IN_FLASH_RODATA
        );


    if (
        model == nullptr
    )
    {
        ESP_LOGE(
            TAG,
            "Model loading failed."
        );


        return;
    }


    ESP_LOGI(
        TAG,
        "Model loaded successfully."
    );


    dl::TensorBase *model_input =
        model->get_input();


    dl::TensorBase *model_output =
        model->get_output();


    if (
        model_input != nullptr
        &&
        model_output != nullptr
    )
    {
        ESP_LOGI(
            TAG,
            "Model input size  : %d",
            model_input->get_size()
        );


        ESP_LOGI(
            TAG,
            "Model output size : %d",
            model_output->get_size()
        );
    }


    // ========================================================
    // BUFFERS
    // ========================================================

    std::vector<int16_t> capture(
        CAPTURE_SAMPLES
    );


    std::vector<float> audio(
        AUDIO_SAMPLES
    );


    std::vector<float> mfcc(
        N_MFCC *
        N_FRAMES
    );


    // ========================================================
    // LIVE LOOP
    // ========================================================

    while (
        true
    )
    {
        printf("\n\n");


        ESP_LOGI(
            TAG,
            "========================================"
        );


        ESP_LOGI(
            TAG,
            "GET READY"
        );


        ESP_LOGI(
            TAG,
            "Prepare to say ONE word: YES, NO or UP"
        );


        ESP_LOGI(
            TAG,
            "========================================"
        );


        // ====================================================
        // COUNTDOWN
        // ========================================================

        for (
            int seconds = 3;
            seconds >= 1;
            seconds--
        )
        {
            ESP_LOGI(
                TAG,
                "%d...",
                seconds
            );


            vTaskDelay(
                pdMS_TO_TICKS(
                    1200
                )
            );
        }


        // ====================================================
        // SPEAK
        // ========================================================

        ESP_LOGI(
            TAG,
            "========================================"
        );


        ESP_LOGI(
            TAG,
            "SPEAK NOW!"
        );


        ESP_LOGI(
            TAG,
            "Say the word anytime during the next %d seconds.",
            CAPTURE_SECONDS
        );


        ESP_LOGI(
            TAG,
            "Speak."
        );


        ESP_LOGI(
            TAG,
            "========================================"
        );


        // ====================================================
        // RECORD TWO SECONDS
        // ========================================================

        if (
            !record_two_seconds(
                capture.data()
            )
        )
        {
            ESP_LOGE(
                TAG,
                "Recording failed."
            );


            vTaskDelay(
                pdMS_TO_TICKS(
                    3000
                )
            );


            continue;
        }


        // ====================================================
        // SELECT BEST ONE-SECOND WINDOW
        // ========================================================

        if (
            !select_best_one_second(
                capture.data(),
                audio.data()
            )
        )
        {
            ESP_LOGE(
                TAG,
                "Could not select speech window."
            );


            vTaskDelay(
                pdMS_TO_TICKS(
                    3000
                )
            );


            continue;
        }


        // ====================================================
        // SILENCE CHECK
        // ========================================================

        if (
            last_audio_rms <
            SILENCE_RMS_THRESHOLD
        )
        {
            printf("\n");


            printf(
                "========================================\n"
            );


            printf(
                "LIVE KEYWORD RESULT\n"
            );


            printf(
                "========================================\n"
            );


            printf(
                "SILENCE / TOO QUIET\n"
            );


            printf(
                "Audio RMS : %.6f\n",
                last_audio_rms
            );


            printf(
                "Threshold : %.6f\n",
                SILENCE_RMS_THRESHOLD
            );


            printf(
                "Model was NOT run.\n"
            );


            printf(
                "LED was NOT changed.\n"
            );


            printf(
                "========================================\n"
            );


            printf("\n");


            ESP_LOGI(
                TAG,
                "Next test in 3 seconds..."
            );


            vTaskDelay(
                pdMS_TO_TICKS(
                    3000
                )
            );


            continue;
        }


        // ====================================================
        // CLIPPING CHECK
        // ========================================================

        if (
            last_clipped_fraction >
            MAX_CLIPPED_FRACTION
        )
        {
            printf("\n");


            printf(
                "========================================\n"
            );


            printf(
                "AUDIO CLIPPED\n"
            );


            printf(
                "Speak normally and move farther from mic.\n"
            );


            printf(
                "Peak      : %.6f\n",
                last_audio_peak
            );


            printf(
                "Clipped   : %.2f %%\n",
                last_clipped_fraction *
                    100.0f
            );


            printf(
                "Model was NOT run.\n"
            );


            printf(
                "LED was NOT changed.\n"
            );


            printf(
                "========================================\n"
            );


            printf("\n");


            ESP_LOGI(
                TAG,
                "Next test in 3 seconds..."
            );


            vTaskDelay(
                pdMS_TO_TICKS(
                    3000
                )
            );


            continue;
        }


        // ====================================================
        // SPEECH ACCEPTED
        // ========================================================

        ESP_LOGI(
            TAG,
            "Speech window accepted."
        );


        ESP_LOGI(
            TAG,
            "Audio RMS %.6f",
            last_audio_rms
        );


        // ====================================================
        // MFCC
        // ========================================================

        if (
            !compute_mfcc(
                audio.data(),
                mfcc.data()
            )
        )
        {
            ESP_LOGE(
                TAG,
                "MFCC calculation failed."
            );


            vTaskDelay(
                pdMS_TO_TICKS(
                    3000
                )
            );


            continue;
        }


        // ====================================================
        // MODEL + LED ACTION
        // ========================================================

        run_model(
            model,
            mfcc.data()
        );


        // ====================================================
        // NEXT TEST
        // ========================================================

        ESP_LOGI(
            TAG,
            "========================================"
        );


        ESP_LOGI(
            TAG,
            "Result complete."
        );


        ESP_LOGI(
            TAG,
            "Next test in 3 seconds..."
        );


        ESP_LOGI(
            TAG,
            "========================================"
        );


        vTaskDelay(
            pdMS_TO_TICKS(
                3000
            )
        );
    }
}