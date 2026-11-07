package com.sixto.rootx.ui.remote

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.sixto.rootx.data.remote.SessionSocket
import com.sixto.rootx.data.remote.SixtoApi
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject
import org.json.JSONObject

data class RemoteState(
    val loading: Boolean = false,
    val code: String? = null,
    val error: String? = null,
    val messages: List<Map<String, Any>> = emptyList(),
    val live: Boolean = false
)

@HiltViewModel
class RemoteViewModel @Inject constructor(
    private val api: SixtoApi,
    private val socket: SessionSocket
) : ViewModel() {
    private val _state = MutableStateFlow(RemoteState())
    val state: StateFlow<RemoteState> = _state

    fun startSession() {
        viewModelScope.launch {
            _state.value = _state.value.copy(loading = true)
            try {
                val s = api.createSession(mapOf<String, Any>())
                _state.value = _state.value.copy(loading = false, code = s["code"]?.toString())
            } catch (e: Exception) {
                _state.value = _state.value.copy(loading = false, error = e.message ?: "Failed — sign in first")
            }
        }
    }

    fun connectLive(code: String) {
        socket.connect(
            code = code,
            onMessage = { text ->
                try {
                    val json = JSONObject(text)
                    val entry = mapOf<String, Any>(
                        "kind" to json.optString("kind", "text"),
                        "body" to json.optString("body", "")
                    )
                    _state.value = _state.value.copy(
                        live = true,
                        messages = _state.value.messages + entry
                    )
                } catch (_: Exception) {
                    _state.value = _state.value.copy(error = "Bad message frame")
                }
            },
            onError = { err ->
                _state.value = _state.value.copy(error = err, live = false)
            }
        )
        _state.value = _state.value.copy(live = true)
    }

    fun sendLive(text: String) {
        val ok = socket.send("text", text)
        if (!ok) {
            _state.value = _state.value.copy(error = "Not connected — tap Connect live chat first")
        } else {
            _state.value = _state.value.copy(
                messages = _state.value.messages + mapOf("kind" to "text", "body" to text)
            )
        }
    }

    fun disconnect() = socket.close()
}
