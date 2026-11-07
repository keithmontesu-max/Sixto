package com.sixto.rootx.ui.autoroot

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.sixto.rootx.data.remote.SixtoApi
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class AutoRootState(
    val loading: Boolean = false,
    val error: String? = null,
    val method: String? = null,
    val status: String? = null,
    val steps: List<Map<String, Any>> = emptyList(),
    val prerequisites: List<String> = emptyList(),
    val recovery: List<String> = emptyList(),
    val verdict: String? = null,
    val operationId: String? = null,
    val authorized: Boolean = false
)

@HiltViewModel
class AutoRootViewModel @Inject constructor(
    private val api: SixtoApi
) : ViewModel() {

    private val _state = MutableStateFlow(AutoRootState(loading = true))
    val state: StateFlow<AutoRootState> = _state

    init {
        // Start by loading once auth is present; if 401 the error surfaces honestly.
        viewModelScope.launch {
            _state.value = AutoRootState(loading = true)
            try {
                val methods = api.methods()
                _state.value = AutoRootState(
                    loading = false,
                    method = "—",
                    prerequisites = (methods["methods"] as? List<*>)?.map { it.toString() } ?: emptyList(),
                    verdict = "Plan with your registered deviceId after sign-in."
                )
            } catch (e: Exception) {
                _state.value = AutoRootState(loading = false, error = e.message ?: "Sign in to view Auto Root")
            }
        }
    }

    fun plan(deviceId: String, method: String = "") {
        viewModelScope.launch {
            _state.value = _state.value.copy(loading = true, error = null)
            try {
                val p = api.planOperation(deviceId, method)
                val steps = (p["steps"] as? List<*>)?.filterIsInstance<Map<*, *>>()
                    ?.map { it.mapKeys { k -> k.key.toString() } } ?: emptyList()
                val prereqs = (p["prerequisites"] as? List<*>)?.map { it.toString() } ?: emptyList()
                val rec = (p["recovery"] as? List<*>)?.map { it.toString() } ?: emptyList()
                _state.value = AutoRootState(
                    loading = false,
                    method = p["method"]?.toString(),
                    status = p["status"]?.toString(),
                    steps = steps,
                    prerequisites = prereqs,
                    recovery = rec,
                    operationId = p["id"]?.toString(),
                    authorized = false,
                    verdict = "Review prerequisites and authorize to continue."
                )
            } catch (e: Exception) {
                _state.value = _state.value.copy(loading = false, error = e.message ?: "Plan failed")
            }
        }
    }

    fun authorize(operationId: String) {
        viewModelScope.launch {
            _state.value = _state.value.copy(loading = true)
            try {
                api.authorizeOperation(operationId)
                _state.value = _state.value.copy(loading = false, authorized = true,
                    verdict = "Authorized. On-device execution may proceed via allowlisted ops. Never blind-retry after timeout.")
            } catch (e: Exception) {
                _state.value = _state.value.copy(loading = false, error = e.message ?: "Authorize failed")
            }
        }
    }

    fun verify(operationId: String, impl: Boolean, kernel: Boolean, manager: Boolean, actual: Boolean) {
        viewModelScope.launch {
            _state.value = _state.value.copy(loading = true)
            try {
                val v = api.verifyOperation(operationId, com.sixto.rootx.data.remote.SixtoApi.BooleanMap(impl, kernel, manager, actual))
                _state.value = _state.value.copy(loading = false,
                    verdict = v["verdict"]?.toString(), status = v["status"]?.toString())
            } catch (e: Exception) {
                _state.value = _state.value.copy(loading = false, error = e.message ?: "Verify failed")
            }
        }
    }
}
