package com.sixto.rootx.di

import com.sixto.rootx.data.remote.SixtoApi
import com.sixto.rootx.data.remote.SixtoHttpClient
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object AppModule {
    @Provides @Singleton
    fun provideApi(client: SixtoHttpClient): SixtoApi = client.api()
}
