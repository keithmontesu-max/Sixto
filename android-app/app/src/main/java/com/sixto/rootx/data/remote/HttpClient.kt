package com.sixto.rootx.data.remote

import com.sixto.rootx.BuildConfig
import com.squareup.okhttp3.OkHttpClient
import com.squareup.okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit
import javax.inject.Inject
import javax.inject.Singleton

class TokenStore @Inject constructor() {
    var accessToken: String? = null
    var refreshToken: String? = null
}

@Singleton
class SixtoHttpClient @Inject constructor(private val tokenStore: TokenStore) {

    private val logging = HttpLoggingInterceptor().apply {
        level = if (BuildConfig.DEBUG) HttpLoggingInterceptor.Level.BODY
        else HttpLoggingInterceptor.Level.BASIC
    }

    val client: OkHttpClient = OkHttpClient.Builder()
        .addInterceptor { chain ->
            val req = chain.request().newBuilder().apply {
                tokenStore.accessToken?.let { addHeader("Authorization", "Bearer $it") }
            }.build()
            chain.proceed(req)
        }
        .addInterceptor(logging)
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .build()

    fun api(): SixtoApi = Retrofit.Builder()
        .baseUrl(BuildConfig.API_BASE_URL)
        .client(client)
        .addConverterFactory(GsonConverterFactory.create())
        .build()
        .create(SixtoApi::class.java)
}
