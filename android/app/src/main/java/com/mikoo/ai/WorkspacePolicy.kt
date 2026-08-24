package com.mikoo.ai

/**
 * Limits for the offline coding workspace. The host must still enforce URI
 * permissions and user approval; these values prevent accidental unbounded
 * context or patch transfer.
 */
object WorkspacePolicy {
    const val MAX_FILES_PER_REQUEST = 32
    const val MAX_FILE_BYTES = 200_000
    const val MAX_TOTAL_CONTEXT_BYTES = 1_000_000
    const val MAX_PATCH_BYTES = 200_000
    const val MAX_SEARCH_MATCHES = 100
    const val MAX_LOG_BYTES = 12_000
    const val MAX_TEST_TIMEOUT_SECONDS = 120

    enum class Action(val requiresApproval: Boolean) {
        LIST_FILES(false),
        READ_FILE(false),
        SEARCH_FILES(false),
        PROPOSE_PATCH(false),
        APPLY_PATCH(true),
        RUN_TESTS(true),
        FORMAT_CODE(true),
        FINAL_ANSWER(false)
    }

    fun validFileRequest(fileCount: Int, totalBytes: Long): Boolean =
        fileCount in 1..MAX_FILES_PER_REQUEST && totalBytes in 1..MAX_TOTAL_CONTEXT_BYTES

    fun validPatch(bytes: Int, approved: Boolean): Boolean =
        bytes in 1..MAX_PATCH_BYTES && approved

    fun validTestProfile(timeoutSeconds: Int, approved: Boolean): Boolean =
        timeoutSeconds in 1..MAX_TEST_TIMEOUT_SECONDS && approved
}
