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
fun WrongQuestionsScreen(token:String,exam:String,back:()->Unit){
    var rows by remember{mutableStateOf<List<WrongQuestionDto>>(emptyList())}
    var loading by remember{mutableStateOf(true)}
    var error by remember{mutableStateOf("")}
    LaunchedEffect(token,exam){
        try{rows=ApiClient.api.wrongQuestions(ApiClient.bearer(token)).filter{it.exam==exam}}
        catch(_:Exception){error="Wrong Question Notebook load नहीं हुआ।"}
        finally{loading=false}
    }
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(20.dp)){
        TextButton(onClick=back){Text("← Wrong Questions")}
        Text(if(exam=="prelims")"Prelims Wrong Question Notebook" else "Mains Wrong Question Notebook",style=MaterialTheme.typography.headlineSmall,fontWeight=FontWeight.Bold)
        if(loading)LinearProgressIndicator(Modifier.fillMaxWidth().padding(vertical=12.dp))
        if(error.isNotBlank())Text(error,color=MaterialTheme.colorScheme.error)
        if(!loading&&rows.isEmpty()&&error.isBlank())Text("अभी कोई latest wrong question नहीं है।",modifier=Modifier.padding(vertical=18.dp))
        rows.forEachIndexed{i,q->
            Card(Modifier.fillMaxWidth().padding(vertical=7.dp)){
                Column(Modifier.padding(16.dp)){
                    Text("${i+1}. ${q.question}",fontWeight=FontWeight.Bold)
                    Text("${q.subject} → ${q.topic} • ${q.difficulty}",style=MaterialTheme.typography.labelMedium,modifier=Modifier.padding(top=6.dp))
                    if(q.options.isNotEmpty())q.options.forEachIndexed{n,opt->Text("${('A'.code+n).toChar()}. $opt",modifier=Modifier.padding(top=5.dp))}
                    if(!q.last_answer.isNullOrBlank())Text("पिछला उत्तर: ${q.last_answer}",modifier=Modifier.padding(top=9.dp))
                }
            }
        }
    }
}
