#include "py/obj.h"
#include "py/runtime.h"
#include <math.h>
#include <stdint.h>

// FIX: Define M_PI if it's not already available in math.h
#ifndef M_PI
#define M_PI 3.14159265358979323846f
#endif

// Filter type constants, matching the C enum
enum { LPF, HPF, BPF, NOTCH, PEQ, LSH, HSH };

// Biquad filter state using floating-point numbers
typedef struct _biquad_state_t {
  float a0, a1, a2, b1, b2; // Coefficients
  float x1, x2, y1, y2;     // State variables
} biquad_state_t;

// The MicroPython object that holds the biquad state
typedef struct _audiodsp_biquad_obj_t {
  mp_obj_base_t base;
  biquad_state_t state;
} audiodsp_biquad_obj_t;

extern const mp_obj_type_t audiodsp_biquad_type;

// Constructor for the Biquad object in Python
static mp_obj_t biquad_make_new(const mp_obj_type_t *type, size_t n_args,
                                size_t n_kw, const mp_obj_t *all_args) {
  enum { ARG_type, ARG_Fc, ARG_Q, ARG_peakGainDB };
  static const mp_arg_t allowed_args[] = {
      {MP_QSTR_type, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0}},
      {MP_QSTR_Fc, MP_ARG_REQUIRED | MP_ARG_OBJ, {.u_rom_obj = MP_ROM_NONE}},
      {MP_QSTR_Q, MP_ARG_REQUIRED | MP_ARG_OBJ, {.u_rom_obj = MP_ROM_NONE}},
      {MP_QSTR_peakGainDB,
       MP_ARG_KW_ONLY | MP_ARG_OBJ,
       {.u_rom_obj = MP_ROM_NONE}},
  };

  mp_arg_val_t args_out[MP_ARRAY_SIZE(allowed_args)];
  mp_arg_parse_all_kw_array(n_args, n_kw, all_args, MP_ARRAY_SIZE(allowed_args),
                            allowed_args, args_out);

  int ftype = args_out[ARG_type].u_int;
  float Fc = mp_obj_get_float(args_out[ARG_Fc].u_obj);
  float Q = mp_obj_get_float(args_out[ARG_Q].u_obj);

  float peakGainDB = 0.0f;
  if (args_out[ARG_peakGainDB].u_obj != mp_const_none) {
    peakGainDB = mp_obj_get_float(args_out[ARG_peakGainDB].u_obj);
  }

  audiodsp_biquad_obj_t *self = mp_obj_malloc(audiodsp_biquad_obj_t, type);

  float a0, a1, a2, b1, b2;
  float norm;
  float V = powf(10.0f, fabsf(peakGainDB) / 20.0f);
  float K = tanf(M_PI * Fc);

  switch (ftype) {
  case LPF:
    norm = 1.0f / (1.0f + K / Q + K * K);
    a0 = K * K * norm;
    a1 = 2.0f * a0;
    a2 = a0;
    b1 = 2.0f * (K * K - 1.0f) * norm;
    b2 = (1.0f - K / Q + K * K) * norm;
    break;
  case HPF:
    norm = 1.0f / (1.0f + K / Q + K * K);
    a0 = 1.0f * norm;
    a1 = -2.0f * a0;
    a2 = a0;
    b1 = 2.0f * (K * K - 1.0f) * norm;
    b2 = (1.0f - K / Q + K * K) * norm;
    break;
  case BPF:
    norm = 1.0f / (1.0f + K / Q + K * K);
    a0 = K / Q * norm;
    a1 = 0.0f;
    a2 = -a0;
    b1 = 2.0f * (K * K - 1.0f) * norm;
    b2 = (1.0f - K / Q + K * K) * norm;
    break;
  case NOTCH:
    norm = 1.0f / (1.0f + K / Q + K * K);
    a0 = (1.0f + K * K) * norm;
    a1 = 2.0f * (K * K - 1.0f) * norm;
    a2 = a0;
    b1 = a1;
    b2 = (1.0f - K / Q + K * K) * norm;
    break;
  case PEQ:
    if (peakGainDB >= 0) { // boost
      norm = 1.0f / (1.0f + 1.0f / Q * K + K * K);
      a0 = (1.0f + V / Q * K + K * K) * norm;
      a1 = 2.0f * (K * K - 1.0f) * norm;
      a2 = (1.0f - V / Q * K + K * K) * norm;
      b1 = a1;
      b2 = (1.0f - 1.0f / Q * K + K * K) * norm;
    } else { // cut
      norm = 1.0f / (1.0f + V / Q * K + K * K);
      a0 = (1.0f + 1.0f / Q * K + K * K) * norm;
      a1 = 2.0f * (K * K - 1.0f) * norm;
      a2 = (1.0f - 1.0f / Q * K + K * K) * norm;
      b1 = a1;
      b2 = (1.0f - V / Q * K + K * K) * norm;
    }
    break;
  case LSH:
    if (peakGainDB >= 0) { // boost
      norm = 1.0f / (1.0f + sqrtf(2.0f) * K + K * K);
      a0 = (1.0f + sqrtf(2.0f * V) * K + V * K * K) * norm;
      a1 = 2.0f * (V * K * K - 1.0f) * norm;
      a2 = (1.0f - sqrtf(2.0f * V) * K + V * K * K) * norm;
      b1 = 2.0f * (K * K - 1.0f) * norm;
      b2 = (1.0f - sqrtf(2.0f) * K + K * K) * norm;
    } else { // cut
      norm = 1.0f / (1.0f + sqrtf(2.0f * V) * K + V * K * K);
      a0 = (1.0f + sqrtf(2.0f) * K + K * K) * norm;
      a1 = 2.0f * (K * K - 1.0f) * norm;
      a2 = (1.0f - sqrtf(2.0f) * K + K * K) * norm;
      b1 = 2.0f * (V * K * K - 1.0f) * norm;
      b2 = (1.0f - sqrtf(2.0f * V) * K + V * K * K) * norm;
    }
    break;
  case HSH:
    if (peakGainDB >= 0) { // boost
      norm = 1.0f / (1.0f + sqrtf(2.0f) * K + K * K);
      a0 = (V + sqrtf(2.0f * V) * K + K * K) * norm;
      a1 = 2.0f * (K * K - V) * norm;
      a2 = (V - sqrtf(2.0f * V) * K + K * K) * norm;
      b1 = 2.0f * (K * K - 1.0f) * norm;
      b2 = (1.0f - sqrtf(2.0f) * K + K * K) * norm;
    } else { // cut
      norm = 1.0f / (V + sqrtf(2.0f * V) * K + K * K);
      a0 = (1.0f + sqrtf(2.0f) * K + K * K) * norm;
      a1 = 2.0f * (K * K - 1.0f) * norm;
      a2 = (1.0f - sqrtf(2.0f) * K + K * K) * norm;
      b1 = 2.0f * (K * K - V) * norm;
      b2 = (V - sqrtf(2.0f * V) * K + K * K) * norm;
    }
    break;
  default:
    mp_raise_ValueError(MP_ERROR_TEXT("Unknown or unsupported filter type"));
    break;
  }

  self->state.a0 = a0;
  self->state.a1 = a1;
  self->state.a2 = a2;
  self->state.b1 = b1;
  self->state.b2 = b2;
  self->state.x1 = 0.0f;
  self->state.x2 = 0.0f;
  self->state.y1 = 0.0f;
  self->state.y2 = 0.0f;

  return MP_OBJ_FROM_PTR(self);
}

MP_DEFINE_CONST_OBJ_TYPE(audiodsp_biquad_type, MP_QSTR_Biquad,
                         MP_TYPE_FLAG_NONE, make_new, biquad_make_new);

static inline float apply_biquad(biquad_state_t *state, float input) {
  float acc = state->a0 * input + state->a1 * state->x1 + state->a2 * state->x2;
  float feedback = state->b1 * state->y1 + state->b2 * state->y2;
  float output = acc - feedback;
  state->x2 = state->x1;
  state->x1 = input;
  state->y2 = state->y1;
  state->y1 = output;
  return output;
}

// Replacement for audiodsp_process_stereo
static mp_obj_t audiodsp_process(size_t n_args, const mp_obj_t *args) {
  // 1. Get all buffer objects and parameters from Python arguments
  mp_buffer_info_t dest_bufinfo;
  mp_get_buffer_raise(args[0], &dest_bufinfo, MP_BUFFER_WRITE);
  mp_buffer_info_t src1_bufinfo;
  mp_get_buffer_raise(args[1], &src1_bufinfo, MP_BUFFER_READ);
  mp_buffer_info_t src2_bufinfo;
  mp_get_buffer_raise(args[2], &src2_bufinfo, MP_BUFFER_READ);

  audiodsp_biquad_obj_t *lpf_l = MP_OBJ_TO_PTR(args[3]);
  audiodsp_biquad_obj_t *hpf_l = MP_OBJ_TO_PTR(args[4]);
  audiodsp_biquad_obj_t *lpf_r = MP_OBJ_TO_PTR(args[5]);
  audiodsp_biquad_obj_t *hpf_r = MP_OBJ_TO_PTR(args[6]);

  // Mixer parameters
  float g1_base = mp_obj_get_float(args[7]);
  float g2_base = mp_obj_get_float(args[8]);
  float pan = mp_obj_get_float(args[9]);

  // EQ parameters
  float bass_l = mp_obj_get_float(args[10]);
  float treble_l = mp_obj_get_float(args[11]);
  float bass_r = mp_obj_get_float(args[12]);
  float treble_r = mp_obj_get_float(args[13]);

  // Master gain
  float master = mp_obj_get_float(args[14]);

  // 2. Determine processing length
  size_t n_samples_1 = src1_bufinfo.len / sizeof(int16_t);
  size_t n_samples_2 = src2_bufinfo.len / sizeof(int16_t);
  size_t n_samples = (n_samples_1 < n_samples_2) ? n_samples_1 : n_samples_2;

  if (dest_bufinfo.len < n_samples * sizeof(int16_t) * 2) {
    mp_raise_ValueError(MP_ERROR_TEXT("Destination buffer too small"));
  }

  int16_t *dest = dest_bufinfo.buf;
  int16_t *src1 = src1_bufinfo.buf;
  int16_t *src2 = src2_bufinfo.buf;

  // 3. Implement Pan logic
  float final_gain_l = g1_base;
  float final_gain_r = g2_base;
  if (pan > 0.0f) { // Pan towards right, reduce left channel gain
    final_gain_l *= (1.0f - pan);
  } else if (pan < 0.0f) {        // Pan towards left, reduce right channel gain
    final_gain_r *= (1.0f + pan); // pan is negative, so this is 1.0 - abs(pan)
  }

  // 4. Main processing loop
  for (size_t i = 0; i < n_samples; i++) {
    // Left Channel: Filter -> EQ -> Gain
    float sample_l_in = (float)src1[i];
    float low_l = apply_biquad(&lpf_l->state, sample_l_in);
    float high_l = apply_biquad(&hpf_l->state, sample_l_in);
    float sample_l_eq = (low_l * bass_l) + (high_l * treble_l);
    float final_l = sample_l_eq * final_gain_l * master;

    // Right Channel: Filter -> EQ -> Gain
    float sample_r_in = (float)src2[i];
    float low_r = apply_biquad(&lpf_r->state, sample_r_in);
    float high_r = apply_biquad(&hpf_r->state, sample_r_in);
    float sample_r_eq = (low_r * bass_r) + (high_r * treble_r);
    float final_r = sample_r_eq * final_gain_r * master;

    // 5. Clipping to 16-bit range
    if (final_l > 32767.0f)
      final_l = 32767.0f;
    else if (final_l < -32768.0f)
      final_l = -32768.0f;

    if (final_r > 32767.0f)
      final_r = 32767.0f;
    else if (final_r < -32768.0f)
      final_r = -32768.0f;

    // Write to stereo destination buffer
    dest[i * 2] = (int16_t)final_l;
    dest[i * 2 + 1] = (int16_t)final_r;
  }

  return mp_const_none;
}
// Update to accept 15 arguments and rename function object
MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(audiodsp_process_obj, 15, 15,
                                    audiodsp_process);

// --- Module Definition ---
static const mp_rom_map_elem_t audiodsp_module_globals_table[] = {
    {MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_audiodsp)},
    {MP_ROM_QSTR(MP_QSTR_Biquad), MP_ROM_PTR(&audiodsp_biquad_type)},
    // Update to use the new function object
    {MP_ROM_QSTR(MP_QSTR_process), MP_ROM_PTR(&audiodsp_process_obj)},
    // Expose filter type constants to Python
    {MP_ROM_QSTR(MP_QSTR_LPF), MP_ROM_INT(LPF)},
    {MP_ROM_QSTR(MP_QSTR_HPF), MP_ROM_INT(HPF)},
    {MP_ROM_QSTR(MP_QSTR_BPF), MP_ROM_INT(BPF)},
    {MP_ROM_QSTR(MP_QSTR_NOTCH), MP_ROM_INT(NOTCH)},
    {MP_ROM_QSTR(MP_QSTR_PEQ), MP_ROM_INT(PEQ)},
    {MP_ROM_QSTR(MP_QSTR_LSH), MP_ROM_INT(LSH)},
    {MP_ROM_QSTR(MP_QSTR_HSH), MP_ROM_INT(HSH)},
};
MP_DEFINE_CONST_DICT(audiodsp_module_globals, audiodsp_module_globals_table);

const mp_obj_module_t audiodsp_user_cmodule = {
    .base = {&mp_type_module},
    .globals = (mp_obj_dict_t *)&audiodsp_module_globals,
};

MP_REGISTER_MODULE(MP_QSTR_audiodsp, audiodsp_user_cmodule);