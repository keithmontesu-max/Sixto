package com.sixto.rootx.ui.downloads

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.sixto.rootx.data.remote.SixtoApi
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class DownloadsState(val loading: Boolean = true, val release: Map<String, Any>? = null, val error: String? = null)

@HiltViewModel
class DownloadsViewModel @Inject constructor(private val api: SixtoApi) : ViewModel() {
    private val _state = MutableStateFlow(DownloadsState())
    val state: StateFlow<DownloadsState> = _state
    init {
        viewModelScope.launch {
            try {
                val r = api.activeRelease()
                _state.value = DownloadsState(loading = false, release = r)
            } catch (e: Exception) {
                _state.value = DownloadsState(loading = false, error = e.message ?: "Sign in to check updates")
            }
        }
    }
}
