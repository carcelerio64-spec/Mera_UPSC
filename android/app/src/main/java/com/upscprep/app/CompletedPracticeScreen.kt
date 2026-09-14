package com.upscprep.app

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp

@Composable
fun CompletedPracticeScreen(
    token:String,
    exam:String,
    onBack:()->Unit,
    onOpenSection:(QuestionSectionDto)->Unit,
){
    var data by remember{mutableStateOf<QuestionSectionsResponse?>(null)}
    var error by remember{mutableStateOf("")}
    var loading by remember{mutableStateOf(true)}
    LaunchedEffect(exam){
        loading=true;error=""
        try{data=ApiClient.api.questionSections(ApiClient.bearer(token),exam)}
        catch(_:Exception){error="Completed Topics load नहीं हुए"}
        finally{loading=false}
    }
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(20.dp)){
        TextButton(onClick=onBack){Text("← ${exam.uppercase()} PRACTICE")}
        Text("Completed Topics",style=MaterialTheme.typography.headlineSmall,fontWeight=FontWeight.Bold)
        Text(if(exam=="prelims")"हर completed topic का अलग MCQ section" else "हर completed topic का अलग Mains question section")
        if(loading)LinearProgressIndicator(Modifier.fillMaxWidth().padding(vertical=12.dp))
        if(error.isNotBlank())Text(error,color=MaterialTheme.colorScheme.error)
        val sections=data?.sections.orEmpty()
        if(!loading&&sections.isEmpty())Card(Modifier.fillMaxWidth().padding(top=14.dp)){Text("पहले किसी topic को Complete करें।",Modifier.padding(18.dp))}
        sections.forEach{section->
            Card(onClick={onOpenSection(section)},modifier=Modifier.fillMaxWidth().padding(vertical=7.dp)){
                Column(Modifier.padding(18.dp)){
                    Text(section.paper,style=MaterialTheme.typography.labelMedium)
                    Text(section.subject,fontWeight=FontWeight.Bold)
                    Text(section.topic)
                    Spacer(Modifier.height(8.dp))
                    Text("Questions: ${section.saved_questions}/${section.question_target}")
                    if(section.generation_needed>0)Text("बाकी unique questions: ${section.generation_needed}") else Text("Section ready")
                }
            }
        }
    }
}

@Composable
fun TopicQuestionListScreen(
    token:String,
    section:QuestionSectionDto,
    onBack:()->Unit,
    onWriteAnswer:(TopicQuestionDto)->Unit,
){
    var data by remember{mutableStateOf<TopicQuestionResponse?>(null)}
    var error by remember{mutableStateOf("")}
    var loading by remember{mutableStateOf(true)}
    LaunchedEffect(section.section_key){
        loading=true;error=""
        try{data=ApiClient.api.topicQuestions(ApiClient.bearer(token),section.exam,section.paper,section.subject,section.topic,section.question_target)}
        catch(_:Exception){error="Questions load नहीं हुए"}
        finally{loading=false}
    }
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(20.dp)){
        TextButton(onClick=onBack){Text("← ${section.topic}")}
        Text(section.subject,style=MaterialTheme.typography.labelLarge)
        Text(section.topic,style=MaterialTheme.typography.headlineSmall,fontWeight=FontWeight.Bold)
        Text("इस section में दूसरे topics mix नहीं होंगे।")
        if(loading)LinearProgressIndicator(Modifier.fillMaxWidth().padding(vertical=12.dp))
        if(error.isNotBlank())Text(error,color=MaterialTheme.colorScheme.error)
        data?.questions.orEmpty().forEachIndexed{i,q->
            Card(Modifier.fillMaxWidth().padding(vertical=7.dp)){
                Column(Modifier.padding(16.dp)){
                    Text("Q${i+1}. ${q.question}",fontWeight=FontWeight.SemiBold)
                    if(section.exam=="prelims"){
                        q.options.forEachIndexed{n,opt->Text("${('A'.code+n).toChar()}. $opt",modifier=Modifier.padding(top=4.dp))}
                    }else{
                        val marks=if(q.marks>0)q.marks else 10
                        val words=if(q.word_limit>0)q.word_limit else if(marks==15)250 else 150
                        Text("$marks marks • $words words",modifier=Modifier.padding(top=8.dp))
                        Button(onClick={onWriteAnswer(q)},modifier=Modifier.fillMaxWidth().padding(top=10.dp)){Text("Answer लिखें / Upload करें")}
                    }
                }
            }
        }
    }
}
