package com.mikoo.ai

import android.app.Activity
import android.content.Intent
import android.graphics.Color
import android.net.Uri
import android.os.Bundle
import android.os.SystemClock
import android.view.KeyEvent
import android.view.View
import android.view.inputmethod.EditorInfo
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ProgressBar
import android.widget.ScrollView
import android.widget.TextView
import java.io.File

class MainActivity : Activity() {
    private lateinit var input: EditText
    private lateinit var transcript: TextView
    private lateinit var status: TextView
    private lateinit var agentState: TextView
    private lateinit var workspaceStatus: TextView
    private lateinit var tasksPanel: LinearLayout
    private lateinit var agentPanel: LinearLayout
    private lateinit var historyPanel: LinearLayout
    private lateinit var historyItems: LinearLayout
    private lateinit var menuPanel: LinearLayout
    private lateinit var composer: LinearLayout
    private lateinit var clearButton: Button
    private lateinit var sendButton: Button
    private lateinit var thinkingProgress: ProgressBar
    private lateinit var transcriptScroll: ScrollView
    private var workspaceUri: Uri? = null
    private var hasTranscript = false
    private var menuOpen = false

    private external fun nativeStatus(): String
    private external fun nativeLoadModel(modelPath: String): Boolean
    private external fun nativeCancel()
    private external fun nativeGenerate(prompt: String, maxTokens: Int, contextTokens: Int): String
    private external fun nativeGeneratedTokenCount(): Long

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        input = findViewById(R.id.message_input)
        transcript = findViewById(R.id.transcript)
        status = findViewById(R.id.status)
        agentState = findViewById(R.id.agent_state)
        workspaceStatus = findViewById(R.id.workspace_status)
        tasksPanel = findViewById(R.id.tasks_panel)
        agentPanel = findViewById(R.id.agent_panel)
        historyPanel = findViewById(R.id.history_panel)
        historyItems = findViewById(R.id.history_items)
        menuPanel = findViewById(R.id.menu_panel)
        composer = findViewById(R.id.composer)
        clearButton = findViewById(R.id.clear_button)
        sendButton = findViewById(R.id.send_button)
        thinkingProgress = findViewById(R.id.thinking_progress)
        transcriptScroll = findViewById(R.id.transcript_scroll)

        val localModelLoaded = loadBundledCheckpoint()
        status.text = "Offline • ${nativeStatus()} • ${MemoryPolicy.deviceMemoryClassMb(this)} MB device class"
        agentState.text = if (localModelLoaded) "LOCAL MODEL" else "BASELINE"
        restoreCurrentSession()
        renderHistory()

        findViewById<TextView>(R.id.menu_button).setOnClickListener { toggleMenu() }
        findViewById<Button>(R.id.menu_chat).setOnClickListener { showChat() }
        findViewById<Button>(R.id.menu_tasks).setOnClickListener { showTasks() }
        findViewById<Button>(R.id.menu_history).setOnClickListener { showHistory() }
        findViewById<Button>(R.id.new_chat_button).setOnClickListener { clearSession() }
        findViewById<Button>(R.id.open_workspace_button).setOnClickListener { openWorkspacePicker() }
        findViewById<Button>(R.id.stop_button).setOnClickListener { cancelGeneration() }
        clearButton.setOnClickListener { clearSession() }
        sendButton.setOnClickListener { sendMessage() }
        input.setOnEditorActionListener { _, actionId, event ->
            val enterPressed = event?.keyCode == KeyEvent.KEYCODE_ENTER && event.action == KeyEvent.ACTION_DOWN
            if (actionId == EditorInfo.IME_ACTION_SEND || enterPressed) {
                sendMessage()
                true
            } else {
                false
            }
        }

        bindSuggestion(R.id.suggestion_one, "Fix a bug in my selected file")
        bindSuggestion(R.id.suggestion_two, "Review this function and suggest a safer patch")
        bindSuggestion(R.id.suggestion_three, "Write tests for the current workspace")
        showChat()
    }

    private fun bindSuggestion(id: Int, prompt: String) {
        findViewById<TextView>(id).setOnClickListener {
            input.setText(prompt)
            input.setSelection(input.length())
            input.requestFocus()
        }
    }

    private fun loadBundledCheckpoint(): Boolean {
        return try {
            val target = File(filesDir, "mikoo_bootstrap.bin")
            if (!target.exists() || target.length() == 0L) {
                assets.open("mikoo_bootstrap.bin").use { source ->
                    target.outputStream().use { destination -> source.copyTo(destination) }
                }
            }
            nativeLoadModel(target.absolutePath)
        } catch (_: Throwable) {
            false
        }
    }

    private fun toggleMenu() {
        menuOpen = !menuOpen
        menuPanel.visibility = if (menuOpen) View.VISIBLE else View.GONE
    }

    private fun closeMenu() {
        menuOpen = false
        menuPanel.visibility = View.GONE
    }

    private fun showChat() {
        closeMenu()
        tasksPanel.visibility = View.GONE
        historyPanel.visibility = View.GONE
        agentPanel.visibility = View.VISIBLE
        composer.visibility = View.VISIBLE
        clearButton.visibility = View.VISIBLE
        status.visibility = View.VISIBLE
        if (hasTranscript) hideSuggestions() else showSuggestions()
    }

    private fun showTasks() {
        closeMenu()
        agentPanel.visibility = View.GONE
        historyPanel.visibility = View.GONE
        tasksPanel.visibility = View.VISIBLE
        composer.visibility = View.GONE
        clearButton.visibility = View.GONE
        status.visibility = View.VISIBLE
        agentState.text = "TASKS"
        status.text = "Offline task board • local workspace actions require approval"
    }

    private fun showHistory() {
        closeMenu()
        agentPanel.visibility = View.GONE
        tasksPanel.visibility = View.GONE
        historyPanel.visibility = View.VISIBLE
        composer.visibility = View.GONE
        clearButton.visibility = View.GONE
        status.visibility = View.VISIBLE
            agentState.text = "HISTORY"
        status.text = "Local chat history • stored only on this device"
        renderHistory()
    }

    private fun showSuggestions() {
        findViewById<TextView>(R.id.suggestions_title).visibility = View.VISIBLE
        findViewById<TextView>(R.id.suggestion_one).visibility = View.VISIBLE
        findViewById<TextView>(R.id.suggestion_two).visibility = View.VISIBLE
        findViewById<TextView>(R.id.suggestion_three).visibility = View.VISIBLE
    }

    private fun hideSuggestions() {
        findViewById<TextView>(R.id.suggestions_title).visibility = View.GONE
        findViewById<TextView>(R.id.suggestion_one).visibility = View.GONE
        findViewById<TextView>(R.id.suggestion_two).visibility = View.GONE
        findViewById<TextView>(R.id.suggestion_three).visibility = View.GONE
    }

    private fun openWorkspacePicker() {
        closeMenu()
        startActivityForResult(Intent(Intent.ACTION_OPEN_DOCUMENT_TREE), REQUEST_WORKSPACE)
    }

    private fun cancelGeneration() {
        nativeCancel()
        val current = transcript.text.toString()
        transcript.text = current.replace("\nMikoo\n…working locally…\n", "\nMikoo\nGeneration cancelled safely.\n")
        thinkingProgress.visibility = View.GONE
        sendButton.isEnabled = true
        agentState.text = "CANCELLED"
        status.text = "Generation cancelled • offline"
        saveCurrentSession()
    }

    private fun clearSession() {
        nativeCancel()
        hasTranscript = false
        transcript.text = "Offline chat ready\n\nType a coding request below. Mikoo will show the prompt and the local agent state here."
        input.setText("")
        thinkingProgress.visibility = View.GONE
        sendButton.isEnabled = true
        agentState.text = "READY"
        status.text = "Offline • ${nativeStatus()}"
        showChat()
        showSuggestions()
        getSharedPreferences(PREFS_NAME, MODE_PRIVATE).edit().remove(KEY_TRANSCRIPT).apply()
    }

    private fun sendMessage() {
        val message = input.text.toString().trim()
        if (message.isEmpty() || !sendButton.isEnabled) return
        if (message.length > 12_000) {
            status.text = "Message is too long; please shorten it."
            agentState.text = "INPUT ERROR"
            return
        }

        showChat()
        if (!hasTranscript) {
            transcript.text = ""
            hasTranscript = true
            hideSuggestions()
        }

        val prompt = transcript.text.toString().takeLast(24_000) + "\nUser: " + message
        transcript.append("\nYou\n$message\n\nMikoo\n…working locally…\n")
        transcriptScroll.post { transcriptScroll.fullScroll(View.FOCUS_DOWN) }
        input.setText("")
        sendButton.isEnabled = false
        thinkingProgress.visibility = View.VISIBLE
        agentState.text = "THINKING"
        status.text = "Mikoo is thinking locally…"
        saveHistoryPrompt(message)

        if (MemoryPolicy.shouldStopGeneration()) {
            val current = transcript.text.toString()
            transcript.text = current.replace("\nMikoo\n…working locally…\n", "\nMikoo\nGeneration stopped safely because the memory guard is active.\n")
            thinkingProgress.visibility = View.GONE
            sendButton.isEnabled = true
            agentState.text = "STOPPED"
            status.text = "Memory limit reached; generation stopped safely."
            saveCurrentSession()
            return
        }

        val contextTokens = MemoryPolicy.safeContextTokens()
        val started = SystemClock.elapsedRealtime()
        Thread {
            val response = try {
                nativeGenerate(prompt, MemoryPolicy.DEFAULT_GENERATION_TOKENS, contextTokens)
            } catch (error: Throwable) {
                "Local runtime error: ${error.message ?: "native generation failed safely"}"
            }
            val elapsed = (SystemClock.elapsedRealtime() - started).coerceAtLeast(1)
            runOnUiThread {
                val current = transcript.text.toString()
                transcript.text = current.removeSuffix("\nMikoo\n…working locally…\n")
                transcript.append("\nMikoo\n$response\n")
                transcriptScroll.post { transcriptScroll.fullScroll(View.FOCUS_DOWN) }
                thinkingProgress.visibility = View.GONE
                sendButton.isEnabled = true
                agentState.text = "REPLIED"
                status.text = "Offline • ${elapsed} ms • context=$contextTokens • pss=${MemoryPolicy.processPssMb()} MB • tokens=${nativeGeneratedTokenCount()}"
                saveCurrentSession()
            }
        }.start()
    }

    private fun restoreCurrentSession() {
        val stored = getSharedPreferences(PREFS_NAME, MODE_PRIVATE).getString(KEY_TRANSCRIPT, "").orEmpty()
        if (stored.isNotBlank()) {
            transcript.text = stored
            hasTranscript = true
            agentState.text = "RESTORED"
        } else {
            transcript.text = "Offline chat ready\n\nType a coding request below. Mikoo will show the prompt and the local agent state here."
            hasTranscript = false
            agentState.text = "READY"
        }
    }

    private fun saveCurrentSession() {
        if (!hasTranscript) return
        getSharedPreferences(PREFS_NAME, MODE_PRIVATE).edit()
            .putString(KEY_TRANSCRIPT, transcript.text.toString().takeLast(40_000))
            .apply()
    }

    private fun saveHistoryPrompt(prompt: String) {
        val prefs = getSharedPreferences(PREFS_NAME, MODE_PRIVATE)
        val old = prefs.getString(KEY_HISTORY, "").orEmpty().split("\n").filter { it.isNotBlank() }
        val safePrompt = prompt.replace("\n", " ").replace("|", "¦")
        val entries = (listOf("${System.currentTimeMillis()}|$safePrompt") + old).take(20)
        prefs.edit().putString(KEY_HISTORY, entries.joinToString("\n")).apply()
        renderHistory()
    }

    private fun renderHistory() {
        if (!::historyItems.isInitialized) return
        historyItems.removeAllViews()
        val entries = getSharedPreferences(PREFS_NAME, MODE_PRIVATE)
            .getString(KEY_HISTORY, "").orEmpty().split("\n").filter { it.isNotBlank() }
        if (entries.isEmpty()) {
            val empty = TextView(this).apply {
                text = "No local chat history yet. Send a prompt from Chat to create one."
                setTextColor(Color.LTGRAY)
                textSize = 15f
                setPadding(dp(16), dp(16), dp(16), dp(16))
            }
            historyItems.addView(empty)
            return
        }
        entries.forEach { entry ->
            val prompt = entry.substringAfter("|", entry)
            val row = TextView(this).apply {
                text = prompt
                setTextColor(Color.WHITE)
                textSize = 15f
                setPadding(dp(16), dp(14), dp(16), dp(14))
                setBackgroundResource(R.drawable.bg_surface)
                setOnClickListener {
                    input.setText(prompt)
                    input.setSelection(input.length())
                    showChat()
                    input.requestFocus()
                }
            }
            historyItems.addView(row, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(8) })
        }
    }

    private fun dp(value: Int): Int = (value * resources.displayMetrics.density).toInt()

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == REQUEST_WORKSPACE && resultCode == RESULT_OK) {
            val uri = data?.data ?: return
            val flags = data.flags and (Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_GRANT_WRITE_URI_PERMISSION)
            if (flags != 0) contentResolver.takePersistableUriPermission(uri, flags)
            workspaceUri = uri
            workspaceStatus.text = "Workspace selected • ${uri.lastPathSegment ?: "local folder"}"
            showChat()
            agentState.text = "READY"
            status.text = "Workspace selected • offline coding actions require approval"
        }
    }

    companion object {
        private const val REQUEST_WORKSPACE = 7001
        private const val PREFS_NAME = "mikoo_local_session"
        private const val KEY_TRANSCRIPT = "current_transcript"
        private const val KEY_HISTORY = "chat_history"

        init {
            System.loadLibrary("mikoo_jni")
        }
    }
}
