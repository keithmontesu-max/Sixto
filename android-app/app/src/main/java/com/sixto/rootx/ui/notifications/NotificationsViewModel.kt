package com.sixto.rootx.ui.notifications

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.sixto.rootx.data.remote.SixtoApi
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class NotificationsState(
    val loading: Boolean = true,
    val items: List<Map<String, Any>> = emptyList(),
    val error: String? = null
)

@HiltViewModel
class NotificationsViewModel @Inject constructor(private val api: SixtoApi) : ViewModel() {
    private val _state = MutableStateFlow(NotificationsState())
    val state: StateFlow<NotificationsState> = _state

    init {
        viewModelScope.launch {
            try {
                val list = api.notifications(false)
                _state.value = NotificationsState(loading = false, items = list)
            } catch (e: Exception) {
                _state.value = NotificationsState(loading = false, error = e.message ?: "Sign in to view notifications")
            }
        }
    }

    fun markRead(id: String) {
        viewModelScope.launch {
            try {
                api.markRead(id)
                val list = api.notifications(false)
                _state.value = NotificationsState(loading = false, items = list)
            } catch (e: Exception) {
                _state.value = _state.value.copy(error = e.message)
            }
        }
    }
}
