package com.sixto.rootx.ui.bootloader

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.sixto.rootx.data.DeviceDetector
import com.sixto.rootx.data.remote.SixtoApi
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class BootloaderState(
    val loading: Boolean = true,
    val status: String? = null,
    val eligibility: String? = null,
    val plan: String? = null,
    val operationId: String? = null,
    val verdict: String? = null,
    val error: String? = null
)

@HiltViewModel
class BootloaderViewModel @Inject constructor(private val api: SixtoApi) : ViewModel() {
    private val _state = MutableStateFlow(BootloaderState())
    val state: StateFlow<BootloaderState> = _state

    init { refresh() }

    fun refresh() {
        viewModelScope.launch {
            _state.value = BootloaderState(loading = true)
            try {
                val info = DeviceDetector.detect()
                _state.value = BootloaderState(
                    loading = false,
                    status = "Bootloader on-device: ${info.bootloaderStatus}",
                    eligibility = "Server verdict loads on plan. Unlock ≠ root; both need separate eligibility."
                )
            } catch (e: Exception) {
                _state.value = BootloaderState(loading = false, error = e.message)
            }
        }
    }

    fun plan(deviceId: String) {
        viewModelScope.launch {
            _state.value = _state.value.copy(loading = true, error = null)
            try {
                val p = api.planOperation(deviceId, "BOOTLOADER_UNLOCK")
                val steps = (p["steps"] as? List<*>)?.joinToString("\n") { s ->
                    val m = s as? Map<*, *>
                    "• ${m?.get("name")} — ${m?.get("description")}"
                }
                _state.value = _state.value.copy(
                    loading = false,
                    plan = steps + "\n\nPrerequisites: " + ((p["prerequisites"] as? List<*>)?.joinToString(", ") ?: ""),
                    operationId = p["id"]?.toString()
                )
            } catch (e: Exception) {
                _state.value = _state.value.copy(loading = false, error = e.message ?: "Plan failed — device may not be unlock-eligible")
            }
        }
    }

    fun authorize(id: String) {
        viewModelScope.launch {
            try {
                api.authorizeOperation(id)
                _state.value = _state.value.copy(verdict = "Authorized. Follow the plan steps on-device; verify below when done.")
            } catch (e: Exception) {
                _state.value = _state.value.copy(error = e.message)
            }
        }
    }

    fun verify(id: String, unlocked: Boolean, wipe: Boolean, auth: Boolean) {
        viewModelScope.launch {
            try {
                val v = api.verifyOperation(id, SixtoApi.BooleanMap(
                    implementation_installed = unlocked,
                    kernel_boot_compatible = false,
                    manager_installed = false,
                    actual_root_available = false,
                    bootloader_unlocked = unlocked,
                    wipe_acknowledged = wipe,
                    authorization_completed = auth
                ))
                _state.value = _state.value.copy(verdict = v["verdict"]?.toString())
            } catch (e: Exception) {
                _state.value = _state.value.copy(error = e.message)
            }
        }
    }
}
