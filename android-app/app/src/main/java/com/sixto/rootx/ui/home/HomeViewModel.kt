package com.sixto.rootx.ui.home

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.sixto.rootx.data.DeviceDetector
import com.sixto.rootx.data.remote.SixtoApi
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class HomeState(
    val loading: Boolean = false,
    val error: String? = null,
    val device: DeviceDetector.Info? = null,
    val compatRoot: String? = null,
    val compatBootloader: String? = null,
    val recommendedManager: String? = null,
    val recommendationReason: String? = null
)

@HiltViewModel
class HomeViewModel @Inject constructor(
    private val api: SixtoApi
) : ViewModel() {

    private val _state = MutableStateFlow(HomeState(loading = true))
    val state: StateFlow<HomeState> = _state

    init { refresh() }

    fun refresh() {
        viewModelScope.launch {
            _state.value = HomeState(loading = true)
            try {
                val info = DeviceDetector.detect()
                // Recommended flow: lookup classification first, then manager selection.
                // Both require auth; if 401 the backend returns it and we surface the error.
                // Device registration to get a device id for orders is a separate step.
                val lookup = runCatching {
                    api.lookup(info.manufacturer, info.model, info.modelId)
                }.getOrNull()
                val rootCls = (lookup?.get("root") as? Map<*, *>)?.get("classification")?.toString()
                val bootCls = (lookup?.get("bootloader") as? Map<*, *>)?.get("classification")?.toString()

                _state.value = HomeState(
                    loading = false,
                    device = info,
                    compatRoot = rootCls,
                    compatBootloader = bootCls,
                    recommendedManager = null,
                    recommendationReason = "Sign in, then tap Run compatibility check to load the full verdict."
                )
            } catch (e: Exception) {
                _state.value = HomeState(loading = false, error = e.message ?: "Failed to load device info")
            }
        }
    }

    fun runFullCheck(onDone: (String) -> Unit = {}) {
        viewModelScope.launch {
            val info = _state.value.device ?: run { refresh(); return@launch }
            _state.value = _state.value.copy(loading = true, error = null)
            try {
                val sel = api.selectManager(
                    info.manufacturer, info.model, info.modelId,
                    info.kernelVersion, info.bootloaderStatus, info.rootManager
                )
                _state.value = _state.value.copy(
                    loading = false,
                    recommendedManager = sel["recommended"]?.toString(),
                    recommendationReason = sel["reason"]?.toString()
                )
                onDone(sel["reason"]?.toString() ?: "")
            } catch (e: Exception) {
                _state.value = _state.value.copy(loading = false, error = e.message ?: "Check failed")
            }
        }
    }
}
