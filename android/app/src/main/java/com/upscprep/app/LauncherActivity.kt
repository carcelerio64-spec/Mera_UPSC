package com.upscprep.app

import android.content.Context
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier

class LauncherActivity : ComponentActivity(){override fun onCreate(savedInstanceState:Bundle?){super.onCreate(savedInstanceState);setContent{MaterialTheme{UpscAppRoot(this)}}}}
@Composable fun UpscAppRoot(context:Context){
 val prefs=remember{context.getSharedPreferences("upsc_session",Context.MODE_PRIVATE)};val saved=remember{prefs.getString("token","")?:""};var token by remember{mutableStateOf(if(saved==DemoMode.TOKEN)"" else saved)};var page by remember{mutableStateOf("home")};var notesExam by remember{mutableStateOf("mains")};var currentExam by remember{mutableStateOf("prelims")};var wrongExam by remember{mutableStateOf("prelims")};var practiceExam by remember{mutableStateOf("prelims")};var target by remember{mutableStateOf<StudyTarget?>(null)};var section by remember{mutableStateOf<QuestionSectionDto?>(null)};var answerQ by remember{mutableStateOf<TopicQuestionDto?>(null)}
 if(token.isBlank()){AuthScreen{t->prefs.edit().putString("token",t).apply();token=t};return};fun logout(){prefs.edit().remove("token").apply();token=""}
 Scaffold(bottomBar={NavigationBar{listOf("Home","Prelims","Mains","Optional").forEach{x->NavigationBarItem(selected=page.equals(x,true),onClick={page=x.lowercase()},icon={},label={Text(x)})}}}){pad->Box(Modifier.padding(pad).fillMaxSize()){when(page){
 "home"->HomeScreen(token,{page="prelims"},{page="mains"},{page="optional"},{logout()})
 "prelims"->SimpleSection("PRELIMS",listOf("📚 पढ़ाई करें","🤖 AI Teacher","🧠 Practice","⏱ Mock Test","📜 PYQ","📰 Current Affairs","🗂 Class Notes","❌ Wrong Questions","🔄 Revision"),{x->when{x.startsWith("📚")->page="prelims_syllabus";x.startsWith("🤖")->page="ai_teacher";x.startsWith("🧠")->{practiceExam="prelims";page="completed_practice"};x.startsWith("⏱")->page="combined_mock";x.startsWith("📜")->page="prelims_pyq";x.startsWith("📰")->{currentExam="prelims";page="current_affairs"};x.startsWith("🗂")->{notesExam="prelims";page="class_notes"};x.startsWith("❌")||x.startsWith("🔄")->{wrongExam="prelims";page="wrong_questions"}}},{page="home"})
 "mains"->SimpleSection("MAINS",listOf("📚 GS / Essay पढ़ें","🤖 AI Teacher","✍ Answer Writing","📄 Test / PDF Paper","📜 PYQ","📰 Mains Current Affairs","🗂 Class Notes","❌ Wrong Questions","🔄 Revision"),{x->when{x.startsWith("📚")->page="mains_syllabus";x.startsWith("🤖")->page="ai_teacher";x.startsWith("✍")->{practiceExam="mains";page="completed_practice"};x.startsWith("📄")->page="mains_combined";x.startsWith("📜")->page="mains_pyq";x.startsWith("📰")->{currentExam="mains";page="current_affairs"};x.startsWith("🗂")->{notesExam="mains";page="class_notes"};x.startsWith("❌")||x.startsWith("🔄")->{wrongExam="mains";page="wrong_questions"}}},{page="home"})
 "optional"->OptionalScreen(token,{notesExam="optional";page="class_notes"}){page="home"}
 "prelims_syllabus"->SyllabusScreen(token,"prelims","PRELIMS SYLLABUS",{r,t->target=StudyTarget("prelims",r.paper,r.subject,t);page="topic_study"}){page="prelims"}
 "mains_syllabus"->SyllabusScreen(token,"mains","MAINS SYLLABUS",{r,t->target=StudyTarget("mains",r.paper,r.subject,t);page="topic_study"}){page="mains"}
 "topic_study"->target?.let{t->TopicStudyV2Screen(token,t){page=if(t.exam=="prelims")"prelims_syllabus" else "mains_syllabus"}}
 "prelims_pyq"->PyqScreen(token,"prelims"){page="prelims"};"mains_pyq"->PyqScreen(token,"mains"){page="mains"}
 "current_affairs"->CurrentAffairsScreen(token,currentExam){page=if(currentExam=="prelims")"prelims" else "mains"}
 "wrong_questions"->WrongQuestionsScreen(token,wrongExam){page=if(wrongExam=="prelims")"prelims" else "mains"}
 "class_notes"->ClassNotesScreen(context,token,notesExam){page=if(notesExam=="optional")"optional" else notesExam}
 "ai_teacher"->AiTeacherScreen(token){page="home"}
 "completed_practice"->CompletedPracticeScreen(token,practiceExam,{page=practiceExam},{section=it;page="topic_questions"})
 "topic_questions"->section?.let{s->TopicQuestionListScreen(token,s,{page="completed_practice"},{q->answerQ=q;page="mains_answer"})}
 "mains_answer"->answerQ?.let{q->MainsAnswerWritingScreen(context,token,q){page="topic_questions"}}
 "combined_mock"->PrelimsCombinedMockScreen(token){page="prelims"}
 "mains_combined"->MainsCombinedPaperScreen(token){page="mains"}
 }}}}
