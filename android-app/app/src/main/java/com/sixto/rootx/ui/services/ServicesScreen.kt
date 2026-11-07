package com.sixto.rootx.ui.services

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel

@Composable
fun ServicesScreen(viewModel: ServicesViewModel = hiltViewModel()) {
    val state = viewModel.state.collectAsState().value
    var deviceId by remember { mutableStateOf("") }

    LazyColumn(modifier = Modifier.fillMaxSize().padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item {
            Text("Services", style = MaterialTheme.typography.headlineMedium)
            Text("Catalog + prices come from the backend. Only compatible services are shown.", style = MaterialTheme.typography.bodySmall)
            Spacer(Modifier.height(8.dp))
            OutlinedTextField(value = deviceId, onValueChange = { deviceId = it },
                label = { Text("Registered device ID") }, modifier = Modifier.fillMaxWidth(), singleLine = true)
        }
        if (state.loading) {
            item { CircularProgressIndicator() }
        }
        state.error?.let { item { Text(state.error!!, color = MaterialTheme.colorScheme.error) } }
        state.orderMsg?.let { item { Text(state.orderMsg!!, color = MaterialTheme.colorScheme.primary) } }
        state.paymentMethods?.let {
            item {
                Card(Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(16.dp)) {
                        Text("Pay the owner directly", style = MaterialTheme.typography.titleMedium)
                        Text(it, style = MaterialTheme.typography.bodySmall)
                    }
                }
            }
        }
        items(state.services.size) { i ->
            val s = state.services[i]
            Card(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(16.dp)) {
                    Text(s["name"].toString(), style = MaterialTheme.typography.titleMedium)
                    Text(s["description"].toString())
                    Text("₱${((s["price_cents"] as? Number)?.toInt() ?: 0) / 100.0} ${s["currency"]} • ETA ${s["eta_minutes"]} min")
                    Text("Refund: ${s["refund_policy"]}", style = MaterialTheme.typography.bodySmall)
                    Spacer(Modifier.height(8.dp))
                    Button(onClick = { if (deviceId.isNotBlank()) viewModel.order(s["id"].toString(), deviceId) }) {
                        Text("Order this service")
                    }
                }
            }
        }
        if (!state.loading && state.services.isEmpty() && state.error == null) {
            item { Text("No active services right now. Check back soon.") }
        }
    }
}
