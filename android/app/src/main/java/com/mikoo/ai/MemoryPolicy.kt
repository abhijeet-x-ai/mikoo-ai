package com.mikoo.ai

import android.app.ActivityManager
import android.content.Context
import android.os.Debug

/**
 * Runtime policy for a 2 GB Android device. Values are policy gates, not a
 * substitute for device PSS/RSS profiling.
 */
object MemoryPolicy {
    const val HARD_PEAK_MB = 749L
    const val PREFERRED_PEAK_MB = 650L
    const val DEFAULT_CONTEXT_TOKENS = 512
    const val RECOMMENDED_CONTEXT_TOKENS = 1024
    const val STRESS_CONTEXT_TOKENS = 2048
    const val DEFAULT_GENERATION_TOKENS = 768

    fun processPssMb(): Long = Debug.getPss() / 1024L

    fun shouldStopGeneration(): Boolean = processPssMb() >= HARD_PEAK_MB

    fun shouldReduceContext(): Boolean = processPssMb() >= PREFERRED_PEAK_MB

    fun safeContextTokens(): Int = when {
        shouldStopGeneration() -> 256
        shouldReduceContext() -> DEFAULT_CONTEXT_TOKENS
        else -> RECOMMENDED_CONTEXT_TOKENS
    }

    fun deviceMemoryClassMb(context: Context): Int {
        val manager = context.getSystemService(Context.ACTIVITY_SERVICE) as ActivityManager
        return manager.memoryClass
    }
}
