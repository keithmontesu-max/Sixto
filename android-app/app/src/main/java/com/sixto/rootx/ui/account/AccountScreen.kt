package com.sixto.rootx.ui.account

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel

@Composable
fun AccountScreen(viewModel: AccountViewModel = hiltViewModel()) {
    val state = viewModel.state.collectAsState().value
    LazyColumn(modifier = Modifier.fillMaxSize().padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item { Text("Account", style = MaterialTheme.typography.headlineMedium) }
        item {
            Card(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(16.dp)) {
                    Text("Profile", style = MaterialTheme.typography.titleMedium)
                    if (state.loading) CircularProgressIndicator()
                    state.email?.let { Text(it) }
                    state.role?.let { Text("Role: $it") }
                    state.error?.let { Text(state.error!!, color = MaterialTheme.colorScheme.error) }
                    Spacer(Modifier.height(8.dp))
                    Button(onClick = { viewModel.refresh() }) { Text("Reload") }
                }
            }
        }
        item {
            Card(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(16.dp)) {
                    Text("Notification preferences", style = MaterialTheme.typography.titleMedium)
                    Text("Promos are off by default. Order/security alerts can be tuned.", style = MaterialTheme.typography.bodySmall)
                    Spacer(Modifier.height(8.dp))
                    PrefToggle("Order updates", state.prefs["ntf_order"] ?: true) { viewModel.toggle("ntf_order", it) }
                    PrefToggle("Payment updates", state.prefs["ntf_payment"] ?: true) { viewModel.toggle("ntf_payment", it) }
                    PrefToggle("Promos", state.prefs["ntf_promo"] ?: false) { viewModel.toggle("ntf_promo", it) }
                    PrefToggle("Security alerts", state.prefs["ntf_security"] ?: true) { viewModel.toggle("ntf_security", it) }
                }
            }
        }
        item {
            Card(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(16.dp)) {
                    Text("Danger zone", style = MaterialTheme.typography.titleMedium)
                    Button(onClick = { viewModel.requestDeletion() }) { Text("Request account deletion") }
                    state.msg?.let { Text(it, style = MaterialTheme.typography.bodySmall) }
                }
            }
        }
    }
}

@Composable
private fun PrefToggle(label: String, value: Boolean, onChange: (Boolean) -> Unit) {
    Row { Checkbox(checked = value, onCheckedChange = onChange); Text(label, modifier = Modifier.padding(top = 12.dp, start = 8.dp)) }
}
