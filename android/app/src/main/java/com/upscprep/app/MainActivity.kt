package com.upscprep.app

import android.content.Context
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.launch

class MainActivity:ComponentActivity(){
    override fun onCreate(savedInstanceState:Bundle?){
        super.onCreate(savedInstanceState)
        setContent{MaterialTheme{UpscApp(this)}}
    }
}

@Composable
fun UpscApp(context:Context){
    val prefs=remember{context.getSharedPreferences("upsc_session",Context.MODE_PRIVATE)}
    var token by remember{mutableStateOf(prefs.getString("token","")?:"")}
    var page by remember{mutableStateOf("home")}
    if(token.isBlank()){
        LoginScreen{newToken->prefs.edit().putString("token",newToken).apply();token=newToken}
        return
    }
    Scaffold(bottomBar={NavigationBar{
        listOf("Home","Prelims","Mains","Optional").forEach{label->
            NavigationBarItem(selected=page.equals(label,true),onClick={page=label.lowercase()},icon={},label={Text(label)})
        }
    }}){p->
        Box(Modifier.padding(p).fillMaxSize()){
            when(page){
                "home"->HomeScreen(token,onPrelims={page="prelims"},onMains={page="mains"},onOptional={page="optional"},onLogout={prefs.edit().remove("token").apply();token=""})
                "prelims"->SimpleSection("PRELIMS",listOf("📚 पढ़ाई करें","🧠 Practice","⏱ Mock Test","📰 Current Affairs","🗂 Class Notes","🔄 Revision"),onItem={if(it.startsWith("📚"))page="prelims_syllabus"}){page="home"}
                "mains"->SimpleSection("MAINS",listOf("📚 GS / Essay पढ़ें","✍ Answer Writing","📄 Test / PDF Paper","📰 Mains Current Affairs","🗂 Class Notes","🔄 Revision"),onItem={if(it.startsWith("📚"))page="mains_syllabus"}){page="home"}
                "prelims_syllabus"->SyllabusScreen(token,"prelims","PRELIMS SYLLABUS"){page="prelims"}
                "mains_syllabus"->SyllabusScreen(token,"mains","MAINS SYLLABUS"){page="mains"}
                "optional"->OptionalScreen(token){page="home"}
            }
        }
    }
}

@Composable
fun LoginScreen(onLogin:(String)->Unit){
    val scope=rememberCoroutineScope();var email by remember{mutableStateOf("")};var password by remember{mutableStateOf("")};var busy by remember{mutableStateOf(false)};var error by remember{mutableStateOf("")}
    Column(Modifier.fillMaxSize().padding(24.dp),verticalArrangement=Arrangement.Center){
        Text("UPSC Prep",style=MaterialTheme.typography.headlineLarge,fontWeight=FontWeight.Bold)
        Text("अपनी तैयारी जारी रखें",modifier=Modifier.padding(bottom=20.dp))
        OutlinedTextField(email,{email=it},label={Text("Email")},modifier=Modifier.fillMaxWidth(),singleLine=true)
        Spacer(Modifier.height(10.dp))
        OutlinedTextField(password,{password=it},label={Text("Password")},visualTransformation=PasswordVisualTransformation(),modifier=Modifier.fillMaxWidth(),singleLine=true)
        if(error.isNotBlank())Text(error,color=MaterialTheme.colorScheme.error,modifier=Modifier.padding(top=8.dp))
        Spacer(Modifier.height(14.dp))
        Button(enabled=!busy&&email.isNotBlank()&&password.isNotBlank(),onClick={scope.launch{busy=true;error="";try{onLogin(ApiClient.api.login(email.trim(),password).access_token)}catch(_:Exception){error="Login नहीं हो पाया। Backend/Internet जाँचें।"}finally{busy=false}}},modifier=Modifier.fillMaxWidth()){Text(if(busy)"LOGIN हो रहा है…" else "LOGIN")}
    }
}

@Composable
fun HomeScreen(token:String,onPrelims:()->Unit,onMains:()->Unit,onOptional:()->Unit,onLogout:()->Unit){
    val scope=rememberCoroutineScope();var dash by remember{mutableStateOf<DashboardDto?>(null)};var error by remember{mutableStateOf("")}
    LaunchedEffect(token){try{dash=ApiClient.api.dashboard(ApiClient.bearer(token))}catch(_:Exception){error="Dashboard load नहीं हुआ"}}
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(20.dp)){
        Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.SpaceBetween){Text("UPSC Prep",style=MaterialTheme.typography.titleLarge,fontWeight=FontWeight.Bold);TextButton(onClick=onLogout){Text("Logout")}}
        Spacer(Modifier.height(18.dp));Text("नमस्ते, ${dash?.name?:"User"}",style=MaterialTheme.typography.headlineSmall,fontWeight=FontWeight.Bold)
        if(error.isNotBlank())Text(error,color=MaterialTheme.colorScheme.error)
        Card(Modifier.fillMaxWidth().padding(vertical=12.dp)){Column(Modifier.padding(18.dp)){Text("आज की पढ़ाई",fontWeight=FontWeight.Bold);Text("${dash?.today_topics?:0} Topics बाकी")}}
        BigCard("PRELIMS","पढ़ाई • MCQ • Mock Test",onPrelims)
        BigCard("MAINS","पढ़ाई • Answer • PDF Test",onMains)
        BigCard("OPTIONAL","एक Optional • Paper-I • Paper-II",onOptional)
        Card(Modifier.fillMaxWidth().padding(top=8.dp)){Column(Modifier.padding(18.dp)){Text("जहाँ छोड़ा था वहीं से पढ़ें",fontWeight=FontWeight.Bold);Text(dash?.continue_learning?:"-");Spacer(Modifier.height(6.dp));Text("Progress: ${dash?.overall_progress?:0}% • Revision Due: ${dash?.revision_due?:0}")}}
    }
}

@Composable fun BigCard(title:String,sub:String,click:()->Unit){Card(onClick=click,modifier=Modifier.fillMaxWidth().padding(vertical=8.dp),shape=RoundedCornerShape(22.dp)){Column(Modifier.padding(26.dp)){Text(title,style=MaterialTheme.typography.headlineMedium,fontWeight=FontWeight.Bold);Text(sub)}}}

@Composable
fun SimpleSection(title:String,items:List<String>,onItem:(String)->Unit,back:()->Unit){
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(20.dp)){TextButton(onClick=back){Text("← $title",style=MaterialTheme.typography.titleLarge)};items.forEach{item->Card(onClick={onItem(item)},modifier=Modifier.fillMaxWidth().padding(vertical=7.dp)){Row(Modifier.padding(22.dp).fillMaxWidth(),horizontalArrangement=Arrangement.SpaceBetween){Text(item);Text("›")}}}}
}

@Composable
fun SyllabusScreen(token:String,exam:String,title:String,back:()->Unit){
    var rows by remember{mutableStateOf<List<SyllabusSectionDto>>(emptyList())};var open by remember{mutableStateOf<String?>(null)};var error by remember{mutableStateOf("")}
    LaunchedEffect(exam){try{rows=ApiClient.api.syllabus(exam,ApiClient.bearer(token))}catch(_:Exception){error="Syllabus load नहीं हुआ"}}
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(20.dp)){TextButton(onClick=back){Text("← $title",style=MaterialTheme.typography.titleLarge)};if(error.isNotBlank())Text(error,color=MaterialTheme.colorScheme.error);rows.forEachIndexed{i,row->val key="${row.paper}-${row.subject}-$i";Card(onClick={open=if(open==key)null else key},modifier=Modifier.fillMaxWidth().padding(vertical=6.dp)){Column(Modifier.padding(18.dp)){Text(row.paper,style=MaterialTheme.typography.labelMedium);Text(row.subject,fontWeight=FontWeight.Bold);if(open==key){Spacer(Modifier.height(10.dp));row.topics.forEachIndexed{n,t->Text("${n+1}. $t",modifier=Modifier.padding(vertical=6.dp))}}}}}}
}

@Composable
fun OptionalScreen(token:String,back:()->Unit){
    val scope=rememberCoroutineScope();var subjects by remember{mutableStateOf<List<String>>(emptyList())};var selected by remember{mutableStateOf("")};var expanded by remember{mutableStateOf(false)};var message by remember{mutableStateOf("")}
    LaunchedEffect(token){try{subjects=ApiClient.api.optionalSubjects(ApiClient.bearer(token));selected=ApiClient.api.optionalSelection(ApiClient.bearer(token)).subject?:""}catch(_:Exception){message="Optional data load नहीं हुआ"}}
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(20.dp)){TextButton(onClick=back){Text("← OPTIONAL",style=MaterialTheme.typography.titleLarge)};Text("अपना एक Optional चुनें",style=MaterialTheme.typography.headlineSmall,fontWeight=FontWeight.Bold);Box(Modifier.fillMaxWidth().padding(vertical=12.dp)){OutlinedButton(onClick={expanded=true},modifier=Modifier.fillMaxWidth()){Text(if(selected.isBlank())"Optional Subject चुनें" else selected)};DropdownMenu(expanded=expanded,onDismissRequest={expanded=false}){subjects.forEach{s->DropdownMenuItem(text={Text(s)},onClick={selected=s;expanded=false})}}};Button(enabled=selected.isNotBlank(),onClick={scope.launch{try{ApiClient.api.saveOptional(ApiClient.bearer(token),OptionalSaveRequest(selected));message="Optional save हो गया"}catch(_:Exception){message="Optional save नहीं हुआ"}}},modifier=Modifier.fillMaxWidth()){Text("Optional Save करें")};if(message.isNotBlank())Text(message,modifier=Modifier.padding(vertical=10.dp));if(selected.isNotBlank()){Card(Modifier.fillMaxWidth().padding(vertical=6.dp)){Column(Modifier.padding(18.dp)){Text("$selected Paper-I",fontWeight=FontWeight.Bold);Text("Syllabus • Topics • PYQ • Questions")}};Card(Modifier.fillMaxWidth().padding(vertical=6.dp)){Column(Modifier.padding(18.dp)){Text("$selected Paper-II",fontWeight=FontWeight.Bold);Text("Syllabus • Topics • PYQ • Questions")}}}}
}
