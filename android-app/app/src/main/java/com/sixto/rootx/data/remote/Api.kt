package com.sixto.rootx.data.remote

import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Query

interface SixtoApi {
    data class AuthIn(val email: String, val password: String, val full_name: String = "")
    data class LoginIn(val email: String, val password: String, val totp_code: String = "")
    data class TokenOut(val access_token: String, val refresh_token: String, val token_type: String = "bearer")
    data class DeviceIn(
        val manufacturer: String, val model: String, val model_id: String = "",
        val hardware_variant: String = "", val chipset: String = "", val android_version: String = "",
        val kernel_version: String = "", val build_fingerprint: String = "",
        val bootloader_status: String = "UNKNOWN", val is_rooted: Boolean = false,
        val root_manager: String = "", val raw_data: Map<String, Any> = emptyMap()
    )
    data class OrderIn(val service_id: String, val device_id: String, val idempotency_key: String = "")
    data class BooleanMap(
        val implementation_installed: Boolean = false,
        val kernel_boot_compatible: Boolean = false,
        val manager_installed: Boolean = false,
        val actual_root_available: Boolean = false,
        val bootloader_unlocked: Boolean = false,
        val wipe_acknowledged: Boolean = false,
        val authorization_completed: Boolean = false,
        val notes: String = ""
    )

    @POST("auth/register") suspend fun register(@Body body: AuthIn): TokenOut
    @POST("auth/login") suspend fun login(@Body body: LoginIn): TokenOut
    @GET("auth/me") suspend fun me(): Map<String, Any>
    @POST("auth/prefs") suspend fun updatePrefs(@Body body: Map<String, Boolean>): Map<String, Any>
    @POST("auth/deletion-request") suspend fun deletionRequest(): Map<String, Any>

    @POST("devices") suspend fun registerDevice(@Body body: DeviceIn): Map<String, Any>
    @GET("devices/mine") suspend fun myDevices(): List<Map<String, Any>>

    @GET("compatibility/lookup") suspend fun lookup(
        @Query("manufacturer") manufacturer: String,
        @Query("model") model: String,
        @Query("model_id") modelId: String = "",
        @Query("firmware_line") fw: String = ""
    ): Map<String, Any>

    @GET("compatibility/select-manager") suspend fun selectManager(
        @Query("manufacturer") manufacturer: String,
        @Query("model") model: String,
        @Query("model_id") modelId: String = "",
        @Query("kernel_version") kernel: String = "",
        @Query("bootloader_status") bootloader: String = "UNKNOWN",
        @Query("existing_root") existingRoot: String = "",
        @Query("firmware_line") fw: String = ""
    ): Map<String, Any>

    @GET("services") suspend fun services(): List<Map<String, Any>>

    @POST("orders") suspend fun createOrder(@Body body: OrderIn): Map<String, Any>
    @GET("orders/mine") suspend fun myOrders(): List<Map<String, Any>>
    @GET("orders/{id}") suspend fun orderDetail(@retrofit2.http.Path("id") id: String): Map<String, Any>
    @POST("push/register") suspend fun registerPush(@Body body: Map<String, String>): Map<String, Any>

    // M3: allowlisted operations (plan → authorize → verify → report). No remote shell.
    @GET("operations/methods") suspend fun methods(): Map<String, Any>
    @POST("operations/plan") suspend fun planOperation(@Body body: Map<String, Any>): Map<String, Any>
    @POST("operations/{id}/authorize") suspend fun authorizeOperation(@retrofit2.http.Path("id") id: String): Map<String, Any>
    @POST("operations/{id}/verify") suspend fun verifyOperation(
        @retrofit2.http.Path("id") id: String,
        @retrofit2.http.Body body: BooleanMap
    ): Map<String, Any>

    @POST("sessions") suspend fun createSession(@Body body: Map<String, Any>): Map<String, Any>
    @GET("payments/methods") suspend fun paymentMethods(): Map<String, Any>
    @POST("payments/initiate") suspend fun initiatePayment(@Body body: Map<String, Any>): Map<String, Any>
    @GET("admin/releases/active") suspend fun activeRelease(): Map<String, Any>
    @GET("notifications/mine") suspend fun notifications(@Query("unread_only") unread: Boolean): List<Map<String, Any>>
    @POST("notifications/{id}/read") suspend fun markRead(@retrofit2.http.Path("id") id: String): Map<String, Any>

    @GET("health") suspend fun health(): Map<String, Any>
}
