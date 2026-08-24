package com.mikoo.ai

import android.app.Activity
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.os.SystemClock
import android.view.KeyEvent
import android.view.View
import android.view.inputmethod.EditorInfo
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView

class MainActivity : Activity() {
    private lateinit var input: EditText
    private lateinit var transcript: TextView
    private lateinit var status: TextView
    private lateinit var workspaceStatus: TextView
    private lateinit var tasksPanel: LinearLayout
    private lateinit var agentPanel: LinearLayout
    private lateinit var transcriptScroll: android.widget.ScrollView
    private var workspaceUri: Uri? = null
    private var hasTranscript = false

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
        workspaceStatus = findViewById(R.id.workspace_status)
        tasksPanel = findViewById(R.id.tasks_panel)
        agentPanel = findViewById(R.id.agent_panel)
        transcriptScroll = findViewById(R.id.transcript_scroll)

        transcript.text = "Offline chat ready\n\nType a coding request below. Mikoo will show your prompt and the local runtime result here."

        val send = findViewById<Button>(R.id.send_button)
        val openWorkspace = findViewById<Button>(R.id.open_workspace_button)
        val stop = findViewById<Button>(R.id.stop_button)
        val clear = findViewById<Button>(R.id.clear_button)
        val tasksTab = findViewById<Button>(R.id.tasks_tab)
        val agentTab = findViewById<Button>(R.id.agent_tab)
        val bannerClose = findViewById<TextView>(R.id.banner_close)
        val back = findViewById<TextView>(R.id.back_button)

        status.text = "Offline • ${nativeStatus()} • ${MemoryPolicy.deviceMemoryClassMb(this)} MB device class"
        send.setOnClickListener { sendMessage() }
        input.setOnEditorActionListener { _, actionId, event ->
            val enterPressed = event?.keyCode == KeyEvent.KEYCODE_ENTER && event.action == KeyEvent.ACTION_DOWN
            if (actionId == EditorInfo.IME_ACTION_SEND || enterPressed) {
                sendMessage()
                true
            } else {
                false
            }
        }
        openWorkspace.setOnClickListener {
            startActivityForResult(Intent(Intent.ACTION_OPEN_DOCUMENT_TREE), REQUEST_WORKSPACE)
        }
        stop.setOnClickListener {
            nativeCancel()
            val current = transcript.text.toString()
            transcript.text = current.replace("\nMikoo\n…working locally…\n", "\nMikoo\nGeneration cancelled safely.\n")
            findViewById<Button>(R.id.send_button).isEnabled = true
            status.text = "Generation cancelled • offline"
        }
        clear.setOnClickListener {
            hasTranscript = false
            transcript.text = "Offline chat ready\n\nType a coding request below. Mikoo will show your prompt and the local runtime result here."
            findViewById<TextView>(R.id.suggestions_title).visibility = View.VISIBLE
            findViewById<TextView>(R.id.suggestion_one).visibility = View.VISIBLE
            findViewById<TextView>(R.id.suggestion_two).visibility = View.VISIBLE
            findViewById<TextView>(R.id.suggestion_three).visibility = View.VISIBLE
            status.text = "Offline • ${nativeStatus()}"
        }
        tasksTab.setOnClickListener { showTasks() }
        agentTab.setOnClickListener { showAgent() }
        bannerClose.setOnClickListener { findViewById<View>(R.id.offline_banner).visibility = View.GONE }
        back.setOnClickListener { finish() }

        bindSuggestion(R.id.suggestion_one, "Fix a bug in my selected file")
        bindSuggestion(R.id.suggestion_two, "Review this function and suggest a safer patch")
        bindSuggestion(R.id.suggestion_three, "Write tests for the current workspace")
    }

    private fun bindSuggestion(id: Int, prompt: String) {
        findViewById<TextView>(id).setOnClickListener {
            input.setText(prompt)
            input.setSelection(input.length())
            input.requestFocus()
        }
    }

    private fun showTasks() {
        tasksPanel.visibility = View.VISIBLE
        agentPanel.visibility = View.GONE
        findViewById<Button>(R.id.tasks_tab).setBackgroundResource(R.drawable.bg_tab_active)
        findViewById<Button>(R.id.agent_tab).setBackgroundResource(R.drawable.bg_tab_inactive)
    }

    private fun showAgent() {
        tasksPanel.visibility = View.GONE
        agentPanel.visibility = View.VISIBLE
        findViewById<Button>(R.id.tasks_tab).setBackgroundResource(R.drawable.bg_tab_inactive)
        findViewById<Button>(R.id.agent_tab).setBackgroundResource(R.drawable.bg_tab_active)
    }

    private fun sendMessage() {
        val message = input.text.toString().trim()
        if (message.isEmpty()) return
        if (message.length > 12_000) {
            status.text = "Message is too long; please shorten it."
            return
        }

        if (!hasTranscript) {
            transcript.text = ""
            hasTranscript = true
            findViewById<TextView>(R.id.suggestions_title).visibility = View.GONE
            findViewById<TextView>(R.id.suggestion_one).visibility = View.GONE
            findViewById<TextView>(R.id.suggestion_two).visibility = View.GONE
            findViewById<TextView>(R.id.suggestion_three).visibility = View.GONE
        }

        val prompt = transcript.text.toString().takeLast(24_000) + "\nUser: " + message
        transcript.append("\nYou\n$message\n\nMikoo\n…working locally…\n")
        transcriptScroll.post { transcriptScroll.fullScroll(View.FOCUS_DOWN) }
        input.setText("")
        findViewById<Button>(R.id.send_button).isEnabled = false
        if (MemoryPolicy.shouldStopGeneration()) {
            val current = transcript.text.toString()
            transcript.text = current.replace("\nMikoo\n…working locally…\n", "\nMikoo\nGeneration stopped safely because the memory guard is active.\n")
            findViewById<Button>(R.id.send_button).isEnabled = true
            status.text = "Memory limit reached; generation stopped safely."
            return
        }
        val contextTokens = MemoryPolicy.safeContextTokens()
        status.text = "Mikoo is thinking locally • context=$contextTokens"
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
                val workingMarker = "\nMikoo\n…working locally…\n"
                transcript.text = current.removeSuffix(workingMarker)
                transcript.append("\nMikoo\n$response\n")
                transcriptScroll.post { transcriptScroll.fullScroll(View.FOCUS_DOWN) }
                findViewById<Button>(R.id.send_button).isEnabled = true
                status.text = "Offline • ${nativeStatus()} • ${elapsed} ms • context=$contextTokens • pss=${MemoryPolicy.processPssMb()} MB • tokens=${nativeGeneratedTokenCount()}"
            }
        }.start()
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == REQUEST_WORKSPACE && resultCode == RESULT_OK) {
            val uri = data?.data ?: return
            val flags = data.flags and (Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_GRANT_WRITE_URI_PERMISSION)
            contentResolver.takePersistableUriPermission(uri, flags)
            workspaceUri = uri
            workspaceStatus.text = "Workspace selected • ${uri.lastPathSegment ?: "local folder"}"
        }
    }

    companion object {
        private const val REQUEST_WORKSPACE = 7001

        init {
            System.loadLibrary("mikoo_jni")
        }
    }
}
