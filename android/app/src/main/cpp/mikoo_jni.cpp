#include <jni.h>

#include <algorithm>
#include <atomic>
#include <cctype>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <initializer_list>
#include <string>
#include <vector>

namespace {
std::atomic<bool> g_cancel{false};

constexpr uint32_t kVocab = 256;
constexpr uint32_t kEmbed = 128;
constexpr uint32_t kHidden = 256;
constexpr int kMaxGenerationTokens = 1024;
constexpr char kMagic[8] = {'M', 'K', 'G', 'R', 'U', '0', '1', '\0'};

struct BootstrapModel {
    bool loaded = false;
    std::vector<float> embedding;
    std::vector<float> weight_ih;
    std::vector<float> weight_hh;
    std::vector<float> bias_ih;
    std::vector<float> bias_hh;
    std::vector<float> output_weight;
    std::vector<float> output_bias;
    std::string path;

    void reset() {
        loaded = false;
        embedding.clear();
        weight_ih.clear();
        weight_hh.clear();
        bias_ih.clear();
        bias_hh.clear();
        output_weight.clear();
        output_bias.clear();
        path.clear();
    }
};

BootstrapModel g_model;
uint64_t g_generated_tokens = 0;

std::string jstring_to_utf8(JNIEnv* env, jstring value) {
    if (value == nullptr) return {};
    const char* chars = env->GetStringUTFChars(value, nullptr);
    if (chars == nullptr) return {};
    std::string result(chars);
    env->ReleaseStringUTFChars(value, chars);
    return result;
}

jstring utf8_to_jstring(JNIEnv* env, const std::string& value) {
    return env->NewStringUTF(value.c_str());
}

bool read_floats(std::ifstream& input, std::vector<float>& values) {
    if (values.empty()) return true;
    input.read(reinterpret_cast<char*>(values.data()),
               static_cast<std::streamsize>(values.size() * sizeof(float)));
    return input.good();
}

bool load_bootstrap_model(const std::string& path) {
    std::ifstream input(path, std::ios::binary);
    if (!input) return false;

    char magic[sizeof(kMagic)] = {};
    input.read(magic, sizeof(magic));
    if (!input || std::string(magic, sizeof(magic)) != std::string(kMagic, sizeof(kMagic))) {
        return false;
    }

    uint32_t vocab = 0;
    uint32_t embed = 0;
    uint32_t hidden = 0;
    uint32_t reserved = 0;
    input.read(reinterpret_cast<char*>(&vocab), sizeof(vocab));
    input.read(reinterpret_cast<char*>(&embed), sizeof(embed));
    input.read(reinterpret_cast<char*>(&hidden), sizeof(hidden));
    input.read(reinterpret_cast<char*>(&reserved), sizeof(reserved));
    if (!input || vocab != kVocab || embed != kEmbed || hidden != kHidden) return false;

    BootstrapModel candidate;
    candidate.embedding.resize(kVocab * kEmbed);
    candidate.weight_ih.resize(3 * kHidden * kEmbed);
    candidate.weight_hh.resize(3 * kHidden * kHidden);
    candidate.bias_ih.resize(3 * kHidden);
    candidate.bias_hh.resize(3 * kHidden);
    candidate.output_weight.resize(kVocab * kHidden);
    candidate.output_bias.resize(kVocab);

    if (!read_floats(input, candidate.embedding) ||
        !read_floats(input, candidate.weight_ih) ||
        !read_floats(input, candidate.weight_hh) ||
        !read_floats(input, candidate.bias_ih) ||
        !read_floats(input, candidate.bias_hh) ||
        !read_floats(input, candidate.output_weight) ||
        !read_floats(input, candidate.output_bias)) {
        return false;
    }

    candidate.loaded = true;
    candidate.path = path;
    g_model = std::move(candidate);
    return true;
}

float sigmoid(float value) {
    if (value >= 0.0f) {
        const float z = std::exp(-value);
        return 1.0f / (1.0f + z);
    }
    const float z = std::exp(value);
    return z / (1.0f + z);
}

void gru_step(uint8_t token, std::vector<float>& hidden,
              std::vector<float>& input_gate, std::vector<float>& recurrent_gate) {
    std::fill(input_gate.begin(), input_gate.end(), 0.0f);
    std::fill(recurrent_gate.begin(), recurrent_gate.end(), 0.0f);
    const float* x = &g_model.embedding[static_cast<size_t>(token) * kEmbed];

    for (uint32_t gate = 0; gate < 3; ++gate) {
        const size_t gate_offset = static_cast<size_t>(gate) * kHidden;
        for (uint32_t row = 0; row < kHidden; ++row) {
            float input_value = g_model.bias_ih[gate_offset + row];
            float recurrent_value = g_model.bias_hh[gate_offset + row];
            const size_t input_offset = gate_offset * kEmbed + row * kEmbed;
            const size_t hidden_offset = gate_offset * kHidden + row * kHidden;
            for (uint32_t column = 0; column < kEmbed; ++column) {
                input_value += g_model.weight_ih[input_offset + column] * x[column];
            }
            for (uint32_t column = 0; column < kHidden; ++column) {
                recurrent_value += g_model.weight_hh[hidden_offset + column] * hidden[column];
            }
            input_gate[gate_offset + row] = input_value;
            recurrent_gate[gate_offset + row] = recurrent_value;
        }
    }

    std::vector<float> next(kHidden, 0.0f);
    for (uint32_t row = 0; row < kHidden; ++row) {
        const float reset_gate = sigmoid(input_gate[row] + recurrent_gate[row]);
        const float update_gate = sigmoid(input_gate[kHidden + row] + recurrent_gate[kHidden + row]);
        const float candidate = std::tanh(input_gate[2 * kHidden + row] +
                                           reset_gate * recurrent_gate[2 * kHidden + row]);
        next[row] = (1.0f - update_gate) * candidate + update_gate * hidden[row];
    }
    hidden.swap(next);
}

std::string last_user_message(const std::string& prompt) {
    const std::string marker = "\nUser\n";
    const size_t position = prompt.rfind(marker);
    if (position != std::string::npos) return prompt.substr(position + marker.size());
    const std::string alternate = "\nUser: ";
    const size_t alternate_position = prompt.rfind(alternate);
    if (alternate_position != std::string::npos) return prompt.substr(alternate_position + alternate.size());
    return prompt;
}

std::string trim_generated(std::string generated) {
    const std::string end_marker = "<|end|>";
    const size_t end = generated.find(end_marker);
    if (end != std::string::npos) generated.erase(end);
    const std::string assistant_marker = "<|assistant|>";
    const size_t assistant = generated.find(assistant_marker);
    if (assistant != std::string::npos) generated.erase(0, assistant + assistant_marker.size());
    while (!generated.empty() && (generated.front() == '\n' || generated.front() == '\r' || generated.front() == ' ')) {
        generated.erase(generated.begin());
    }
    while (!generated.empty() && (generated.back() == '\n' || generated.back() == '\r' || generated.back() == ' ')) {
        generated.pop_back();
    }
    return generated;
}

std::string generate_with_bootstrap(const std::string& prompt, int max_tokens) {
    std::string user = last_user_message(prompt);
    if (user.size() > 1024) user = user.substr(user.size() - 1024);
    const std::string model_prompt = "<|user|>\n" + user + "\n<|assistant|>\n";
    std::vector<float> hidden(kHidden, 0.0f);
    std::vector<float> input_gate(3 * kHidden, 0.0f);
    std::vector<float> recurrent_gate(3 * kHidden, 0.0f);
    for (unsigned char byte : model_prompt) gru_step(byte, hidden, input_gate, recurrent_gate);

    std::string generated;
    const int limit = std::max(32, std::min(max_tokens, kMaxGenerationTokens));
    for (int index = 0; index < limit; ++index) {
        int best_token = 0;
        float best_score = -INFINITY;
        for (uint32_t token = 0; token < kVocab; ++token) {
            float score = g_model.output_bias[token];
            const size_t offset = static_cast<size_t>(token) * kHidden;
            for (uint32_t column = 0; column < kHidden; ++column) {
                score += g_model.output_weight[offset + column] * hidden[column];
            }
            if (score > best_score) {
                best_score = score;
                best_token = static_cast<int>(token);
            }
        }
        if (g_cancel.load(std::memory_order_acquire)) break;
        generated.push_back(static_cast<char>(best_token));
        gru_step(static_cast<uint8_t>(best_token), hidden, input_gate, recurrent_gate);
        if (generated.find("<|end|>") != std::string::npos) break;
    }
    return trim_generated(generated);
}
}  // namespace

extern "C" JNIEXPORT jstring JNICALL
Java_com_mikoo_ai_MainActivity_nativeStatus(JNIEnv* env, jobject /* thiz */) {
    if (g_model.loaded) {
        return utf8_to_jstring(env, "Mikoo Nano local checkpoint loaded; offline inference active.");
    }
    return utf8_to_jstring(env, "Mikoo Nano checkpoint unavailable; local baseline ready.");
}

extern "C" JNIEXPORT jboolean JNICALL
Java_com_mikoo_ai_MainActivity_nativeLoadModel(JNIEnv* env, jobject /* thiz */, jstring model_path) {
    const std::string path = jstring_to_utf8(env, model_path);
    if (path.empty() || path.size() > 4096) return JNI_FALSE;
    return load_bootstrap_model(path) ? JNI_TRUE : JNI_FALSE;
}

extern "C" JNIEXPORT void JNICALL
Java_com_mikoo_ai_MainActivity_nativeCancel(JNIEnv* /* env */, jobject /* thiz */) {
    g_cancel.store(true, std::memory_order_release);
}

extern "C" JNIEXPORT jstring JNICALL
Java_com_mikoo_ai_MainActivity_nativeGenerate(JNIEnv* env, jobject /* thiz */, jstring prompt,
                                              jint max_tokens, jint context_tokens) {
    const std::string input = jstring_to_utf8(env, prompt);
    const int bounded_tokens = max_tokens < 1 ? 1 : (max_tokens > kMaxGenerationTokens ? kMaxGenerationTokens : max_tokens);
    const int bounded_context = context_tokens < 256 ? 256 : (context_tokens > 2048 ? 2048 : context_tokens);
    if (input.size() > static_cast<size_t>(bounded_context) * 16) {
        return utf8_to_jstring(env, "Input exceeds the native safety bound.");
    }
    g_cancel.store(false, std::memory_order_release);
    if (!g_model.loaded) {
        return utf8_to_jstring(env, "Local checkpoint is unavailable; no code was generated.");
    }

    std::string response = generate_with_bootstrap(input, bounded_tokens);
    if (response.empty()) response = "The local checkpoint stopped without a readable response.";
    g_generated_tokens += static_cast<uint64_t>(response.size());
    return utf8_to_jstring(env, response);
}

extern "C" JNIEXPORT jlong JNICALL
Java_com_mikoo_ai_MainActivity_nativeGeneratedTokenCount(JNIEnv* /* env */, jobject /* thiz */) {
    return static_cast<jlong>(g_generated_tokens);
}
