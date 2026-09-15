package com.upscprep.app

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.launch

private val Purple=Color(0xFF5A43D6)
private val DeepPurple=Color(0xFF3322A8)
private val Ink=Color(0xFF27314D)

@Composable
fun AuthScreen(onAuthenticated:(String)->Unit){
    val scope=rememberCoroutineScope()
    var signup by remember{mutableStateOf(false)}
    var name by remember{mutableStateOf("")}
    var email by remember{mutableStateOf("")}
    var password by remember{mutableStateOf("")}
    var showPassword by remember{mutableStateOf(false)}
    var busy by remember{mutableStateOf(false)}
    var error by remember{mutableStateOf("")}
    val bg=Brush.verticalGradient(listOf(Color(0xFFF4F2FF),Color(0xFFF8FAFF),Color(0xFFE8EEFF)))

    Box(Modifier.fillMaxSize().background(bg)){
        Text("“\nDiscipline\nToday,\nA Brighter\nTomorrow",color=Color(0xFF6672A5),fontSize=12.sp,lineHeight=17.sp,modifier=Modifier.align(Alignment.TopStart).padding(start=24.dp,top=22.dp))
        Text("Dream\nPrepare\nAchieve",color=Color(0xFF8177C9),fontSize=18.sp,lineHeight=19.sp,fontStyle=FontStyle.Italic,textAlign=TextAlign.End,modifier=Modifier.align(Alignment.TopEnd).padding(end=24.dp,top=24.dp))

        Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(start=22.dp,end=22.dp,top=105.dp,bottom=24.dp),horizontalAlignment=Alignment.CenterHorizontally){
            Card(modifier=Modifier.fillMaxWidth().widthIn(max=520.dp).shadow(24.dp,RoundedCornerShape(38.dp)),shape=RoundedCornerShape(38.dp),colors=CardDefaults.cardColors(containerColor=Color(0xF7FFFFFF)),elevation=CardDefaults.cardElevation(defaultElevation=12.dp)){
                Column(Modifier.fillMaxWidth().padding(horizontal=24.dp,vertical=28.dp),horizontalAlignment=Alignment.CenterHorizontally){
                    Surface(shape=CircleShape,color=Color(0xFFF0ECFF),shadowElevation=8.dp){Text("◉",fontSize=34.sp,color=Purple,modifier=Modifier.padding(horizontal=15.dp,vertical=8.dp))}
                    Text("UPSC",fontSize=52.sp,fontWeight=FontWeight.ExtraBold,color=DeepPurple,letterSpacing=2.sp,modifier=Modifier.padding(top=6.dp))
                    Surface(modifier=Modifier.width(44.dp).height(3.dp),color=Purple,shape=RoundedCornerShape(3.dp)){}
                    Text(if(signup)"अपना नया account बनाएं" else "अपनी तैयारी जारी रखें",fontSize=18.sp,fontWeight=FontWeight.SemiBold,color=Ink,modifier=Modifier.padding(top=9.dp,bottom=20.dp))

                    if(DemoMode.ENABLED){Surface(shape=RoundedCornerShape(14.dp),color=Color(0xFFF0ECFF),modifier=Modifier.fillMaxWidth().padding(bottom=12.dp)){Text("TEST MODE • Backend deploy होने तक",color=DeepPurple,textAlign=TextAlign.Center,fontWeight=FontWeight.SemiBold,modifier=Modifier.fillMaxWidth().padding(9.dp))}}
                    if(signup){SoftField(name,{name=it},"Name","●");Spacer(Modifier.height(12.dp))}
                    SoftField(email,{email=it},"Email","✉")
                    Spacer(Modifier.height(12.dp))
                    SoftField(password,{password=it},"Password","▣",password=true,visible=showPassword,onVisibility={showPassword=!showPassword})
                    if(!signup) TextButton(onClick={error="Forgot Password backend deploy होने के बाद चालू होगा।"},modifier=Modifier.align(Alignment.End)){Text("Forgot Password?",color=DeepPurple)}
                    if(error.isNotBlank())Text(error,color=MaterialTheme.colorScheme.error,fontSize=12.sp,modifier=Modifier.fillMaxWidth().padding(bottom=8.dp))

                    Button(enabled=!busy&&email.isNotBlank()&&password.isNotBlank()&&(!signup||name.isNotBlank()),onClick={scope.launch{busy=true;error="";try{val token=if(signup)ApiClient.api.signup(SignupRequest(name.trim(),email.trim(),password)).access_token else ApiClient.api.login(email.trim(),password).access_token;onAuthenticated(token)}catch(_:Exception){error=if(signup)"Account नहीं बन पाया। Test Mode से app जाँच सकते हैं।" else "Login नहीं हो पाया। Test Mode से app जाँच सकते हैं।"}finally{busy=false}}},modifier=Modifier.fillMaxWidth().height(58.dp).shadow(12.dp,RoundedCornerShape(28.dp)),shape=RoundedCornerShape(28.dp),colors=ButtonDefaults.buttonColors(containerColor=Purple)){
                        Text(if(busy)"कृपया प्रतीक्षा करें…" else if(signup)"CREATE ACCOUNT  →" else "LOGIN  →",fontSize=18.sp,fontWeight=FontWeight.Bold,letterSpacing=1.sp)
                    }
                    Row(Modifier.fillMaxWidth().padding(vertical=15.dp),verticalAlignment=Alignment.CenterVertically){HorizontalDivider(Modifier.weight(1f));Text("  OR  ",color=Color.Gray);HorizontalDivider(Modifier.weight(1f))}
                    Text(if(signup)"Already have an account?" else "Don’t have an account?",color=Color.DarkGray)
                    OutlinedButton(enabled=!busy,onClick={error="";signup=!signup},shape=RoundedCornerShape(24.dp),modifier=Modifier.padding(top=8.dp).height(48.dp)){Text(if(signup)"Login" else "Create Account",color=Purple,fontWeight=FontWeight.Bold)}
                    if(DemoMode.ENABLED){TextButton(onClick={onAuthenticated(DemoMode.TOKEN)},enabled=!busy,modifier=Modifier.padding(top=4.dp)){Text("ENTER TEST MODE",color=DeepPurple,fontWeight=FontWeight.Bold)}}
                    Text("●  Amit Kumar",fontSize=20.sp,fontStyle=FontStyle.Italic,fontWeight=FontWeight.SemiBold,color=DeepPurple,modifier=Modifier.padding(top=10.dp))
                    Text("A  S T E P  C L O S E R  T O  Y O U R  G O A L",fontSize=9.sp,letterSpacing=1.sp,color=Color(0xFF6975A8),modifier=Modifier.padding(top=5.dp))
                }
            }
            Row(Modifier.fillMaxWidth().padding(top=24.dp),horizontalArrangement=Arrangement.SpaceBetween){Text("CIVIL SERVICES\nA BRIGHTER INDIA",fontSize=10.sp,letterSpacing=1.sp,color=Color(0xFF6975A8));Text("🇮🇳  SERVE\n     LEARN\n     LEAD",fontSize=10.sp,letterSpacing=1.sp,color=Color(0xFF6975A8),textAlign=TextAlign.End)}
        }
    }
}

@Composable
private fun SoftField(value:String,onValue:(String)->Unit,label:String,leading:String,password:Boolean=false,visible:Boolean=false,onVisibility:()->Unit={}){
    Surface(modifier=Modifier.fillMaxWidth().shadow(9.dp,RoundedCornerShape(19.dp)),shape=RoundedCornerShape(19.dp),color=Color(0xFFF9FAFF)){
        OutlinedTextField(value=value,onValueChange=onValue,label={Text(label)},leadingIcon={Text(leading,color=Purple,fontSize=20.sp)},trailingIcon=if(password){{TextButton(onClick=onVisibility){Text(if(visible)"HIDE" else "SHOW",fontSize=10.sp,color=Ink)}}}else null,singleLine=true,visualTransformation=if(password&&!visible)PasswordVisualTransformation() else VisualTransformation.None,modifier=Modifier.fillMaxWidth(),shape=RoundedCornerShape(19.dp),colors=OutlinedTextFieldDefaults.colors(focusedBorderColor=Purple,unfocusedBorderColor=Color.Transparent,focusedContainerColor=Color.Transparent,unfocusedContainerColor=Color.Transparent))
    }
}
