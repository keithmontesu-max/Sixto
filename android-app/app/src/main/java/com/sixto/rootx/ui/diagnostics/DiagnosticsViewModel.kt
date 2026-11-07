package com.sixto.rootx.ui.diagnostics

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.sixto.rootx.data.DeviceDetector
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class DiagnosticsState(val loading: Boolean = true, val device: DeviceDetector.Info? = null, val error: String? = null)

@HiltViewModel
class DiagnosticsViewModel @Inject constructor() : ViewModel() {
    private val _state = MutableStateFlow(DiagnosticsState())
    val state: StateFlow<DiagnosticsState> = _state
    init { refresh() }
    fun refresh() {
        viewModelScope.launch {
            _state.value = DiagnosticsState(loading = true)
            try {
                val info = DeviceDetector.detect()
                _state.value = DiagnosticsState(loading = false, device = info)
            } catch (e: Exception) {
                _state.value = DiagnosticsState(loading = false, error = e.message)
            }
        }
    }
}
