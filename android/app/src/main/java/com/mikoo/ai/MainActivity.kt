package com.mikoo.ai

import android.app.Activity
import android.os.Bundle
import android.os.SystemClock
import android.content.Intent
import android.net.Uri
import android.widget.Button
import android.widget.EditText
import android.widget.TextView

class MainActivity : Activity() {
    private lateinit var input: EditText
    private lateinit var transcript: TextView
    private lateinit var status: TextView
    private lateinit var workspaceStatus: TextView
    private var workspaceUri: Uri? = null

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
        val send = findViewById<Button>(R.id.send_button)
        val openWorkspace = findViewById<Button>(R.id.open_workspace_button)
        val stop = findViewById<Button>(R.id.stop_button)
        val clear = findViewById<Button>(R.id.clear_button)

        status.text = "${nativeStatus()} | deviceMemoryClass=${MemoryPolicy.deviceMemoryClassMb(this)} MB"
        send.setOnClickListener { sendMessage() }
        openWorkspace.setOnClickListener {
            startActivityForResult(Intent(Intent.ACTION_OPEN_DOCUMENT_TREE), REQUEST_WORKSPACE)
        }
        stop.setOnClickListener {
            nativeCancel()
            status.text = "Generation cancelled."
        }
        clear.setOnClickListener {
            transcript.text = ""
            status.text = nativeStatus()
        }
    }

    private fun sendMessage() {
        val message = input.text.toString().trim()
        if (message.isEmpty()) return
        if (message.length > 12_000) {
            status.text = "Message is too long; please shorten it."
            return
        }

        val prompt = transcript.text.toString().takeLast(24_000) + "\nUser: " + message
        transcript.append("\nYou: $message\n")
        input.setText("")
        if (MemoryPolicy.shouldStopGeneration()) {
            status.text = "Memory limit reached; generation stopped safely."
            return
        }
        val contextTokens = MemoryPolicy.safeContextTokens()
        status.text = "Generating… context=$contextTokens"
        val started = SystemClock.elapsedRealtime()

        Thread {
            val response = nativeGenerate(prompt, 256, contextTokens)
            val elapsed = (SystemClock.elapsedRealtime() - started).coerceAtLeast(1)
            runOnUiThread {
                transcript.append("Mikoo: $response\n")
                status.text = "${nativeStatus()} | ${elapsed} ms | context=${contextTokens} | pss=${MemoryPolicy.processPssMb()} MB | tokens=${nativeGeneratedTokenCount()}"
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
            workspaceStatus.text = "Workspace selected: ${uri.lastPathSegment ?: "local folder"}"
        }
    }

    companion object {
        private const val REQUEST_WORKSPACE = 7001

        init {
            System.loadLibrary("mikoo_jni")
        }
    }
}
