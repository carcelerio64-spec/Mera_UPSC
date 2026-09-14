package com.upscprep.app

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.launch

@Composable
fun TopicStudyV2Screen(token:String,target:StudyTarget,back:()->Unit){
    val scope=rememberCoroutineScope()
    var data by remember{mutableStateOf<TopicStudyDto?>(null)}
    var error by remember{mutableStateOf("")}
    var busy by remember{mutableStateOf(false)}

    suspend fun load(){
        try{data=ApiClient.api.topicStudy(ApiClient.bearer(token),target.exam,target.paper,target.subject,target.topic);error=""}
        catch(_:Exception){error="Topic data load नहीं हुआ"}
    }
    LaunchedEffect(target){load()}

    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(20.dp)){
        TextButton(onClick=back){Text("← Topic")}
        Text(target.topic,style=MaterialTheme.typography.headlineSmall,fontWeight=FontWeight.Bold)
        Text("${target.paper} • ${target.subject}")
        if(error.isNotBlank())Text(error,color=MaterialTheme.colorScheme.error,modifier=Modifier.padding(top=8.dp))

        Card(Modifier.fillMaxWidth().padding(top=14.dp)){Column(Modifier.padding(18.dp)){
            Text(if(data?.completed==true)"✅ Topic Complete" else "Topic अभी complete नहीं है",fontWeight=FontWeight.Bold)
            Text(if(data?.completed==true)"Question section unlocked" else "Complete करने पर अलग question section unlock होगा")
            Button(enabled=!busy,onClick={scope.launch{
                busy=true
                try{ApiClient.api.setTopicCompletion(ApiClient.bearer(token),TopicCompletionRequest(target.exam,target.paper,target.subject,target.topic,data?.completed!=true));load()}
                catch(_:Exception){error="Completion save नहीं हुआ"}
                finally{busy=false}
            }},modifier=Modifier.fillMaxWidth().padding(top=10.dp)){Text(if(data?.completed==true)"Undo Complete" else "Mark Complete")}
        }}

        Card(Modifier.fillMaxWidth().padding(vertical=7.dp)){Column(Modifier.padding(18.dp)){
            Text("Question Bank",fontWeight=FontWeight.Bold)
            Text("Saved unique questions: ${data?.question_bank_count?:0}/${data?.question_target?:0}")
            if(data?.completed==true&&data?.generation_needed?:0>0)Text("बाकी unique questions: ${data?.generation_needed}")
        }}
        Card(Modifier.fillMaxWidth().padding(vertical=7.dp)){Column(Modifier.padding(18.dp)){
            Text("Class Notes",fontWeight=FontWeight.Bold)
            if(data?.class_notes.isNullOrEmpty())Text("इस topic पर अभी कोई note upload नहीं है।") else data?.class_notes?.forEach{Text("• ${it.title} (${it.file_type})",modifier=Modifier.padding(top=6.dp))}
        }}
        Card(Modifier.fillMaxWidth().padding(vertical=7.dp)){Column(Modifier.padding(18.dp)){Text("Current Affairs",fontWeight=FontWeight.Bold);Text("Linked saved items: ${data?.current_affairs?.size?:0}")}}
    }
}
