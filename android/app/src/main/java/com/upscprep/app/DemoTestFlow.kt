package com.upscprep.app

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp

/** Local test data only. Production data still comes from the backend. */
object DemoTestData {
    val prelims = listOf(
        SyllabusSectionDto("GS Paper-I", "History", listOf("Ancient India", "Medieval India", "Modern India", "Art & Culture")),
        SyllabusSectionDto("GS Paper-I", "Geography", listOf("Physical Geography", "Indian Geography", "World Geography")),
        SyllabusSectionDto("GS Paper-I", "Polity & Governance", listOf("Constitution", "Parliament", "Judiciary", "Local Government")),
        SyllabusSectionDto("GS Paper-I", "Economy", listOf("Growth & Development", "Inflation", "Banking", "Budget")),
        SyllabusSectionDto("GS Paper-I", "Environment", listOf("Ecology", "Biodiversity", "Climate Change")),
        SyllabusSectionDto("GS Paper-I", "Science & Technology", listOf("Space", "Biotechnology", "Digital Technology")),
        SyllabusSectionDto("CSAT", "Aptitude", listOf("Comprehension", "Reasoning", "Numeracy", "Data Interpretation"))
    )

    val mains = listOf(
        SyllabusSectionDto("Essay", "Essay", listOf("Essay Practice")),
        SyllabusSectionDto("GS-I", "History, Society & Geography", listOf("Indian Heritage & Culture", "Modern History", "World History", "Indian Society", "Geography")),
        SyllabusSectionDto("GS-II", "Polity, Governance & IR", listOf("Constitution", "Governance", "Social Justice", "International Relations")),
        SyllabusSectionDto("GS-III", "Economy, S&T, Environment & Security", listOf("Economy", "Agriculture", "Science & Technology", "Environment", "Disaster Management", "Internal Security")),
        SyllabusSectionDto("GS-IV", "Ethics", listOf("Ethics & Human Interface", "Attitude", "Aptitude", "Emotional Intelligence", "Probity", "Case Studies"))
    )

    val completed = mutableStateListOf<String>()

    fun key(target: StudyTarget) = "${target.exam}|${target.paper}|${target.subject}|${target.topic}"

    fun questions(target: StudyTarget): List<TopicQuestionDto> = if (target.exam == "prelims") {
        listOf(
            TopicQuestionDto(9001, question = "${target.topic} से संबंधित सही कथन चुनिए।", difficulty = "Moderate", question_type = "mcq", options = listOf("कथन 1", "कथन 2", "दोनों", "इनमें से कोई नहीं")),
            TopicQuestionDto(9002, question = "${target.topic} के संदर्भ में निम्न में से कौन-सा विकल्प सर्वाधिक उपयुक्त है?", difficulty = "Easy", question_type = "mcq", options = listOf("विकल्प A", "विकल्प B", "विकल्प C", "विकल्प D"))
        )
    } else {
        listOf(
            TopicQuestionDto(9101, question = "${target.topic} के महत्व का विश्लेषण कीजिए।", difficulty = "Moderate", question_type = "mains", marks = 10, word_limit = 150),
            TopicQuestionDto(9102, question = "${target.topic} से जुड़ी प्रमुख चुनौतियों और आगे की राह पर चर्चा कीजिए।", difficulty = "Moderate", question_type = "mains", marks = 15, word_limit = 250)
        )
    }
}

@Composable
fun DemoSyllabusScreen(exam: String, title: String, onTopic: (StudyTarget) -> Unit, back: () -> Unit) {
    val rows = if (exam == "prelims") DemoTestData.prelims else DemoTestData.mains
    var open by remember { mutableStateOf<String?>(null) }
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(20.dp)) {
        TextButton(onClick = back) { Text("← $title", style = MaterialTheme.typography.titleLarge) }
        Text("TEST MODE • Original flow", style = MaterialTheme.typography.labelMedium)
        rows.forEachIndexed { i, row ->
            val rowKey = "${row.paper}-${row.subject}-$i"
            Card(onClick = { open = if (open == rowKey) null else rowKey }, modifier = Modifier.fillMaxWidth().padding(vertical = 6.dp)) {
                Column(Modifier.padding(18.dp)) {
                    Text(row.paper, style = MaterialTheme.typography.labelMedium)
                    Text(row.subject, fontWeight = FontWeight.Bold)
                    if (open == rowKey) {
                        Spacer(Modifier.height(10.dp))
                        row.topics.forEachIndexed { n, topic ->
                            TextButton(onClick = { onTopic(StudyTarget(exam, row.paper, row.subject, topic)) }, modifier = Modifier.fillMaxWidth()) {
                                Text("${n + 1}. $topic", modifier = Modifier.fillMaxWidth())
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun DemoTopicStudyScreen(target: StudyTarget, onPractice: () -> Unit, back: () -> Unit) {
    val targetKey = DemoTestData.key(target)
    var completed by remember { mutableStateOf(DemoTestData.completed.contains(targetKey)) }
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(20.dp)) {
        TextButton(onClick = back) { Text("← Topic") }
        Text(target.topic, style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
        Text("${target.paper} • ${target.subject}")
        Card(Modifier.fillMaxWidth().padding(top = 14.dp)) {
            Column(Modifier.padding(18.dp)) {
                Text(if (completed) "✅ Topic Complete" else "Topic अभी complete नहीं है", fontWeight = FontWeight.Bold)
                Button(onClick = {
                    completed = !completed
                    if (completed) {
                        if (!DemoTestData.completed.contains(targetKey)) DemoTestData.completed.add(targetKey)
                    } else DemoTestData.completed.remove(targetKey)
                }, modifier = Modifier.fillMaxWidth().padding(top = 10.dp)) {
                    Text(if (completed) "Undo Complete" else "Mark Complete")
                }
            }
        }
        Card(Modifier.fillMaxWidth().padding(top = 10.dp)) {
            Column(Modifier.padding(18.dp)) {
                Text("Question Bank", fontWeight = FontWeight.Bold)
                Text(if (completed) "Test questions ready • section unlocked" else "Complete करने पर question section unlock होगा")
                if (completed) Button(onClick = onPractice, modifier = Modifier.fillMaxWidth().padding(top = 8.dp)) { Text("Questions खोलें") }
            }
        }
        Card(Modifier.fillMaxWidth().padding(top = 10.dp)) { Column(Modifier.padding(18.dp)) { Text("Class Notes", fontWeight = FontWeight.Bold); Text("PDF • Photo • Gallery • Camera upload flow") } }
        Card(Modifier.fillMaxWidth().padding(top = 10.dp)) { Column(Modifier.padding(18.dp)) { Text("Current Affairs", fontWeight = FontWeight.Bold); Text("Live verified data production backend से आएगा") } }
    }
}

@Composable
fun DemoQuestionScreen(target: StudyTarget, onWriteAnswer: (TopicQuestionDto) -> Unit, back: () -> Unit) {
    val questions = DemoTestData.questions(target)
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(20.dp)) {
        TextButton(onClick = back) { Text("← ${target.topic}") }
        Text(target.topic, style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
        Text("TEST MODE • इसी topic के questions")
        questions.forEachIndexed { i, question ->
            Card(Modifier.fillMaxWidth().padding(vertical = 7.dp)) {
                Column(Modifier.padding(16.dp)) {
                    Text("Q${i + 1}. ${question.question}", fontWeight = FontWeight.SemiBold)
                    if (target.exam == "prelims") {
                        question.options.forEachIndexed { n, option -> Text("${('A'.code + n).toChar()}. $option", Modifier.padding(top = 4.dp)) }
                    } else {
                        Text("${question.marks} marks • ${question.word_limit} words", Modifier.padding(top = 8.dp))
                        Button(onClick = { onWriteAnswer(question) }, modifier = Modifier.fillMaxWidth().padding(top = 8.dp)) { Text("Answer लिखें / Upload करें") }
                    }
                }
            }
        }
    }
}
