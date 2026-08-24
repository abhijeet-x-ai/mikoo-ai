# Android build

The project is a native Kotlin/C++ prototype. Install JDK 17+, Android SDK platform 35, Android Build Tools 35.x, Android NDK, CMake 3.22.1, and Gradle 8.x on the build machine.

From this directory, set `ANDROID_HOME` or `ANDROID_SDK_ROOT`, accept the required Android SDK licenses, and run:

```bash
gradle :app:assembleDebug
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

The first ABI is `arm64-v8a`. Add `armeabi-v7a` only after the C++ runtime and model are validated on an ARMv7 device.

The current native library is a guarded JNI adapter and deliberately reports that the trained model/runtime is pending. It does not fabricate generated answers. Before release, replace the guarded loader and generation branch in `mikoo_jni.cpp` with the validated GGUF-compatible or ExecuTorch runtime integration, then run the offline and memory benchmark suite.

## Sandbox validation status

The sandbox used to prepare this repository has no detected Android SDK, Gradle, ADB, PyTorch installation, CUDA GPU, or physical Android device. Python syntax, model-manifest, benchmark-template, and offline-permission checks pass. APK compilation, checkpoint training, and device performance measurements remain external execution steps.
