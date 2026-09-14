plugins { id("com.android.application"); id("org.jetbrains.kotlin.android"); id("org.jetbrains.kotlin.plugin.compose") }
android { namespace="com.upscprep.app"; compileSdk=35
 defaultConfig { applicationId="com.upscprep.app"; minSdk=26; targetSdk=35; versionCode=1; versionName="1.0"; buildConfigField("String","API_BASE_URL","\"http://10.0.2.2:8000\"") }
 buildFeatures { compose=true; buildConfig=true }
}
dependencies { implementation(platform("androidx.compose:compose-bom:2025.05.00")); implementation("androidx.activity:activity-compose:1.10.1"); implementation("androidx.compose.material3:material3"); implementation("androidx.compose.ui:ui"); implementation("androidx.compose.ui:ui-tooling-preview"); debugImplementation("androidx.compose.ui:ui-tooling"); implementation("com.squareup.retrofit2:retrofit:2.11.0"); implementation("com.squareup.retrofit2:converter-gson:2.11.0"); implementation("com.squareup.okhttp3:okhttp:4.12.0"); implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.9.0"); implementation("androidx.datastore:datastore-preferences:1.1.7") }
