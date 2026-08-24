#include <jni.h>

#include <atomic>
#include <cctype>
#include <cstdint>
#include <initializer_list>
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

std::string lower_ascii(std::string value) {
    for (char& character : value) {
        character = static_cast<char>(std::tolower(static_cast<unsigned char>(character)));
    }
    return value;
}

bool contains_any(const std::string& text, const std::initializer_list<const char*>& terms) {
    for (const char* term : terms) {
        if (text.find(term) != std::string::npos) return true;
    }
    return false;
}

std::string offline_fallback(const std::string& input) {
    const std::string text = lower_ascii(input);
    const bool greeting = contains_any(text, {"hello", "hi", "hey", "হ্যালো"});
    const bool bug = contains_any(text, {"bug", "error", "fix", "বাগ", "সমস্যা"});
    const bool tests = contains_any(text, {"test", "tests", "unit test", "টেস্ট"});
    const bool review = contains_any(text, {"review", "refactor", "safer", "explain", "রিভিউ", "ব্যাখ্যা"});

    std::string response;
    if (greeting) {
        response =
            "Hello. I am Mikoo's offline coding assistant.\n\n"
            "The local chat path is working. This APK currently uses a deterministic local baseline while the trained Mikoo checkpoint is being prepared.\n\n"
            "You can select a workspace, keep a local chat history, and submit coding tasks without network access.";
    } else if (bug) {
        response =
            "I received a bug-fix request in offline mode.\n\n"
            "Local workflow:\n"
            "1. Open Tasks → New workspace and choose the project folder.\n"
            "2. Share the failing file or error details in this chat.\n"
            "3. Mikoo will propose a bounded patch for approval before any write or test action.\n\n"
            "The trained checkpoint is not bundled yet, so this baseline cannot inspect or generate a real patch.";
    } else if (tests) {
        response =
            "I received a test-generation request offline.\n\n"
            "Local workflow:\n"
            "1. Select the project workspace.\n"
            "2. Identify the function or file to cover.\n"
            "3. Review the proposed tests before execution.\n\n"
            "The trained checkpoint is still pending; no test file or command was fabricated or executed.";
    } else if (review) {
        response =
            "I received your review request offline.\n\n"
            "I can keep the conversation and workspace context locally, but a real code review requires the self-trained Mikoo checkpoint and native inference adapter. No external model or network service is used.";
    } else {
        response =
            "I received your request offline.\n\n"
            "The Mikoo local chat path is working, and this build can manage the conversation, local history, workspace selection, and safe task flow.\n\n"
            "For real code generation and reasoning, the self-trained Mikoo checkpoint and bounded C++ inference adapter still need to be connected. No external AI or network service will be used.";
    }

    response += "\n\nLocal baseline • prompt size: " + std::to_string(input.size()) + " bytes.";
    return response;
}
}  // namespace

extern "C" JNIEXPORT jstring JNICALL
Java_com_mikoo_ai_MainActivity_nativeStatus(JNIEnv* env, jobject /* thiz */) {
    if (!g_state.model_loaded) {
        return utf8_to_jstring(env, "Local baseline ready; trained Mikoo checkpoint pending.");
    }
    return utf8_to_jstring(env, "Model loaded in native memory.");
}

extern "C" JNIEXPORT jboolean JNICALL
Java_com_mikoo_ai_MainActivity_nativeLoadModel(JNIEnv* env, jobject /* thiz */, jstring model_path) {
    const std::string path = jstring_to_utf8(env, model_path);
    if (path.empty() || path.size() > 4096) {
        return JNI_FALSE;
    }
    // Replace this guarded transition with the validated self-trained loader
    // when the Mikoo checkpoint and tokenizer are available.
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
        return utf8_to_jstring(env, offline_fallback(input));
    }
    // TODO: Stream tokens from the selected validated runtime through a
    // bounded JNI callback. This path must retain the 749 MB application cap.
    (void)bounded_context;
    g_state.generated_tokens += static_cast<uint64_t>(bounded_tokens);
    return utf8_to_jstring(env, "Validated Mikoo runtime adapter is not connected.");
}

extern "C" JNIEXPORT jlong JNICALL
Java_com_mikoo_ai_MainActivity_nativeGeneratedTokenCount(JNIEnv* /* env */, jobject /* thiz */) {
    return static_cast<jlong>(g_state.generated_tokens);
}
