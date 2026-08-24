#include <jni.h>

#include <atomic>
#include <chrono>
#include <cstdint>
#include <string>

namespace {
std::atomic<bool> g_cancel{false};

struct RuntimeState {
    bool model_loaded = false;
    std::string model_path;
    uint64_t generated_tokens = 0;
};

RuntimeState g_state;

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
}  // namespace

extern "C" JNIEXPORT jstring JNICALL
Java_com_mikoo_ai_MainActivity_nativeStatus(JNIEnv* env, jobject /* thiz */) {
    if (!g_state.model_loaded) {
        return utf8_to_jstring(env, "Model artifact pending: native runtime is ready, no trained checkpoint loaded.");
    }
    return utf8_to_jstring(env, "Model loaded in native memory.");
}

extern "C" JNIEXPORT jboolean JNICALL
Java_com_mikoo_ai_MainActivity_nativeLoadModel(JNIEnv* env, jobject /* thiz */, jstring model_path) {
    const std::string path = jstring_to_utf8(env, model_path);
    if (path.empty() || path.size() > 4096) {
        return JNI_FALSE;
    }
    // TODO: Replace this guarded state transition with the selected GGUF/ExecuTorch
    // loader after the trained and quantized artifact is validated.
    g_state.model_path = path;
    g_state.model_loaded = false;
    return JNI_FALSE;
}

extern "C" JNIEXPORT void JNICALL
Java_com_mikoo_ai_MainActivity_nativeCancel(JNIEnv* /* env */, jobject /* thiz */) {
    g_cancel.store(true, std::memory_order_release);
}

extern "C" JNIEXPORT jstring JNICALL
Java_com_mikoo_ai_MainActivity_nativeGenerate(JNIEnv* env, jobject /* thiz */, jstring prompt,
                                              jint max_tokens, jint context_tokens) {
    const std::string input = jstring_to_utf8(env, prompt);
    const int bounded_tokens = max_tokens < 1 ? 1 : (max_tokens > 256 ? 256 : max_tokens);
    const int bounded_context = context_tokens < 256 ? 256 : (context_tokens > 2048 ? 2048 : context_tokens);
    if (input.size() > static_cast<size_t>(bounded_context) * 16) {
        return utf8_to_jstring(env, "Input exceeds the native safety bound.");
    }
    g_cancel.store(false, std::memory_order_release);
    if (!g_state.model_loaded) {
        return utf8_to_jstring(env, "Mikoo model is not loaded yet. Train and quantize the checkpoint, then connect the validated runtime adapter.");
    }
    // TODO: Stream tokens from the selected runtime through a bounded JNI callback.
    // This placeholder deliberately does not fabricate model output.
    (void)bounded_context;
    g_state.generated_tokens += static_cast<uint64_t>(bounded_tokens);
    return utf8_to_jstring(env, "Runtime adapter not connected.");
}

extern "C" JNIEXPORT jlong JNICALL
Java_com_mikoo_ai_MainActivity_nativeGeneratedTokenCount(JNIEnv* /* env */, jobject /* thiz */) {
    return static_cast<jlong>(g_state.generated_tokens);
}
