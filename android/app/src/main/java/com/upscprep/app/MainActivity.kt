package com.upscprep.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp

class MainActivity:ComponentActivity(){override fun onCreate(savedInstanceState:Bundle?){super.onCreate(savedInstanceState);setContent{MaterialTheme{UpscApp()}}}}

@Composable fun UpscApp(){var logged by remember{mutableStateOf(false)};var page by remember{mutableStateOf("home")};if(!logged){LoginScreen{logged=true};return};Scaffold(bottomBar={NavigationBar{listOf("Home","Prelims","Mains","Profile").forEach{label->NavigationBarItem(selected=page.equals(label,true),onClick={page=label.lowercase()},icon={},label={Text(label)})}}}){p->Box(Modifier.padding(p).fillMaxSize()){when(page){"home"->Home({page="prelims"},{page="mains"});"prelims"->SimpleSection("PRELIMS",listOf("📚 पढ़ाई करें","🧠 Practice","⏱ Mock Test","📰 Current Affairs","🔄 Revision")){page="home"};"mains"->SimpleSection("MAINS",listOf("📚 GS / Essay पढ़ें","✍ Answer Writing","📄 Test / PDF Paper","📰 Mains Current Affairs","🔄 Revision")){page="home"};else->Profile{logged=false}}}}}

@Composable fun LoginScreen(onLogin:()->Unit){Column(Modifier.fillMaxSize().padding(24.dp),verticalArrangement=Arrangement.Center){Text("UPSC Prep",style=MaterialTheme.typography.headlineLarge,fontWeight=FontWeight.Bold);Text("अपनी तैयारी जारी रखें",modifier=Modifier.padding(bottom=20.dp));OutlinedTextField("",{},label={Text("Email / Mobile")},modifier=Modifier.fillMaxWidth());Spacer(Modifier.height(10.dp));OutlinedTextField("",{},label={Text("Password")},modifier=Modifier.fillMaxWidth());Spacer(Modifier.height(14.dp));Button(onClick=onLogin,modifier=Modifier.fillMaxWidth()){Text("LOGIN")};TextButton(onClick={}){Text("नया Account बनाएँ")}}}

@Composable fun Home(pre:()->Unit,mains:()->Unit){Column(Modifier.fillMaxSize().padding(20.dp)){Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.SpaceBetween){Text("UPSC Prep",style=MaterialTheme.typography.titleLarge,fontWeight=FontWeight.Bold);Text("☰")};Spacer(Modifier.height(24.dp));Text("आज की पढ़ाई",fontWeight=FontWeight.Bold);Text("3 Topics बाकी");Button(onClick={},modifier=Modifier.padding(vertical=10.dp)){Text("पढ़ाई शुरू करें")};BigCard("PRELIMS","पढ़ाई • MCQ • Mock Test",pre);BigCard("MAINS","पढ़ाई • Answer • PDF Test",mains);Card(Modifier.fillMaxWidth()){Column(Modifier.padding(18.dp)){Text("जहाँ छोड़ा था वहीं से पढ़ें",fontWeight=FontWeight.Bold);Text("Polity → मौलिक अधिकार")}};Spacer(Modifier.height(12.dp));Text("Revision Due: 2 Topics")}}

@Composable fun BigCard(title:String,sub:String,click:()->Unit){Card(onClick=click,modifier=Modifier.fillMaxWidth().padding(vertical=8.dp),shape=RoundedCornerShape(22.dp)){Column(Modifier.padding(28.dp)){Text(title,style=MaterialTheme.typography.headlineMedium,fontWeight=FontWeight.Bold);Text(sub)}}}

@Composable fun SimpleSection(title:String,items:List<String>,back:()->Unit){Column(Modifier.fillMaxSize().padding(20.dp)){TextButton(onClick=back){Text("← $title",style=MaterialTheme.typography.titleLarge)};items.forEach{Card(onClick={},modifier=Modifier.fillMaxWidth().padding(vertical=7.dp)){Row(Modifier.padding(22.dp).fillMaxWidth(),horizontalArrangement=Arrangement.SpaceBetween){Text(it);Text("›")}}}}}

@Composable fun Profile(logout:()->Unit){Column(Modifier.fillMaxSize().padding(20.dp)){Text("Profile",style=MaterialTheme.typography.headlineMedium,fontWeight=FontWeight.Bold);listOf("🌐 Website खोलें","🔖 Bookmarks","📊 Progress","⚙ Settings").forEach{Text(it,modifier=Modifier.padding(vertical=14.dp))};Button(onClick=logout){Text("Logout")}}}
