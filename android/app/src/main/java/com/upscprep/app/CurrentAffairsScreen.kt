package com.upscprep.app

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalUriHandler
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.launch
import java.time.LocalDate

@Composable
fun CurrentAffairsScreen(token:String, examMode:String, back:()->Unit){
    val scope=rememberCoroutineScope()
    val uriHandler=LocalUriHandler.current
    var date by remember{mutableStateOf(LocalDate.now().toString())}
    var subject by remember{mutableStateOf("")}
    var rows by remember{mutableStateOf<List<CurrentAffairDto>>(emptyList())}
    var loading by remember{mutableStateOf(false)}
    var error by remember{mutableStateOf("")}

    fun load(){
        scope.launch{
            loading=true;error=""
            try{
                rows=ApiClient.api.currentAffairs(
                    ApiClient.bearer(token),
                    date,
                    subject.trim().ifBlank{null},
                    100,
                )
            }catch(_:Exception){error="Current Affairs load नहीं हुआ।"}
            finally{loading=false}
        }
    }
    LaunchedEffect(Unit){load()}

    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(20.dp)){
        TextButton(onClick=back){Text("← Current Affairs")}
        Text(
            if(examMode=="prelims") "Prelims Current Affairs" else "Mains Current Affairs",
            style=MaterialTheme.typography.headlineSmall,
            fontWeight=FontWeight.Bold,
        )
        OutlinedTextField(date,{date=it},label={Text("Date (YYYY-MM-DD)")},modifier=Modifier.fillMaxWidth(),singleLine=true)
        OutlinedTextField(subject,{subject=it},label={Text("Subject (optional)")},modifier=Modifier.fillMaxWidth(),singleLine=true)
        Button(onClick={load()},modifier=Modifier.fillMaxWidth()){Text("देखें")}
        if(loading)LinearProgressIndicator(Modifier.fillMaxWidth().padding(vertical=10.dp))
        if(error.isNotBlank())Text(error,color=MaterialTheme.colorScheme.error,modifier=Modifier.padding(vertical=8.dp))
        if(!loading&&rows.isEmpty()&&error.isBlank())Text("इस तारीख के लिए कोई saved update नहीं मिला।",modifier=Modifier.padding(vertical=16.dp))
        rows.forEach{item->
            Card(Modifier.fillMaxWidth().padding(vertical=7.dp)){
                Column(Modifier.padding(16.dp)){
                    Text("${item.source_name} • ${item.subject}",style=MaterialTheme.typography.labelMedium)
                    Spacer(Modifier.height(5.dp))
                    Text(item.title,fontWeight=FontWeight.Bold)
                    if(!item.summary.isNullOrBlank())Text(item.summary,modifier=Modifier.padding(top=8.dp))
                    Spacer(Modifier.height(10.dp))
                    if(examMode=="prelims"&&!item.prelims_relevance.isNullOrBlank()){
                        Text("Prelims relevance",fontWeight=FontWeight.Bold)
                        Text(item.prelims_relevance)
                    }
                    if(examMode=="mains"&&!item.mains_relevance.isNullOrBlank()){
                        Text("Mains relevance",fontWeight=FontWeight.Bold)
                        Text(item.mains_relevance)
                    }
                    TextButton(onClick={uriHandler.openUri(item.source_url)}){Text("Official source ↗")}
                }
            }
        }
    }
}
