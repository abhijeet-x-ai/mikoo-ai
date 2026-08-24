# Mikoo Android build

## Environment used for the debug APK

The local build toolchain is installed outside the repository at `/home/ubuntu/mikoo-toolchain`:

- OpenJDK 21 with `javac`
- Gradle 8.11.1
- Android SDK Platform 35
- Android Build Tools 35.0.0
- Android NDK 27.0.12077973
- CMake 3.22.1

The repository's `local.properties` points to the local SDK path. Do not commit personal SDK paths if the project is moved to another machine.

## Build command

```bash
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
export ANDROID_SDK_ROOT=/home/ubuntu/mikoo-toolchain/android-sdk
export ANDROID_HOME="$ANDROID_SDK_ROOT"
export PATH="$JAVA_HOME/bin:$ANDROID_SDK_ROOT/cmdline-tools/latest/bin:$ANDROID_SDK_ROOT/platform-tools:$ANDROID_SDK_ROOT/build-tools/35.0.0:/home/ubuntu/mikoo-toolchain/gradle/gradle-8.11.1/bin:$PATH"
cd android
gradle --no-daemon assembleDebug
```

Output: `app/build/outputs/apk/debug/app-debug.apk`

## Verified status

The debug APK builds successfully, is v2-signed by the debug keystore, contains the ARM64 native library `libmikoo_jni.so`, targets SDK 35, and has package ID `com.mikoo.ai`. The verified artifact is approximately 3.7 MB because no trained model checkpoint is bundled.

No physical Android device is connected in the build environment, so install, first-token latency, PSS/RSS, thermal, battery, cancellation, crash, and ANR measurements remain pending. The native bridge reports a pending runtime adapter until a real trained and validated local checkpoint is connected.
