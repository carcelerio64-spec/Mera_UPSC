package com.upscprep.app

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.launch

@Composable
fun PrelimsCombinedMockScreen(token:String,back:()->Unit){
 val scope=rememberCoroutineScope();var paper by remember{mutableStateOf("GS Paper-I")};var data by remember{mutableStateOf<PrelimsMockDto?>(null)};var err by remember{mutableStateOf("")};var answers by remember{mutableStateOf<Map<String,String>>(emptyMap())};var result by remember{mutableStateOf<MockResultDto?>(null)}
 fun load(){scope.launch{err="";result=null;answers=emptyMap();try{data=ApiClient.api.prelimsCombinedMock(ApiClient.bearer(token),paper)}catch(e:Exception){err="Mock load नहीं हुआ। Backend connection जाँचें।"}}}
 LaunchedEffect(paper){load()}
 Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp)){TextButton(onClick=back){Text("← PRELIMS")};Text("Combined Mock Test",style=MaterialTheme.typography.headlineSmall);Row{listOf("GS Paper-I","CSAT").forEach{p->FilterChip(selected=paper==p,onClick={paper=p},label={Text(p)},modifier=Modifier.padding(end=8.dp))}}
 if(err.isNotBlank())Text(err,color=MaterialTheme.colorScheme.error);data?.let{d->Text("Completed topics only • ${d.questions.size}/${d.required_questions} questions",Modifier.padding(vertical=8.dp));if(d.generation_needed>0)Card(Modifier.fillMaxWidth()){Text("Full paper के लिए ${d.generation_needed} verified unique questions और चाहिए। उपलब्ध questions से practice कर सकते हैं।",Modifier.padding(14.dp))};d.questions.forEachIndexed{i,q->Card(Modifier.fillMaxWidth().padding(vertical=6.dp)){Column(Modifier.padding(14.dp)){Text("Q${i+1}. ${q.question}");q.options.forEach{op->Row{RadioButton(selected=answers[q.id.toString()]==op,onClick={answers=answers+(q.id.toString() to op)});Text(op,Modifier.padding(top=12.dp))}}}}};if(d.questions.isNotEmpty())Button(onClick={scope.launch{try{result=ApiClient.api.submitPrelimsCombinedMock(ApiClient.bearer(token),MockSubmitRequest(d.questions.map{it.id},answers))}catch(e:Exception){err="Submit नहीं हुआ।"}}},modifier=Modifier.fillMaxWidth().padding(top=12.dp)){Text("Submit Mock")}}
 result?.let{r->Card(Modifier.fillMaxWidth().padding(top=12.dp)){Column(Modifier.padding(16.dp)){Text("Score: ${r.score}",style=MaterialTheme.typography.titleLarge);Text("Correct ${r.correct} • Wrong ${r.wrong} • Blank ${r.blank}");Text("Wrong answer penalty: 1/3")}}}}
}

@Composable
fun MainsCombinedPaperScreen(token:String,back:()->Unit){
 val scope=rememberCoroutineScope();var paper by remember{mutableStateOf("GS-I")};var data by remember{mutableStateOf<MainsPaperDto?>(null)};var err by remember{mutableStateOf("")}
 fun load(){scope.launch{err="";try{data=ApiClient.api.mainsCombinedPaper(ApiClient.bearer(token),paper)}catch(e:Exception){err="Mains paper load नहीं हुआ। Backend connection जाँचें।"}}}
 LaunchedEffect(paper){load()}
 Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp)){TextButton(onClick=back){Text("← MAINS")};Text("Mains Combined Paper",style=MaterialTheme.typography.headlineSmall);Row(Modifier.fillMaxWidth()){listOf("GS-I","GS-II","GS-III","GS-IV").forEach{p->FilterChip(selected=paper==p,onClick={paper=p},label={Text(p)},modifier=Modifier.padding(end=5.dp))}};if(err.isNotBlank())Text(err,color=MaterialTheme.colorScheme.error);data?.let{d->Text("3 Hours • 250 Marks • Completed topics only",Modifier.padding(vertical=10.dp));if(!d.ready)Card(Modifier.fillMaxWidth()){Text("Full 20-question paper के लिए ${d.generation_needed} verified unique questions और चाहिए।",Modifier.padding(16.dp))};d.questions.forEach{q->Card(Modifier.fillMaxWidth().padding(vertical=6.dp)){Column(Modifier.padding(14.dp)){Text("Q${q.number}. ${q.question}");Text("${q.marks} Marks • ${q.word_limit} words",style=MaterialTheme.typography.labelMedium)}}}}}
}
