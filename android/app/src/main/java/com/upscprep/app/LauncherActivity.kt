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

class LauncherActivity:ComponentActivity(){
    override fun onCreate(savedInstanceState:Bundle?){super.onCreate(savedInstanceState);setContent{MaterialTheme{UpscAppRoot(this)}}}
}

@Composable
fun UpscAppRoot(context:Context){
    val prefs=remember{context.getSharedPreferences("upsc_session",Context.MODE_PRIVATE)}
    val savedToken=remember{prefs.getString("token","")?:""}
    var token by remember{mutableStateOf(if(savedToken==DemoMode.TOKEN&&!DemoMode.ENABLED)"" else savedToken)}
    var page by remember{mutableStateOf("home")}
    var notesExam by remember{mutableStateOf("mains")}
    var currentExam by remember{mutableStateOf("prelims")}
    var wrongExam by remember{mutableStateOf("prelims")}
    var studyTarget by remember{mutableStateOf<StudyTarget?>(null)}
    var practiceExam by remember{mutableStateOf("prelims")}
    var selectedSection by remember{mutableStateOf<QuestionSectionDto?>(null)}
    var answerQuestion by remember{mutableStateOf<TopicQuestionDto?>(null)}

    if(token.isBlank()){AuthScreen{newToken->prefs.edit().putString("token",newToken).apply();token=newToken};return}

    val demo=DemoMode.ENABLED&&token==DemoMode.TOKEN
    Scaffold(bottomBar={NavigationBar{listOf("Home","Prelims","Mains","Optional").forEach{label->NavigationBarItem(selected=page.equals(label,true),onClick={page=label.lowercase()},icon={},label={Text(label)})}}}){padding->
        Box(Modifier.padding(padding).fillMaxSize()){
            if(demo){
                DemoHomeScreen(onLogout={prefs.edit().remove("token").apply();token=""})
            }else when(page){
                "home"->HomeScreen(token,onPrelims={page="prelims"},onMains={page="mains"},onOptional={page="optional"},onLogout={prefs.edit().remove("token").apply();token=""})
                "prelims"->SimpleSection("PRELIMS",listOf("📚 पढ़ाई करें","🤖 AI Teacher","🧠 Practice","⏱ Mock Test","📜 PYQ","📰 Current Affairs","🗂 Class Notes","❌ Wrong Questions","🔄 Revision"),onItem={item->when{item.startsWith("📚")->page="prelims_syllabus";item.startsWith("🤖")->page="ai_teacher";item.startsWith("🧠")->{practiceExam="prelims";page="completed_practice"};item.startsWith("📜")->page="prelims_pyq";item.startsWith("📰")->{currentExam="prelims";page="current_affairs"};item.startsWith("🗂")->{notesExam="prelims";page="class_notes"};item.startsWith("❌")->{wrongExam="prelims";page="wrong_questions"}}}){page="home"}
                "mains"->SimpleSection("MAINS",listOf("📚 GS / Essay पढ़ें","🤖 AI Teacher","✍ Answer Writing","📄 Test / PDF Paper","📜 PYQ","📰 Mains Current Affairs","🗂 Class Notes","❌ Wrong Questions","🔄 Revision"),onItem={item->when{item.startsWith("📚")->page="mains_syllabus";item.startsWith("🤖")->page="ai_teacher";item.startsWith("✍")->{practiceExam="mains";page="completed_practice"};item.startsWith("📜")->page="mains_pyq";item.startsWith("📰")->{currentExam="mains";page="current_affairs"};item.startsWith("🗂")->{notesExam="mains";page="class_notes"};item.startsWith("❌")->{wrongExam="mains";page="wrong_questions"}}}){page="home"}
                "prelims_syllabus"->SyllabusScreen(token,"prelims","PRELIMS SYLLABUS",onTopic={row,topic->studyTarget=StudyTarget("prelims",row.paper,row.subject,topic);page="topic_study"}){page="prelims"}
                "mains_syllabus"->SyllabusScreen(token,"mains","MAINS SYLLABUS",onTopic={row,topic->studyTarget=StudyTarget("mains",row.paper,row.subject,topic);page="topic_study"}){page="mains"}
                "prelims_pyq"->PyqScreen(token,"prelims"){page="prelims"}
                "mains_pyq"->PyqScreen(token,"mains"){page="mains"}
                "current_affairs"->CurrentAffairsScreen(token,currentExam){page=if(currentExam=="prelims")"prelims" else "mains"}
                "wrong_questions"->WrongQuestionsScreen(token,wrongExam){page=if(wrongExam=="prelims")"prelims" else "mains"}
                "optional"->OptionalScreen(token,onNotes={notesExam="optional";page="class_notes"}){page="home"}
                "class_notes"->ClassNotesScreen(context,token,notesExam){page=when(notesExam){"prelims"->"prelims";"mains"->"mains";else->"optional"}}
                "topic_study"->studyTarget?.let{target->TopicStudyV2Screen(token,target){page=if(target.exam=="prelims")"prelims_syllabus" else "mains_syllabus"}}
                "completed_practice"->CompletedPracticeScreen(token,practiceExam,onBack={page=if(practiceExam=="prelims")"prelims" else "mains"},onOpenSection={selectedSection=it;page="topic_questions"})
                "topic_questions"->selectedSection?.let{section->TopicQuestionListScreen(token,section,onBack={page="completed_practice"},onWriteAnswer={q->answerQuestion=q;page="mains_answer"})}
                "mains_answer"->answerQuestion?.let{q->MainsAnswerWritingScreen(context,token,q){page="topic_questions"}}
                "ai_teacher"->AiTeacherScreen(token){page="home"}
            }
        }
    }
}

@Composable
private fun DemoHomeScreen(onLogout:()->Unit){
    Column(Modifier.fillMaxSize().padding(20.dp)){
        Text("UPSC • TEST MODE",style=MaterialTheme.typography.headlineSmall)
        Text("UI और navigation जाँचने के लिए temporary demo चालू है। Backend data fake नहीं किया गया है।",modifier=Modifier.padding(vertical=16.dp))
        Card(Modifier.fillMaxWidth()){Column(Modifier.padding(18.dp)){Text("PRELIMS");Text("MAINS");Text("OPTIONAL");Text("AI Teacher • Practice • Tests • Notes")}}
        TextButton(onClick=onLogout){Text("Test Mode से बाहर जाएँ")}
    }
}
