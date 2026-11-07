package com.sixto.rootx.ui.orders

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.sixto.rootx.data.remote.SixtoApi
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class OrdersState(
    val loading: Boolean = true,
    val orders: List<Map<String, Any>> = emptyList(),
    val error: String? = null,
    val detail: Map<String, Any>? = null,
    val detailLoading: Boolean = false,
    val paymentMethods: String? = null,
    val submitMsg: String? = null
)

@HiltViewModel
class OrdersViewModel @Inject constructor(private val api: SixtoApi) : ViewModel() {
    private val _state = MutableStateFlow(OrdersState())
    val state: StateFlow<OrdersState> = _state

    init {
        viewModelScope.launch {
            try {
                val list = api.myOrders()
                _state.value = OrdersState(loading = false, orders = list)
            } catch (e: Exception) {
                _state.value = OrdersState(loading = false, error = e.message ?: "Sign in to view orders")
            }
        }
        viewModelScope.launch {
            runCatching { api.paymentMethods() }.onSuccess { m ->
                _state.value = _state.value.copy(paymentMethods = m.toString())
            }
        }
    }

    fun openDetail(id: String) {
        viewModelScope.launch {
            _state.value = _state.value.copy(detailLoading = true)
            try {
                val d = api.orderDetail(id)
                _state.value = _state.value.copy(detailLoading = false, detail = d)
            } catch (e: Exception) {
                _state.value = _state.value.copy(detailLoading = false, error = e.message ?: "Failed to load order")
            }
        }
    }

    fun closeDetail() {
        _state.value = _state.value.copy(detail = null)
    }

    fun submitRef(provider: String, reference: String) {
        val id = _state.value.detail?.get("id")?.toString() ?: return
        viewModelScope.launch {
            _state.value = _state.value.copy(submitMsg = null)
            try {
                val r = api.initiatePayment(mapOf("order_id" to id, "provider" to provider, "provider_ref" to reference))
                _state.value = _state.value.copy(
                    submitMsg = "Submitted (${r["status"]}). The owner will verify your ${provider} transfer.",
                    detailLoading = false
                )
            } catch (e: Exception) {
                _state.value = _state.value.copy(submitMsg = "Failed: ${e.message}")
            }
        }
    }
}
