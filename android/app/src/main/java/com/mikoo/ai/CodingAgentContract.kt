package com.mikoo.ai

object CodingAgentContract {
    enum class TaskType {
        COMPLETION,
        EXPLANATION,
        UNIT_TESTS,
        DEBUGGING,
        BUG_FIXING,
        REFACTORING,
        CODE_TRANSLATION,
        REPOSITORY_CONTEXT,
        PATCH_PROPOSAL,
        FINAL_ANSWER
    }

    data class Result(
        val summary: String,
        val filesRead: List<String> = emptyList(),
        val filesChanged: List<String> = emptyList(),
        val testsRun: List<String> = emptyList(),
        val testsPassed: Boolean? = null,
        val risks: List<String> = emptyList(),
        val toolError: String? = null,
    )

    fun systemInstruction(): String = """
        You are Mikoo AI, an offline coding agent. Work only with user-provided or
        explicitly approved workspace context. Propose minimal changes. Never claim
        a file was read, a patch was applied, or a test passed without a successful
        host tool result. Require user approval before applying patches or running tests.
        Return concise code, a diff, tests, assumptions, and remaining risks.
    """.trimIndent()
}
