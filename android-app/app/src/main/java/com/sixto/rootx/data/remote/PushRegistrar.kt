package com.sixto.rootx.data.remote

import android.util.Log
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Push token registration. When Firebase is added later, replace `fetchToken`
 * with FirebaseMessaging.getInstance().token. Backend mirrors to FCM when
 * FCM_SERVER_KEY is set; in-app notifications remain source of truth.
 */
@Singleton
class PushRegistrar @Inject constructor(private val api: SixtoApi) {

    /** TODO(FCM): return FirebaseMessaging token once google-services.json is configured.
     * Enable by uncommenting after adding google-services.json + deps:
     *   val t = Tasks.await(FirebaseMessaging.getInstance().token)
     * On failure returns null and in-app notifications still work.
     */
    fun fetchToken(): String? = null

    /** Firebase-ready variant (call from MainActivity when FCM is enabled).
     * Requires: google-services.json in android-app/app/ + google-services gradle plugin.
     * Kept reflection-free so the app builds without Firebase.
     */
    suspend fun registerWithToken(token: String): Boolean {
        return try {
            api.registerPush(mapOf("token" to token, "platform" to "android"))
            true
        } catch (e: Exception) {
            Log.w("PushRegistrar", "register failed: ${e.message}")
            false
        }
    }

    suspend fun registerIfAvailable(): Boolean {
        val token = fetchToken() ?: return false
        return registerWithToken(token)
    }
}
