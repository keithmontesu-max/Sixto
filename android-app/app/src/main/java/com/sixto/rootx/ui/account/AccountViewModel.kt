package com.sixto.rootx.ui.account

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.sixto.rootx.data.remote.SixtoApi
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class AccountState(
    val loading: Boolean = true,
    val email: String? = null,
    val role: String? = null,
    val prefs: Map<String, Boolean> = emptyMap(),
    val msg: String? = null,
    val error: String? = null
)

@HiltViewModel
class AccountViewModel @Inject constructor(private val api: SixtoApi) : ViewModel() {
    private val _state = MutableStateFlow(AccountState())
    val state: StateFlow<AccountState> = _state
    init { refresh() }
    fun refresh() {
        viewModelScope.launch {
            _state.value = AccountState(loading = true)
            try {
                val me = api.me()
                val prefs = (me["prefs"] as? Map<*, *>)?.mapKeys { it.key.toString() }?.mapValues { it.value as? Boolean ?: true } ?: emptyMap()
                _state.value = AccountState(loading = false, email = me["email"]?.toString(), role = me["role"]?.toString(), prefs = prefs)
            } catch (e: Exception) {
                _state.value = AccountState(loading = false, error = e.message ?: "Sign in to view account")
            }
        }
    }
    fun toggle(key: String, value: Boolean) {
        viewModelScope.launch {
            try {
                api.updatePrefs(mapOf(key to value))
                _state.value = _state.value.copy(prefs = _state.value.prefs + (key to value))
            } catch (e: Exception) {
                _state.value = _state.value.copy(error = e.message)
            }
        }
    }
    fun requestDeletion() {
        viewModelScope.launch {
            try {
                api.deletionRequest()
                _state.value = _state.value.copy(msg = "Deletion requested. Admin will review.")
            } catch (e: Exception) {
                _state.value = _state.value.copy(error = e.message)
            }
        }
    }
}
