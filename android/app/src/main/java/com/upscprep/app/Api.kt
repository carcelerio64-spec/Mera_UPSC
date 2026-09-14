package com.upscprep.app

import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.Body
import retrofit2.http.Field
import retrofit2.http.FormUrlEncoded
import retrofit2.http.GET
import retrofit2.http.Header
import retrofit2.http.POST
import retrofit2.http.PUT
import retrofit2.http.Path


data class TokenResponse(val access_token:String,val token_type:String)
data class DashboardDto(val name:String,val target_year:Int,val overall_progress:Int,val revision_due:Int,val today_topics:Int,val continue_learning:String)
data class SyllabusSectionDto(val paper:String,val subject:String,val topics:List<String> = emptyList())
data class OptionalSelectionDto(val subject:String? = null)
data class OptionalSaveRequest(val subject:String)

interface UpscApi{
    @FormUrlEncoded
    @POST("auth/token")
    suspend fun login(@Field("username") username:String,@Field("password") password:String):TokenResponse

    @GET("dashboard")
    suspend fun dashboard(@Header("Authorization") auth:String):DashboardDto

    @GET("syllabus/{exam}")
    suspend fun syllabus(@Path("exam") exam:String,@Header("Authorization") auth:String):List<SyllabusSectionDto>

    @GET("optional/subjects")
    suspend fun optionalSubjects(@Header("Authorization") auth:String):List<String>

    @GET("optional/selection")
    suspend fun optionalSelection(@Header("Authorization") auth:String):OptionalSelectionDto

    @PUT("optional/selection")
    suspend fun saveOptional(@Header("Authorization") auth:String,@Body body:OptionalSaveRequest):OptionalSelectionDto
}

object ApiClient{
    val api:UpscApi by lazy{
        Retrofit.Builder()
            .baseUrl(BuildConfig.API_BASE_URL.trimEnd('/') + "/")
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(UpscApi::class.java)
    }
    fun bearer(token:String)="Bearer $token"
}
