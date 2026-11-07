package com.sixto.rootx.ui.orders

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel

@Composable
fun OrdersScreen(viewModel: OrdersViewModel = hiltViewModel()) {
    val state = viewModel.state.collectAsState().value

    if (state.detail != null || state.detailLoading) {
        OrderDetailScreen(
            order = state.detail,
            loading = state.detailLoading,
            paymentMethods = state.paymentMethods,
            onSubmitRef = { p, r -> viewModel.submitRef(p, r) },
            submitMsg = state.submitMsg,
            onBack = { viewModel.closeDetail() }
        )
        return
    }

    LazyColumn(modifier = Modifier.fillMaxSize().padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item {
            Text("My Orders", style = MaterialTheme.typography.headlineMedium)
            Text("Live order status from the backend. Tap for fresh timeline.", style = MaterialTheme.typography.bodySmall)
        }
        if (state.loading) item { CircularProgressIndicator() }
        state.error?.let { item { Text(state.error!!, color = MaterialTheme.colorScheme.error) } }
        items(state.orders.size) { i ->
            val o = state.orders[i]
            Card(Modifier.fillMaxWidth().clickable { viewModel.openDetail(o["id"].toString()) }) {
                Column(Modifier.padding(16.dp)) {
                    Text("Order ${o["id"].toString().take(8)}…", style = MaterialTheme.typography.titleMedium)
                    Text("Status: ${o["status"]}")
                    Text("₱${((o["total_cents"] as? Number)?.toInt() ?: 0) / 100.0} ${o["currency"]}")
                    Text("Created: ${o["created_at"]} • Tap for timeline", style = MaterialTheme.typography.bodySmall)
                }
            }
        }
        if (!state.loading && state.orders.isEmpty() && state.error == null) {
            item { Text("No orders yet. Browse Services to place one.") }
        }
    }
}
