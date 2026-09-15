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
    var practiceExam by remember{mutableStateOf("prelims")}

    if(token.isBlank()){AuthScreen{newToken->prefs.edit().putString("token",newToken).apply();token=newToken};return}
    val demo=DemoMode.ENABLED&&token==DemoMode.TOKEN
    fun logout(){prefs.edit().remove("token").apply();token=""}

    Scaffold(bottomBar={NavigationBar{listOf("Home","Prelims","Mains","Optional").forEach{label->NavigationBarItem(selected=page.equals(label,true),onClick={page=label.lowercase()},icon={},label={Text(label)})}}}){padding->
        Box(Modifier.padding(padding).fillMaxSize()){
            when(page){
                "home"->if(demo) DemoHomeScreen(onOpen={page=it},onLogout={logout()}) else HomeScreen(token,onPrelims={page="prelims"},onMains={page="mains"},onOptional={page="optional"},onLogout={logout()})
                "prelims"->SimpleSection("PRELIMS",listOf("📚 पढ़ाई करें","🤖 AI Teacher","🧠 Practice","⏱ Mock Test","📜 PYQ","📰 Current Affairs","🗂 Class Notes","❌ Wrong Questions","🔄 Revision"),onItem={item->when{item.startsWith("📚")->page=if(demo)"demo_prelims_syllabus" else "prelims_syllabus";item.startsWith("🤖")->page=if(demo)"demo_ai" else "ai_teacher";item.startsWith("🧠")->if(demo)page="demo_practice" else {practiceExam="prelims";page="completed_practice"};item.startsWith("⏱")->page="demo_mock";item.startsWith("📜")->page=if(demo)"demo_pyq" else "prelims_pyq";item.startsWith("📰")->if(demo)page="demo_current" else {currentExam="prelims";page="current_affairs"};item.startsWith("🗂")->if(demo)page="demo_notes" else {notesExam="prelims";page="class_notes"};item.startsWith("❌")->if(demo)page="demo_wrong" else {wrongExam="prelims";page="wrong_questions"};else->page="demo_revision"}}){page="home"}
                "mains"->SimpleSection("MAINS",listOf("📚 GS / Essay पढ़ें","🤖 AI Teacher","✍ Answer Writing","📄 Test / PDF Paper","📜 PYQ","📰 Mains Current Affairs","🗂 Class Notes","❌ Wrong Questions","🔄 Revision"),onItem={item->when{item.startsWith("📚")->page=if(demo)"demo_mains_syllabus" else "mains_syllabus";item.startsWith("🤖")->page=if(demo)"demo_ai" else "ai_teacher";item.startsWith("✍")->if(demo)page="demo_answer" else {practiceExam="mains";page="completed_practice"};item.startsWith("📄")->page="demo_mains_test";item.startsWith("📜")->page=if(demo)"demo_pyq" else "mains_pyq";item.startsWith("📰")->if(demo)page="demo_current" else {currentExam="mains";page="current_affairs"};item.startsWith("🗂")->if(demo)page="demo_notes" else {notesExam="mains";page="class_notes"};item.startsWith("❌")->if(demo)page="demo_wrong" else {wrongExam="mains";page="wrong_questions"};else->page="demo_revision"}}){page="home"}
                "optional"->if(demo) DemoFeatureScreen("OPTIONAL",listOf("Optional Subject Selection","Paper I","Paper II","Syllabus","PYQ","Answer Writing","Class Notes")){page="home"} else OptionalScreen(token,onNotes={notesExam="optional";page="class_notes"}){page="home"}
                "prelims_syllabus"->SyllabusScreen(token,"prelims","PRELIMS SYLLABUS",onTopic={_,_->}){page="prelims"}
                "mains_syllabus"->SyllabusScreen(token,"mains","MAINS SYLLABUS",onTopic={_,_->}){page="mains"}
                "prelims_pyq"->PyqScreen(token,"prelims"){page="prelims"}
                "mains_pyq"->PyqScreen(token,"mains"){page="mains"}
                "current_affairs"->CurrentAffairsScreen(token,currentExam){page=if(currentExam=="prelims")"prelims" else "mains"}
                "wrong_questions"->WrongQuestionsScreen(token,wrongExam){page=if(wrongExam=="prelims")"prelims" else "mains"}
                "class_notes"->ClassNotesScreen(context,token,notesExam){page="home"}
                "completed_practice"->CompletedPracticeScreen(token,practiceExam,onBack={page=if(practiceExam=="prelims")"prelims" else "mains"},onOpenSection={})
                "ai_teacher"->AiTeacherScreen(token){page="home"}
                "demo_prelims_syllabus"->DemoFeatureScreen("PRELIMS SYLLABUS",listOf("GS Paper-I","CSAT","Subject → Topic → Subtopic","Completed Topic Questions")){page="prelims"}
                "demo_mains_syllabus"->DemoFeatureScreen("MAINS SYLLABUS",listOf("Essay","GS-I","GS-II","GS-III","GS-IV","Subject → Topic → Subtopic")){page="mains"}
                "demo_ai"->DemoFeatureScreen("AI TEACHER",listOf("Prelims View","Mains View","Quick Revision","Verified Official Knowledge")){page="home"}
                "demo_practice"->DemoFeatureScreen("PRACTICE",listOf("Completed Topic Sections","100 Prelims Questions / Topic","No-repeat Question Bank","Wrong Questions")){page="prelims"}
                "demo_mock"->DemoFeatureScreen("PRELIMS MOCK TEST",listOf("GS Paper-I","CSAT","Timer","Negative Marking 1/3","Completed Topics Combined Mock")){page="prelims"}
                "demo_answer"->DemoFeatureScreen("MAINS ANSWER WRITING",listOf("10/15 Marks","150/250 Words","PDF / Photo / Camera Upload","UPSC-pattern AI Evaluation","Model Answer Unlock")){page="mains"}
                "demo_mains_test"->DemoFeatureScreen("MAINS TEST / PDF",listOf("Essay","GS-I","GS-II","GS-III","GS-IV","QCA-style Paper","Answer Space")){page="mains"}
                "demo_pyq"->DemoFeatureScreen("PYQ",listOf("Official UPSC Papers","Prelims","Mains","Optional Paper I & II")){page="home"}
                "demo_current"->DemoFeatureScreen("CURRENT AFFAIRS",listOf("Daily Official-source Updates","Date-wise Archive","Prelims Relevance","Mains Relevance")){page="home"}
                "demo_notes"->DemoFeatureScreen("CLASS NOTES",listOf("Prelims / Mains / Optional","Subject → Topic → Subtopic","PDF","Photo / Gallery","Camera")){page="home"}
                "demo_wrong"->DemoFeatureScreen("WRONG QUESTIONS",listOf("Prelims","Mains","Topic-wise Review","Revision")){page="home"}
                "demo_revision"->DemoFeatureScreen("REVISION",listOf("Due Revision","Completed Topics","Wrong Questions","Quick Revision")){page="home"}
            }
        }
    }
}

@Composable
private fun DemoHomeScreen(onOpen:(String)->Unit,onLogout:()->Unit){
    Column(Modifier.fillMaxSize().padding(20.dp)){
        Text("UPSC",style=MaterialTheme.typography.headlineLarge)
        Text("TEST MODE • पूरा original structure देखने के लिए",modifier=Modifier.padding(bottom=16.dp))
        listOf("PRELIMS" to "prelims","MAINS" to "mains","OPTIONAL" to "optional","AI TEACHER" to "demo_ai","CURRENT AFFAIRS" to "demo_current","CLASS NOTES" to "demo_notes","PYQ" to "demo_pyq","REVISION" to "demo_revision").forEach{(title,target)->
            ElevatedCard(onClick={onOpen(target)},modifier=Modifier.fillMaxWidth().padding(vertical=5.dp),elevation=CardDefaults.elevatedCardElevation(defaultElevation=7.dp)){Text(title,style=MaterialTheme.typography.titleMedium,modifier=Modifier.padding(18.dp))}
        }
        TextButton(onClick=onLogout){Text("Test Mode से बाहर जाएँ")}
    }
}

@Composable
private fun DemoFeatureScreen(title:String,items:List<String>,onBack:()->Unit){
    Column(Modifier.fillMaxSize().padding(20.dp)){
        TextButton(onClick=onBack){Text("← Back")}
        Text(title,style=MaterialTheme.typography.headlineSmall)
        Text("TEST MODE",style=MaterialTheme.typography.labelMedium,modifier=Modifier.padding(bottom=12.dp))
        items.forEach{item->ElevatedCard(modifier=Modifier.fillMaxWidth().padding(vertical=5.dp),elevation=CardDefaults.elevatedCardElevation(defaultElevation=6.dp)){Text(item,modifier=Modifier.padding(18.dp))}}
    }
}
