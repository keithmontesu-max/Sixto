package com.sixto.rootx.data.remote

import com.sixto.rootx.BuildConfig
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import okhttp3.WebSocket
import okhttp3.WebSocketListener
import java.util.concurrent.TimeUnit
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Live session WebSocket. Token goes as query param (browsers/OkHttp can't set
 * headers on WS reliably). Closed when the composable leaves.
 */
@Singleton
class SessionSocket @Inject constructor(private val tokenStore: TokenStore) {

    private var ws: WebSocket? = null

    fun connect(code: String, onMessage: (String) -> Unit, onError: (String) -> Unit): WebSocket? {
        close()
        val token = tokenStore.accessToken ?: run { onError("Sign in first"); return null }
        val base = BuildConfig.API_BASE_URL.trimEnd('/') // .../api/v1
        val wsBase = base.replaceFirst("http://", "ws://").replaceFirst("https://", "wss://")
        val url = "$wsBase/remote/sessions/ws/${code.uppercase()}?token=$token"
        val client = OkHttpClient.Builder()
            .connectTimeout(15, TimeUnit.SECONDS)
            .readTimeout(0, TimeUnit.SECONDS)
            .build()
        val req = Request.Builder().url(url).build()
        ws = client.newWebSocket(req, object : WebSocketListener() {
            override fun onMessage(webSocket: WebSocket, text: String) { onMessage(text) }
            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                onError(t.message ?: "WebSocket failed")
            }
            override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                if (code != 1000) onError("Session $reason")
            }
        })
        return ws
    }

    fun send(kind: String, body: String): Boolean {
        val socket = ws ?: return false
        val safeBody = body.replace("\"", "\\\"").take(4000)
        return socket.send("{\"kind\":\"$kind\",\"body\":\"$safeBody\"}")
    }

    fun close() {
        ws?.close(1000, "leave")
        ws = null
    }
}
