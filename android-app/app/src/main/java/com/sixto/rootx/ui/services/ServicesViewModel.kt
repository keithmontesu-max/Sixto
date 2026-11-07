package com.sixto.rootx.ui.services

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.sixto.rootx.data.remote.SixtoApi
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class ServicesState(
    val loading: Boolean = true,
    val services: List<Map<String, Any>> = emptyList(),
    val error: String? = null,
    val orderMsg: String? = null,
    val paymentMethods: String? = null
)

@HiltViewModel
class ServicesViewModel @Inject constructor(
    private val api: SixtoApi
) : ViewModel() {

    private val _state = MutableStateFlow(ServicesState())
    val state: StateFlow<ServicesState> = _state

    init {
        viewModelScope.launch {
            try {
                val list = api.services()
                val methods = runCatching { api.paymentMethods() }.getOrNull()
                _state.value = ServicesState(loading = false, services = list, paymentMethods = methods?.toString())
            } catch (e: Exception) {
                _state.value = ServicesState(loading = false, error = e.message ?: "Sign in to view services")
            }
        }
    }

    fun order(serviceId: String, deviceId: String) {
        viewModelScope.launch {
            _state.value = _state.value.copy(loading = true)
            try {
                val o = api.createOrder(SixtoApi.OrderIn(serviceId, deviceId))
                _state.value = _state.value.copy(loading = false,
                    orderMsg = "Order ${o["id"]} created — status ${o["status"]}. Pay the owner directly (see below), then submit your reference in Orders.")
            } catch (e: Exception) {
                _state.value = _state.value.copy(loading = false, error = e.message ?: "Order failed")
            }
        }
    }
}
