package com.upscprep.app

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.launch

@Composable
fun AuthScreen(onAuthenticated:(String)->Unit){
    val scope=rememberCoroutineScope()
    var signup by remember{mutableStateOf(false)}
    var name by remember{mutableStateOf("")}
    var email by remember{mutableStateOf("")}
    var password by remember{mutableStateOf("")}
    var busy by remember{mutableStateOf(false)}
    var error by remember{mutableStateOf("")}

    val bg=Brush.verticalGradient(listOf(Color(0xFFF8FAFC),Color(0xFFE8EEF5),Color(0xFFF4F7FA)))
    Box(Modifier.fillMaxSize().background(bg).padding(horizontal=24.dp),contentAlignment=Alignment.Center){
        Card(modifier=Modifier.fillMaxWidth().widthIn(max=520.dp),shape=RoundedCornerShape(30.dp),elevation=CardDefaults.cardElevation(defaultElevation=12.dp),colors=CardDefaults.cardColors(containerColor=Color(0xFFFDFEFF))){
            Column(Modifier.fillMaxWidth().padding(horizontal=24.dp,vertical=30.dp),horizontalAlignment=Alignment.CenterHorizontally){
                Surface(shape=RoundedCornerShape(24.dp),shadowElevation=10.dp,color=Color(0xFFE6EDF4)){
                    Text("UPSC",fontSize=42.sp,fontWeight=FontWeight.ExtraBold,color=Color(0xFF1F2937),modifier=Modifier.padding(horizontal=32.dp,vertical=14.dp))
                }
                Text("Amit Kumar",fontSize=17.sp,fontWeight=FontWeight.SemiBold,color=Color(0xFF536273),modifier=Modifier.padding(top=12.dp,bottom=4.dp))
                Text(if(signup)"अपना नया account बनाएं" else "अपनी तैयारी जारी रखें",color=Color(0xFF667585),modifier=Modifier.padding(bottom=22.dp))

                if(DemoMode.ENABLED){
                    Surface(shape=RoundedCornerShape(12.dp),color=Color(0xFFF0ECFF),modifier=Modifier.fillMaxWidth().padding(bottom=12.dp)){
                        Text("TEST MODE • Backend deploy होने तक",color=Color(0xFF5E43A6),fontWeight=FontWeight.SemiBold,modifier=Modifier.padding(10.dp))
                    }
                }
                if(signup){
                    OutlinedTextField(name,{name=it},label={Text("Name")},singleLine=true,modifier=Modifier.fillMaxWidth(),shape=RoundedCornerShape(16.dp))
                    Spacer(Modifier.height(10.dp))
                }
                OutlinedTextField(email,{email=it},label={Text("Email")},singleLine=true,modifier=Modifier.fillMaxWidth(),shape=RoundedCornerShape(16.dp))
                Spacer(Modifier.height(10.dp))
                OutlinedTextField(password,{password=it},label={Text("Password")},singleLine=true,visualTransformation=PasswordVisualTransformation(),modifier=Modifier.fillMaxWidth(),shape=RoundedCornerShape(16.dp))
                if(error.isNotBlank())Text(error,color=MaterialTheme.colorScheme.error,modifier=Modifier.fillMaxWidth().padding(top=8.dp))
                Spacer(Modifier.height(16.dp))
                Button(enabled=!busy&&email.isNotBlank()&&password.isNotBlank()&&(!signup||name.isNotBlank()),onClick={scope.launch{
                    busy=true;error=""
                    try{
                        val token=if(signup) ApiClient.api.signup(SignupRequest(name.trim(),email.trim(),password)).access_token else ApiClient.api.login(email.trim(),password).access_token
                        onAuthenticated(token)
                    }catch(_:Exception){error=if(signup)"Account नहीं बन पाया। Test Mode से app जाँच सकते हैं।" else "Login नहीं हो पाया। Test Mode से app जाँच सकते हैं।"}
                    finally{busy=false}
                }},modifier=Modifier.fillMaxWidth().height(54.dp),shape=RoundedCornerShape(18.dp)){
                    Text(if(busy)"कृपया प्रतीक्षा करें…" else if(signup)"CREATE ACCOUNT" else "LOGIN",fontWeight=FontWeight.Bold)
                }
                if(DemoMode.ENABLED){
                    OutlinedButton(onClick={onAuthenticated(DemoMode.TOKEN)},enabled=!busy,modifier=Modifier.fillMaxWidth().height(52.dp).padding(top=8.dp),shape=RoundedCornerShape(18.dp)){
                        Text("ENTER TEST MODE",fontWeight=FontWeight.Bold)
                    }
                }
                TextButton(enabled=!busy,onClick={error="";signup=!signup}){Text(if(signup)"पहले से account है? Login" else "नया account बनाएं")}
            }
        }
    }
}
