package com.upscprep.app

import okhttp3.MultipartBody
import okhttp3.RequestBody
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.Body
import retrofit2.http.Field
import retrofit2.http.FormUrlEncoded
import retrofit2.http.GET
import retrofit2.http.Header
import retrofit2.http.Multipart
import retrofit2.http.POST
import retrofit2.http.PUT
import retrofit2.http.Part
import retrofit2.http.Path
import retrofit2.http.Query

data class TokenResponse(val access_token:String,val token_type:String)
data class DashboardDto(val name:String,val target_year:Int,val overall_progress:Int,val revision_due:Int,val today_topics:Int,val continue_learning:String)
data class SyllabusSectionDto(val paper:String,val subject:String,val topics:List<String> = emptyList())
data class OptionalSelectionDto(val subject:String? = null)
data class OptionalSaveRequest(val subject:String)
data class OptionalPaperDto(val paper:String,val topics:List<String> = emptyList(),val fully_verified:Boolean = false)
data class OptionalSyllabusDto(val subject:String,val source_url:String? = null,val pyq_source_url:String? = null,val complete:Boolean = false,val papers:List<OptionalPaperDto> = emptyList())
data class PyqPaperDto(val title:String,val url:String,val kind:String? = null)
data class PyqResponseDto(val source:String,val exam:String,val year:Int,val source_page:String,val papers:List<PyqPaperDto> = emptyList(),val note:String? = null)
data class CurrentAffairDto(val id:Int,val source_name:String,val source_url:String,val title:String,val summary:String? = null,val subject:String,val prelims_relevance:String? = null,val mains_relevance:String? = null,val published_at:String? = null,val fetched_at:String? = null)
data class WrongQuestionDto(val id:Int,val exam:String,val paper:String,val subject:String,val topic:String,val question:String,val difficulty:String,val options:List<String> = emptyList(),val last_answer:String? = null,val attempted_at:String? = null)
data class ClassNoteDto(val id:Int,val exam:String,val paper:String,val subject:String,val topic:String,val subtopic:String,val title:String,val file_type:String,val file_url:String,val uploaded_at:String)
data class UploadNoteResponse(val ok:Boolean,val id:Int,val file_type:String,val file_url:String)
data class TopicStudyDto(val exam:String,val paper:String,val subject:String,val topic:String,val official_syllabus_match:Boolean = false,val class_notes:List<ClassNoteDto> = emptyList(),val question_bank_count:Int = 0,val current_affairs:List<Map<String,Any?>> = emptyList())

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

    @GET("optional/syllabus/{subject}")
    suspend fun optionalSyllabus(@Path("subject") subject:String,@Header("Authorization") auth:String):OptionalSyllabusDto

    @GET("pyq")
    suspend fun pyq(@Header("Authorization") auth:String,@Query("exam") exam:String,@Query("year") year:Int,@Query("subject") subject:String? = null):PyqResponseDto

    @GET("current-affairs/date-wise")
    suspend fun currentAffairs(@Header("Authorization") auth:String,@Query("date") date:String,@Query("subject") subject:String? = null,@Query("limit") limit:Int = 100):List<CurrentAffairDto>

    @GET("wrong-questions")
    suspend fun wrongQuestions(@Header("Authorization") auth:String,@Query("limit") limit:Int = 200):List<WrongQuestionDto>

    @GET("class-notes")
    suspend fun classNotes(@Header("Authorization") auth:String,@Query("subject") subject:String? = null,@Query("topic") topic:String? = null):List<ClassNoteDto>

    @Multipart
    @POST("uploads/class-note")
    suspend fun uploadClassNote(
        @Header("Authorization") auth:String,
        @Part file:MultipartBody.Part,
        @Part("exam") exam:RequestBody,
        @Part("subject") subject:RequestBody,
        @Part("topic") topic:RequestBody,
        @Part("title") title:RequestBody,
        @Part("paper") paper:RequestBody,
        @Part("subtopic") subtopic:RequestBody,
    ):UploadNoteResponse

    @GET("study/topic")
    suspend fun topicStudy(
        @Header("Authorization") auth:String,
        @Query("exam") exam:String,
        @Query("paper") paper:String,
        @Query("subject") subject:String,
        @Query("topic") topic:String,
    ):TopicStudyDto
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
