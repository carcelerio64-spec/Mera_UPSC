package com.upscprep.app

import android.content.Context
import android.graphics.Bitmap
import android.net.Uri
import android.os.Bundle
import android.provider.OpenableColumns
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.launch
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.ByteArrayOutputStream

class MainActivity:ComponentActivity(){
    override fun onCreate(savedInstanceState:Bundle?){
        super.onCreate(savedInstanceState)
        setContent{MaterialTheme{UpscApp(this)}}
    }
}

data class StudyTarget(val exam:String,val paper:String,val subject:String,val topic:String)
data class LocalUpload(val bytes:ByteArray,val name:String,val mime:String)

@Composable
fun UpscApp(context:Context){
    val prefs=remember{context.getSharedPreferences("upsc_session",Context.MODE_PRIVATE)}
    var token by remember{mutableStateOf(prefs.getString("token","")?:"")}
    var page by remember{mutableStateOf("home")}
    var notesExam by remember{mutableStateOf("mains")}
    var studyTarget by remember{mutableStateOf<StudyTarget?>(null)}
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
                "prelims"->SimpleSection("PRELIMS",listOf("📚 पढ़ाई करें","🧠 Practice","⏱ Mock Test","📰 Current Affairs","🗂 Class Notes","🔄 Revision"),onItem={item->when{item.startsWith("📚")->page="prelims_syllabus";item.startsWith("🗂")->{notesExam="prelims";page="class_notes"}}}){page="home"}
                "mains"->SimpleSection("MAINS",listOf("📚 GS / Essay पढ़ें","✍ Answer Writing","📄 Test / PDF Paper","📰 Mains Current Affairs","🗂 Class Notes","🔄 Revision"),onItem={item->when{item.startsWith("📚")->page="mains_syllabus";item.startsWith("🗂")->{notesExam="mains";page="class_notes"}}}){page="home"}
                "prelims_syllabus"->SyllabusScreen(token,"prelims","PRELIMS SYLLABUS",onTopic={row,topic->studyTarget=StudyTarget("prelims",row.paper,row.subject,topic);page="topic_study"}){page="prelims"}
                "mains_syllabus"->SyllabusScreen(token,"mains","MAINS SYLLABUS",onTopic={row,topic->studyTarget=StudyTarget("mains",row.paper,row.subject,topic);page="topic_study"}){page="mains"}
                "optional"->OptionalScreen(token,onNotes={notesExam="optional";page="class_notes"}){page="home"}
                "class_notes"->ClassNotesScreen(context,token,notesExam){page=if(notesExam=="prelims")"prelims" else if(notesExam=="mains")"mains" else "optional"}
                "topic_study"->studyTarget?.let{target->TopicStudyScreen(token,target){page=if(target.exam=="prelims")"prelims_syllabus" else "mains_syllabus"}}
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
    var dash by remember{mutableStateOf<DashboardDto?>(null)};var error by remember{mutableStateOf("")}
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
fun SyllabusScreen(token:String,exam:String,title:String,onTopic:(SyllabusSectionDto,String)->Unit,back:()->Unit){
    var rows by remember{mutableStateOf<List<SyllabusSectionDto>>(emptyList())};var open by remember{mutableStateOf<String?>(null)};var error by remember{mutableStateOf("")}
    LaunchedEffect(exam){try{rows=ApiClient.api.syllabus(exam,ApiClient.bearer(token))}catch(_:Exception){error="Syllabus load नहीं हुआ"}}
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(20.dp)){TextButton(onClick=back){Text("← $title",style=MaterialTheme.typography.titleLarge)};if(error.isNotBlank())Text(error,color=MaterialTheme.colorScheme.error);rows.forEachIndexed{i,row->val key="${row.paper}-${row.subject}-$i";Card(onClick={open=if(open==key)null else key},modifier=Modifier.fillMaxWidth().padding(vertical=6.dp)){Column(Modifier.padding(18.dp)){Text(row.paper,style=MaterialTheme.typography.labelMedium);Text(row.subject,fontWeight=FontWeight.Bold);if(open==key){Spacer(Modifier.height(10.dp));row.topics.forEachIndexed{n,t->TextButton(onClick={onTopic(row,t)},modifier=Modifier.fillMaxWidth()){Text("${n+1}. $t",modifier=Modifier.fillMaxWidth())}}}}}}}
}

@Composable
fun TopicStudyScreen(token:String,target:StudyTarget,back:()->Unit){
    var data by remember{mutableStateOf<TopicStudyDto?>(null)};var error by remember{mutableStateOf("")}
    LaunchedEffect(target){try{data=ApiClient.api.topicStudy(ApiClient.bearer(token),target.exam,target.paper,target.subject,target.topic)}catch(_:Exception){error="Topic data load नहीं हुआ"}}
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(20.dp)){
        TextButton(onClick=back){Text("← Topic")}
        Text(target.topic,style=MaterialTheme.typography.headlineSmall,fontWeight=FontWeight.Bold)
        Text("${target.paper} • ${target.subject}",style=MaterialTheme.typography.bodyMedium)
        Spacer(Modifier.height(16.dp))
        if(error.isNotBlank())Text(error,color=MaterialTheme.colorScheme.error)
        Card(Modifier.fillMaxWidth().padding(vertical=6.dp)){Column(Modifier.padding(18.dp)){Text("Question Bank",fontWeight=FontWeight.Bold);Text("Saved unique questions: ${data?.question_bank_count?:0}")}}
        Card(Modifier.fillMaxWidth().padding(vertical=6.dp)){Column(Modifier.padding(18.dp)){Text("Class Notes",fontWeight=FontWeight.Bold);if(data?.class_notes.isNullOrEmpty())Text("इस topic पर अभी कोई note upload नहीं है।") else data?.class_notes?.forEach{Text("• ${it.title} (${it.file_type})",modifier=Modifier.padding(top=6.dp))}}}
        Card(Modifier.fillMaxWidth().padding(vertical=6.dp)){Column(Modifier.padding(18.dp)){Text("Current Affairs",fontWeight=FontWeight.Bold);Text("Linked saved items: ${data?.current_affairs?.size?:0}")}}
    }
}

@Composable
fun OptionalScreen(token:String,onNotes:()->Unit,back:()->Unit){
    val scope=rememberCoroutineScope();var subjects by remember{mutableStateOf<List<String>>(emptyList())};var selected by remember{mutableStateOf("")};var expanded by remember{mutableStateOf(false)};var message by remember{mutableStateOf("")}
    LaunchedEffect(token){try{subjects=ApiClient.api.optionalSubjects(ApiClient.bearer(token));selected=ApiClient.api.optionalSelection(ApiClient.bearer(token)).subject?:""}catch(_:Exception){message="Optional data load नहीं हुआ"}}
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(20.dp)){TextButton(onClick=back){Text("← OPTIONAL",style=MaterialTheme.typography.titleLarge)};Text("अपना एक Optional चुनें",style=MaterialTheme.typography.headlineSmall,fontWeight=FontWeight.Bold);Box(Modifier.fillMaxWidth().padding(vertical=12.dp)){OutlinedButton(onClick={expanded=true},modifier=Modifier.fillMaxWidth()){Text(if(selected.isBlank())"Optional Subject चुनें" else selected)};DropdownMenu(expanded=expanded,onDismissRequest={expanded=false}){subjects.forEach{s->DropdownMenuItem(text={Text(s)},onClick={selected=s;expanded=false})}}};Button(enabled=selected.isNotBlank(),onClick={scope.launch{try{ApiClient.api.saveOptional(ApiClient.bearer(token),OptionalSaveRequest(selected));message="Optional save हो गया"}catch(_:Exception){message="Optional save नहीं हुआ"}}},modifier=Modifier.fillMaxWidth()){Text("Optional Save करें")};if(message.isNotBlank())Text(message,modifier=Modifier.padding(vertical=10.dp));if(selected.isNotBlank()){Card(Modifier.fillMaxWidth().padding(vertical=6.dp)){Column(Modifier.padding(18.dp)){Text("$selected Paper-I",fontWeight=FontWeight.Bold);Text("Official detailed syllabus load होने पर topics यहीं खुलेंगे")}};Card(Modifier.fillMaxWidth().padding(vertical=6.dp)){Column(Modifier.padding(18.dp)){Text("$selected Paper-II",fontWeight=FontWeight.Bold);Text("Official detailed syllabus load होने पर topics यहीं खुलेंगे")}};Button(onClick=onNotes,modifier=Modifier.fillMaxWidth().padding(top=10.dp)){Text("🗂 Optional Class Notes")}}}
}

@Composable
fun ClassNotesScreen(context:Context,token:String,exam:String,back:()->Unit){
    val scope=rememberCoroutineScope()
    var subject by remember{mutableStateOf("")};var topic by remember{mutableStateOf("")};var title by remember{mutableStateOf("")};var selected by remember{mutableStateOf<LocalUpload?>(null)};var message by remember{mutableStateOf("")};var notes by remember{mutableStateOf<List<ClassNoteDto>>(emptyList())};var busy by remember{mutableStateOf(false)}
    fun loadNotes(){scope.launch{try{notes=ApiClient.api.classNotes(ApiClient.bearer(token))}catch(_:Exception){}}}
    LaunchedEffect(token){loadNotes()}
    val pdfPicker=rememberLauncherForActivityResult(ActivityResultContracts.GetContent()){uri:Uri?->uri?.let{selected=readUri(context,it,"class-note.pdf","application/pdf")}}
    val photoPicker=rememberLauncherForActivityResult(ActivityResultContracts.GetContent()){uri:Uri?->uri?.let{selected=readUri(context,it,"class-note.jpg","image/jpeg")}}
    val camera=rememberLauncherForActivityResult(ActivityResultContracts.TakePicturePreview()){bitmap:Bitmap?->bitmap?.let{val out=ByteArrayOutputStream();it.compress(Bitmap.CompressFormat.JPEG,90,out);selected=LocalUpload(out.toByteArray(),"camera-${System.currentTimeMillis()}.jpg","image/jpeg")}}
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(20.dp)){
        TextButton(onClick=back){Text("← Class Notes")}
        Text("${exam.uppercase()} Class Notes",style=MaterialTheme.typography.headlineSmall,fontWeight=FontWeight.Bold)
        OutlinedTextField(subject,{subject=it},label={Text("Subject")},modifier=Modifier.fillMaxWidth())
        OutlinedTextField(topic,{topic=it},label={Text("Topic")},modifier=Modifier.fillMaxWidth())
        OutlinedTextField(title,{title=it},label={Text("Note का नाम")},modifier=Modifier.fillMaxWidth())
        Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.spacedBy(8.dp)){
            OutlinedButton(onClick={pdfPicker.launch("application/pdf")},modifier=Modifier.weight(1f)){Text("📄 PDF")}
            OutlinedButton(onClick={photoPicker.launch("image/*")},modifier=Modifier.weight(1f)){Text("🖼 Photo")}
            OutlinedButton(onClick={camera.launch(null)},modifier=Modifier.weight(1f)){Text("📷 Camera")}
        }
        selected?.let{Text("Selected: ${it.name}",modifier=Modifier.padding(vertical=8.dp))}
        Button(enabled=!busy&&selected!=null&&subject.isNotBlank()&&topic.isNotBlank()&&title.isNotBlank(),onClick={scope.launch{
            val item=selected?:return@launch;busy=true;message=""
            try{
                val filePart=MultipartBody.Part.createFormData("file",item.name,item.bytes.toRequestBody(item.mime.toMediaTypeOrNull()))
                fun text(v:String)=v.toRequestBody("text/plain".toMediaTypeOrNull())
                ApiClient.api.uploadClassNote(ApiClient.bearer(token),filePart,text(exam),text(subject.trim()),text(topic.trim()),text(title.trim()),text(""),text(""))
                message="Class Note upload हो गया";selected=null;title="";loadNotes()
            }catch(_:Exception){message="Upload नहीं हुआ। File/Internet जाँचें।"}finally{busy=false}
        }},modifier=Modifier.fillMaxWidth()){Text(if(busy)"Upload हो रहा है…" else "Upload करें")}
        if(message.isNotBlank())Text(message,modifier=Modifier.padding(vertical=8.dp))
        Spacer(Modifier.height(12.dp));Text("Saved Notes",fontWeight=FontWeight.Bold)
        notes.filter{it.exam==exam}.forEach{n->Card(Modifier.fillMaxWidth().padding(vertical=5.dp)){Column(Modifier.padding(14.dp)){Text(n.title,fontWeight=FontWeight.Bold);Text("${n.subject} → ${n.topic} • ${n.file_type}")}}}
    }
}

fun readUri(context:Context,uri:Uri,fallbackName:String,fallbackMime:String):LocalUpload?{
    return try{
        val bytes=context.contentResolver.openInputStream(uri)?.use{it.readBytes()}?:return null
        var name=fallbackName
        context.contentResolver.query(uri,arrayOf(OpenableColumns.DISPLAY_NAME),null,null,null)?.use{cursor->if(cursor.moveToFirst()){val i=cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME);if(i>=0)name=cursor.getString(i)?:fallbackName}}
        val mime=context.contentResolver.getType(uri)?:fallbackMime
        LocalUpload(bytes,name,mime)
    }catch(_:Exception){null}
}
