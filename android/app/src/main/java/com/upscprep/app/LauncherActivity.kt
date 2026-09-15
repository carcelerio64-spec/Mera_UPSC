package com.upscprep.app

import android.content.Context
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

class LauncherActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { MaterialTheme { UpscAppRoot(this) } }
    }
}

@Composable
fun UpscAppRoot(context: Context) {
    val prefs = remember { context.getSharedPreferences("upsc_session", Context.MODE_PRIVATE) }
    val savedToken = remember { prefs.getString("token", "") ?: "" }
    var token by remember { mutableStateOf(if (savedToken == DemoMode.TOKEN && !DemoMode.ENABLED) "" else savedToken) }
    var page by remember { mutableStateOf("home") }
    var notesExam by remember { mutableStateOf("mains") }
    var currentExam by remember { mutableStateOf("prelims") }
    var wrongExam by remember { mutableStateOf("prelims") }
    var practiceExam by remember { mutableStateOf("prelims") }
    var studyTarget by remember { mutableStateOf<StudyTarget?>(null) }
    var selectedSection by remember { mutableStateOf<QuestionSectionDto?>(null) }
    var answerQuestion by remember { mutableStateOf<TopicQuestionDto?>(null) }

    if (token.isBlank()) {
        AuthScreen { newToken -> prefs.edit().putString("token", newToken).apply(); token = newToken }
        return
    }
    val demo = DemoMode.ENABLED && token == DemoMode.TOKEN
    fun logout() { prefs.edit().remove("token").apply(); token = "" }

    Scaffold(bottomBar = {
        NavigationBar {
            listOf("Home", "Prelims", "Mains", "Optional").forEach { label ->
                NavigationBarItem(selected = page.equals(label, true), onClick = { page = label.lowercase() }, icon = {}, label = { Text(label) })
            }
        }
    }) { padding ->
        Box(Modifier.padding(padding).fillMaxSize()) {
            when (page) {
                "home" -> if (demo) DemoHomeScreen({ page = it }, { logout() }) else HomeScreen(token, { page = "prelims" }, { page = "mains" }, { page = "optional" }, { logout() })
                "prelims" -> SimpleSection("PRELIMS", listOf("📚 पढ़ाई करें", "🤖 AI Teacher", "🧠 Practice", "⏱ Mock Test", "📜 PYQ", "📰 Current Affairs", "🗂 Class Notes", "❌ Wrong Questions", "🔄 Revision"), { item ->
                    when {
                        item.startsWith("📚") -> page = "prelims_syllabus"
                        item.startsWith("🤖") -> page = if (demo) "demo_ai" else "ai_teacher"
                        item.startsWith("🧠") -> { practiceExam = "prelims"; page = if (demo) "demo_completed" else "completed_practice" }
                        item.startsWith("⏱") -> page = "demo_mock"
                        item.startsWith("📜") -> page = if (demo) "demo_pyq" else "prelims_pyq"
                        item.startsWith("📰") -> if (demo) page = "demo_current" else { currentExam = "prelims"; page = "current_affairs" }
                        item.startsWith("🗂") -> if (demo) page = "demo_notes" else { notesExam = "prelims"; page = "class_notes" }
                        item.startsWith("❌") -> if (demo) page = "demo_wrong" else { wrongExam = "prelims"; page = "wrong_questions" }
                        else -> page = "demo_revision"
                    }
                }, { page = "home" })
                "mains" -> SimpleSection("MAINS", listOf("📚 GS / Essay पढ़ें", "🤖 AI Teacher", "✍ Answer Writing", "📄 Test / PDF Paper", "📜 PYQ", "📰 Mains Current Affairs", "🗂 Class Notes", "❌ Wrong Questions", "🔄 Revision"), { item ->
                    when {
                        item.startsWith("📚") -> page = "mains_syllabus"
                        item.startsWith("🤖") -> page = if (demo) "demo_ai" else "ai_teacher"
                        item.startsWith("✍") -> { practiceExam = "mains"; page = if (demo) "demo_completed" else "completed_practice" }
                        item.startsWith("📄") -> page = "demo_mains_test"
                        item.startsWith("📜") -> page = if (demo) "demo_pyq" else "mains_pyq"
                        item.startsWith("📰") -> if (demo) page = "demo_current" else { currentExam = "mains"; page = "current_affairs" }
                        item.startsWith("🗂") -> if (demo) page = "demo_notes" else { notesExam = "mains"; page = "class_notes" }
                        item.startsWith("❌") -> if (demo) page = "demo_wrong" else { wrongExam = "mains"; page = "wrong_questions" }
                        else -> page = "demo_revision"
                    }
                }, { page = "home" })
                "optional" -> if (demo) DemoFeatureScreen("OPTIONAL", listOf("Optional Subject Selection", "Paper I", "Paper II", "Syllabus", "PYQ", "Answer Writing", "Class Notes")) { page = "home" } else OptionalScreen(token, { notesExam = "optional"; page = "class_notes" }) { page = "home" }
                "prelims_syllabus" -> if (demo) DemoSyllabusScreen("prelims", "PRELIMS SYLLABUS", { studyTarget = it; page = "topic_study" }) { page = "prelims" } else SyllabusScreen(token, "prelims", "PRELIMS SYLLABUS", { row, topic -> studyTarget = StudyTarget("prelims", row.paper, row.subject, topic); page = "topic_study" }) { page = "prelims" }
                "mains_syllabus" -> if (demo) DemoSyllabusScreen("mains", "MAINS SYLLABUS", { studyTarget = it; page = "topic_study" }) { page = "mains" } else SyllabusScreen(token, "mains", "MAINS SYLLABUS", { row, topic -> studyTarget = StudyTarget("mains", row.paper, row.subject, topic); page = "topic_study" }) { page = "mains" }
                "topic_study" -> studyTarget?.let { t -> if (demo) DemoTopicStudyScreen(t, { page = "demo_questions" }) { page = if (t.exam == "prelims") "prelims_syllabus" else "mains_syllabus" } else TopicStudyV2Screen(token, t) { page = if (t.exam == "prelims") "prelims_syllabus" else "mains_syllabus" } }
                "demo_questions" -> studyTarget?.let { t -> DemoQuestionScreen(t, { q -> answerQuestion = q; page = "demo_answer" }) { page = "topic_study" } }
                "demo_completed" -> {
                    val targets = DemoTestData.completed.mapNotNull { raw -> val p = raw.split('|'); if (p.size == 4 && p[0] == practiceExam) StudyTarget(p[0], p[1], p[2], p[3]) else null }
                    DemoCompletedScreen(practiceExam, targets, { studyTarget = it; page = "demo_questions" }) { page = practiceExam }
                }
                "prelims_pyq" -> PyqScreen(token, "prelims") { page = "prelims" }
                "mains_pyq" -> PyqScreen(token, "mains") { page = "mains" }
                "current_affairs" -> CurrentAffairsScreen(token, currentExam) { page = if (currentExam == "prelims") "prelims" else "mains" }
                "wrong_questions" -> WrongQuestionsScreen(token, wrongExam) { page = if (wrongExam == "prelims") "prelims" else "mains" }
                "class_notes" -> ClassNotesScreen(context, token, notesExam) { page = if (notesExam == "optional") "optional" else notesExam }
                "ai_teacher" -> AiTeacherScreen(token) { page = "home" }
                "completed_practice" -> CompletedPracticeScreen(token, practiceExam, { page = practiceExam }, { selectedSection = it; page = "topic_questions" })
                "topic_questions" -> selectedSection?.let { s -> TopicQuestionListScreen(token, s, { page = "completed_practice" }, { q -> answerQuestion = q; page = "mains_answer" }) }
                "mains_answer" -> answerQuestion?.let { q -> MainsAnswerWritingScreen(context, token, q) { page = "topic_questions" } }
                "demo_ai" -> DemoFeatureScreen("AI TEACHER", listOf("Prelims View", "Mains View", "Quick Revision", "Verified Official Knowledge")) { page = "home" }
                "demo_mock" -> DemoFeatureScreen("PRELIMS MOCK TEST", listOf("GS Paper-I", "CSAT", "Timer", "Negative Marking 1/3", "Completed Topics Combined Mock")) { page = "prelims" }
                "demo_answer" -> answerQuestion?.let { q -> MainsAnswerWritingScreen(context, DemoMode.TOKEN, q) { page = "demo_questions" } }
                "demo_mains_test" -> DemoFeatureScreen("MAINS TEST / PDF", listOf("Essay", "GS-I", "GS-II", "GS-III", "GS-IV", "QCA-style Paper", "Answer Space")) { page = "mains" }
                "demo_pyq" -> DemoFeatureScreen("PYQ", listOf("Official UPSC Papers", "Prelims", "Mains", "Optional Paper I & II")) { page = "home" }
                "demo_current" -> DemoFeatureScreen("CURRENT AFFAIRS", listOf("Daily Official-source Updates", "Date-wise Archive", "Prelims Relevance", "Mains Relevance")) { page = "home" }
                "demo_notes" -> DemoFeatureScreen("CLASS NOTES", listOf("Prelims / Mains / Optional", "Subject → Topic → Subtopic", "PDF", "Photo / Gallery", "Camera")) { page = "home" }
                "demo_wrong" -> DemoFeatureScreen("WRONG QUESTIONS", listOf("Prelims", "Mains", "Topic-wise Review", "Revision")) { page = "home" }
                "demo_revision" -> DemoFeatureScreen("REVISION", listOf("Due Revision", "Completed Topics", "Wrong Questions", "Quick Revision")) { page = "home" }
            }
        }
    }
}

@Composable
private fun DemoHomeScreen(onOpen: (String) -> Unit, onLogout: () -> Unit) {
    Column(Modifier.fillMaxSize().padding(20.dp)) {
        Text("UPSC", style = MaterialTheme.typography.headlineLarge)
        Text("TEST MODE • Original flow testing", modifier = Modifier.padding(bottom = 16.dp))
        listOf("PRELIMS" to "prelims", "MAINS" to "mains", "OPTIONAL" to "optional", "AI TEACHER" to "demo_ai", "CURRENT AFFAIRS" to "demo_current", "CLASS NOTES" to "demo_notes", "PYQ" to "demo_pyq", "REVISION" to "demo_revision").forEach { (a, b) ->
            ElevatedCard(onClick = { onOpen(b) }, modifier = Modifier.fillMaxWidth().padding(vertical = 5.dp)) { Text(a, Modifier.padding(18.dp)) }
        }
        TextButton(onClick = onLogout) { Text("Test Mode से बाहर जाएँ") }
    }
}

@Composable
private fun DemoFeatureScreen(title: String, items: List<String>, onBack: () -> Unit) {
    Column(Modifier.fillMaxSize().padding(20.dp)) {
        TextButton(onClick = onBack) { Text("← Back") }
        Text(title, style = MaterialTheme.typography.headlineSmall)
        Text("TEST MODE", style = MaterialTheme.typography.labelMedium)
        items.forEach { ElevatedCard(modifier = Modifier.fillMaxWidth().padding(vertical = 5.dp)) { Text(it, Modifier.padding(18.dp)) } }
    }
}

@Composable
private fun DemoCompletedScreen(exam: String, targets: List<StudyTarget>, open: (StudyTarget) -> Unit, back: () -> Unit) {
    Column(Modifier.fillMaxSize().padding(20.dp)) {
        TextButton(onClick = back) { Text("← ${exam.uppercase()} PRACTICE") }
        Text("Completed Topics", style = MaterialTheme.typography.headlineSmall)
        if (targets.isEmpty()) Text("पहले Syllabus में कोई topic Complete करें।", Modifier.padding(top = 16.dp))
        targets.forEach { t -> Card(onClick = { open(t) }, modifier = Modifier.fillMaxWidth().padding(vertical = 6.dp)) { Column(Modifier.padding(18.dp)) { Text(t.paper); Text(t.subject, style = MaterialTheme.typography.titleMedium); Text(t.topic) } } }
    }
}
