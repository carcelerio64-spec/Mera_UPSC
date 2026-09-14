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
fun AiTeacherScreen(token:String,onBack:()->Unit){
    val scope=rememberCoroutineScope()
    var question by remember{mutableStateOf("")}
    var answer by remember{mutableStateOf<AiTeacherResponse?>(null)}
    var busy by remember{mutableStateOf(false)}
    var error by remember{mutableStateOf("")}

    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(20.dp)){
        TextButton(onClick=onBack){Text("← AI Teacher")}
        Text("🤖 AI UPSC Teacher",style=MaterialTheme.typography.headlineSmall,fontWeight=FontWeight.Bold)
        Text("एक सवाल पूछें — Prelims और Mains दोनों view मिलेंगे।",modifier=Modifier.padding(top=6.dp,bottom=14.dp))
        OutlinedTextField(
            value=question,
            onValueChange={question=it},
            label={Text("अपना UPSC सवाल लिखें")},
            modifier=Modifier.fillMaxWidth().heightIn(min=130.dp)
        )
        Button(
            enabled=!busy && question.trim().length>=2,
            onClick={scope.launch{
                busy=true;error="";answer=null
                try{answer=ApiClient.api.askAiTeacher(ApiClient.bearer(token),AiTeacherAskRequest(question=question.trim()))}
                catch(_:Exception){error="AI Teacher जवाब नहीं दे पाया। Backend AI configuration जाँचें।"}
                finally{busy=false}
            }},
            modifier=Modifier.fillMaxWidth().padding(top=10.dp)
        ){Text(if(busy)"जवाब तैयार हो रहा है…" else "पूछें")}
        if(busy)LinearProgressIndicator(Modifier.fillMaxWidth().padding(vertical=10.dp))
        if(error.isNotBlank())Text(error,color=MaterialTheme.colorScheme.error,modifier=Modifier.padding(vertical=8.dp))

        answer?.let{a->
            Card(Modifier.fillMaxWidth().padding(top=14.dp)){Column(Modifier.padding(16.dp)){
                Text("PRELIMS VIEW",fontWeight=FontWeight.Bold)
                Text(a.prelims_view,modifier=Modifier.padding(top=8.dp))
            }}
            Card(Modifier.fillMaxWidth().padding(top=10.dp)){Column(Modifier.padding(16.dp)){
                Text("MAINS VIEW",fontWeight=FontWeight.Bold)
                Text(a.mains_view,modifier=Modifier.padding(top=8.dp))
            }}
            if(a.quick_revision.isNotEmpty())Card(Modifier.fillMaxWidth().padding(top=10.dp)){Column(Modifier.padding(16.dp)){
                Text("Quick Revision",fontWeight=FontWeight.Bold)
                a.quick_revision.forEach{Text("• $it",modifier=Modifier.padding(top=5.dp))}
            }}
            if(a.source_note.isNotBlank())Text(a.source_note,style=MaterialTheme.typography.labelSmall,modifier=Modifier.padding(top=10.dp))
        }
    }
}
