# Mikoo native JNI symbols are accessed by their generated names.
# Keep the activity entry point and native method declarations in release builds.
-keep class com.mikoo.ai.MainActivity { *; }
