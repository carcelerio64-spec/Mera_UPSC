package com.upscprep.app

import android.content.Context
import android.graphics.Bitmap
import android.net.Uri
import android.provider.OpenableColumns
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.launch
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.ByteArrayOutputStream

private data class AnswerUpload(val bytes: ByteArray, val name: String, val mime: String)

private fun readAnswerFile(context: Context, uri: Uri, mimeFallback: String): AnswerUpload? {
    val bytes = context.contentResolver.openInputStream(uri)?.use { it.readBytes() } ?: return null
    var name = "answer"
    context.contentResolver.query(uri, arrayOf(OpenableColumns.DISPLAY_NAME), null, null, null)?.use { c ->
        if (c.moveToFirst()) name = c.getString(0) ?: name
    }
    return AnswerUpload(bytes, name, context.contentResolver.getType(uri) ?: mimeFallback)
}

@Composable
fun MainsAnswerWritingScreen(context: Context, token: String, question: TopicQuestionDto, onBack: () -> Unit) {
    val demo = DemoMode.ENABLED && token == DemoMode.TOKEN
    val scope = rememberCoroutineScope()
    var answer by remember { mutableStateOf("") }
    var selectedFile by remember { mutableStateOf<AnswerUpload?>(null) }
    var submission by remember { mutableStateOf<AnswerSubmissionResponse?>(null) }
    var evaluation by remember { mutableStateOf<AnswerEvaluationDto?>(null) }
    var solution by remember { mutableStateOf<QuestionSolutionDto?>(null) }
    var busy by remember { mutableStateOf(false) }
    var message by remember { mutableStateOf("") }
    var demoHandwritten by remember { mutableStateOf(false) }
    var demoSubmitted by remember { mutableStateOf(false) }

    val photoPicker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { u ->
        selectedFile = u?.let { readAnswerFile(context, it, "image/jpeg") }
    }
    val pdfPicker = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { u ->
        selectedFile = u?.let { readAnswerFile(context, it, "application/pdf") }
    }
    val camera = rememberLauncherForActivityResult(ActivityResultContracts.TakePicturePreview()) { bmp: Bitmap? ->
        if (bmp != null) {
            val out = ByteArrayOutputStream()
            bmp.compress(Bitmap.CompressFormat.JPEG, 92, out)
            selectedFile = AnswerUpload(out.toByteArray(), "camera-answer.jpg", "image/jpeg")
        }
    }

    fun loadEvaluation() {
        if (demo) {
            message = if (demoHandwritten) "UPSC-pattern AI Evaluation • TEST MODE: handwritten submission accepted. यह official examiner marks नहीं है।" else "🔒 Evaluation के लिए handwritten PDF/photo/camera answer जरूरी है।"
            return
        }
        val id = submission?.submission_id ?: return
        scope.launch { try { evaluation = ApiClient.api.mainsEvaluation(ApiClient.bearer(token), id) } catch (_: Exception) { message = "Evaluation अभी उपलब्ध नहीं है" } }
    }
    fun loadSolution() {
        if (demo) {
            message = if (demoHandwritten) "Model framework unlocked • TEST MODE" else "🔒 Handwritten PDF/photo/camera answer upload करने के बाद model answer खुलेगा।"
            return
        }
        scope.launch {
            busy = true
            try { solution = ApiClient.api.questionSolution(ApiClient.bearer(token), question.id) } catch (_: Exception) { message = "Model answer अभी उपलब्ध नहीं है" } finally { busy = false }
        }
    }

    LaunchedEffect(question.id) { loadSolution() }

    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(20.dp)) {
        TextButton(onClick = onBack) { Text("← Answer Writing") }
        Text("Mains Answer Writing", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
        if (demo) Text("TEST MODE • Original answer workflow", style = MaterialTheme.typography.labelMedium)

        Card(Modifier.fillMaxWidth().padding(vertical = 10.dp)) {
            Column(Modifier.padding(16.dp)) {
                Text(question.question, fontWeight = FontWeight.SemiBold)
                val marks = if (question.marks > 0) question.marks else 10
                val words = if (question.word_limit > 0) question.word_limit else if (marks == 15) 250 else 150
                Text("$marks marks • $words words", modifier = Modifier.padding(top = 8.dp))
            }
        }
        OutlinedTextField(value = answer, onValueChange = { answer = it }, label = { Text("Typed answer") }, modifier = Modifier.fillMaxWidth().heightIn(min = 180.dp))
        Button(
            enabled = !busy && answer.isNotBlank(),
            onClick = {
                if (demo) {
                    demoSubmitted = true
                    message = "Typed answer saved • TEST MODE. Model answer/evaluation के लिए handwritten upload जरूरी है।"
                } else {
                    scope.launch {
                        busy = true
                        try {
                            submission = ApiClient.api.submitTypedAnswer(ApiClient.bearer(token), TypedAnswerRequest(question.id, answer))
                            evaluation = null
                            message = "Typed answer submit हो गया। Handwritten upload के बाद model answer/evaluation unlock होगा।"
                            loadSolution()
                        } catch (_: Exception) { message = "Answer submit नहीं हुआ" } finally { busy = false }
                    }
                }
            },
            modifier = Modifier.fillMaxWidth().padding(top = 10.dp)
        ) { Text("Typed Answer Submit") }
        if (demoSubmitted) Text("✓ Typed draft saved locally", style = MaterialTheme.typography.labelMedium, modifier = Modifier.padding(top = 6.dp))

        Text("या handwritten answer upload करें", fontWeight = FontWeight.Bold, modifier = Modifier.padding(top = 20.dp, bottom = 8.dp))
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            OutlinedButton(onClick = { pdfPicker.launch(arrayOf("application/pdf")) }, modifier = Modifier.weight(1f)) { Text("📄 PDF") }
            OutlinedButton(onClick = { photoPicker.launch("image/*") }, modifier = Modifier.weight(1f)) { Text("🖼 Photo") }
            OutlinedButton(onClick = { camera.launch(null) }, modifier = Modifier.weight(1f)) { Text("📷 Camera") }
        }

        selectedFile?.let { f ->
            Text("Selected: ${f.name}", modifier = Modifier.padding(top = 8.dp))
            Button(
                enabled = !busy,
                onClick = {
                    if (demo) {
                        demoHandwritten = true
                        message = "Handwritten answer accepted locally • TEST MODE. Evaluation और model framework unlock हो गए।"
                    } else {
                        scope.launch {
                            busy = true
                            try {
                                val qid = question.id.toString().toRequestBody("text/plain".toMediaTypeOrNull())
                                val body = f.bytes.toRequestBody(f.mime.toMediaTypeOrNull())
                                val part = MultipartBody.Part.createFormData("file", f.name, body)
                                submission = ApiClient.api.uploadMainsAnswer(ApiClient.bearer(token), qid, part)
                                evaluation = null
                                message = "Handwritten answer upload हो गया"
                                solution = ApiClient.api.questionSolution(ApiClient.bearer(token), question.id)
                            } catch (_: Exception) { message = "Answer upload नहीं हुआ" } finally { busy = false }
                        }
                    }
                },
                modifier = Modifier.fillMaxWidth().padding(top = 8.dp)
            ) { Text("Upload Answer") }
        }

        if (busy) LinearProgressIndicator(Modifier.fillMaxWidth().padding(vertical = 10.dp))
        if (message.isNotBlank()) Text(message, modifier = Modifier.padding(vertical = 8.dp))

        Card(Modifier.fillMaxWidth().padding(top = 12.dp)) {
            Column(Modifier.padding(16.dp)) {
                Text("Model Answer / Framework", fontWeight = FontWeight.Bold)
                if (demo) {
                    if (demoHandwritten) {
                        Text("TEST MODE framework: प्रश्न की demand पहचानें → परिचय → व्यवस्थित analytical points → evidence/examples → balanced conclusion.", modifier = Modifier.padding(top = 8.dp))
                    } else {
                        Text("🔒 Handwritten PDF/photo/camera answer upload करने के बाद ही model answer खुलेगा।", modifier = Modifier.padding(top = 8.dp))
                        TextButton(onClick = { loadSolution() }) { Text("Unlock status refresh करें") }
                    }
                } else {
                    val sol = solution
                    if (sol?.model_answer_unlocked == true) {
                        if (sol.model_outline.isNotBlank()) Text(sol.model_outline, modifier = Modifier.padding(top = 8.dp)) else Text("Model framework अभी तैयार नहीं है।", modifier = Modifier.padding(top = 8.dp))
                    } else {
                        Text(sol?.detail ?: "🔒 Handwritten PDF/photo/camera answer upload करने के बाद ही model answer खुलेगा।", modifier = Modifier.padding(top = 8.dp))
                        TextButton(onClick = { loadSolution() }) { Text("Unlock status refresh करें") }
                    }
                }
            }
        }

        if (demo) {
            Card(Modifier.fillMaxWidth().padding(top = 12.dp)) {
                Column(Modifier.padding(16.dp)) {
                    Text("UPSC-pattern AI Evaluation", fontWeight = FontWeight.Bold)
                    if (!demoHandwritten) Text("🔒 Evaluation locked — handwritten answer जरूरी है।", modifier = Modifier.padding(top = 8.dp))
                    else {
                        Text("TEST MODE evaluation flow unlocked", fontWeight = FontWeight.SemiBold, modifier = Modifier.padding(top = 8.dp))
                        Text("Demand • Relevance • Structure • Analysis • Evidence • Balance • Conclusion • Presentation • Word limit")
                        Text("Demo में fabricated marks नहीं दिए जाते।", style = MaterialTheme.typography.labelMedium, modifier = Modifier.padding(top = 8.dp))
                    }
                    TextButton(onClick = { loadEvaluation() }) { Text("Evaluation status देखें") }
                }
            }
        }

        submission?.let { s ->
            Card(Modifier.fillMaxWidth().padding(top = 12.dp)) {
                Column(Modifier.padding(16.dp)) {
                    Text("Submission #${s.submission_id}", fontWeight = FontWeight.Bold)
                    Text("Maximum: ${s.max_marks} marks • Word limit: ${s.word_limit}")
                    TextButton(onClick = { loadEvaluation() }) { Text("Evaluation status देखें") }
                }
            }
        }
        evaluation?.let { e ->
            Card(Modifier.fillMaxWidth().padding(top = 10.dp)) {
                Column(Modifier.padding(16.dp)) {
                    Text("UPSC-pattern AI Evaluation", fontWeight = FontWeight.Bold)
                    when (e.status) {
                        "locked" -> Text(e.detail ?: "🔒 Handwritten answer required", modifier = Modifier.padding(top = 8.dp))
                        "pending" -> Text("Evaluation pending", modifier = Modifier.padding(top = 8.dp))
                        "evaluated" -> {
                            Text("Marks: ${e.marks_awarded ?: 0.0}/${e.max_marks ?: 0}", style = MaterialTheme.typography.titleLarge, modifier = Modifier.padding(top = 8.dp))
                            if (!e.strengths.isNullOrBlank()) Text("Strengths: ${e.strengths}")
                            if (!e.improvements.isNullOrBlank()) Text("Improve: ${e.improvements}")
                            Text("यह UPSC-pattern AI Evaluation है, official UPSC examiner marks नहीं।", style = MaterialTheme.typography.labelMedium, modifier = Modifier.padding(top = 10.dp))
                        }
                        else -> Text(e.detail ?: "Evaluation status उपलब्ध नहीं है")
                    }
                }
            }
        }
    }
}
