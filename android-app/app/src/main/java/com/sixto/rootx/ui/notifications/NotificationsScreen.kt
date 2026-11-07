package com.sixto.rootx.ui.notifications

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel

@Composable
fun NotificationsScreen(viewModel: NotificationsViewModel = hiltViewModel()) {
    val state = viewModel.state.collectAsState().value
    LazyColumn(modifier = Modifier.fillMaxSize().padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item { Text("Notifications", style = MaterialTheme.typography.headlineMedium) }
        if (state.loading) item { CircularProgressIndicator() }
        state.error?.let { item { Text(state.error!!, color = MaterialTheme.colorScheme.error) } }
        items(state.items.size) { i ->
            val n = state.items[i]
            Card(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(16.dp)) {
                    Text(n["title"].toString(), style = MaterialTheme.typography.titleMedium)
                    Text(n["body"].toString())
                    Text("${n["kind"]} • ${n["created_at"]}", style = MaterialTheme.typography.bodySmall)
                    if (!(n["is_read"] as? Boolean ?: false)) {
                        TextButton(onClick = { viewModel.markRead(n["id"].toString()) }) { Text("Mark read") }
                    }
                }
            }
        }
        if (!state.loading && state.items.isEmpty() && state.error == null) {
            item { Text("All caught up. Order updates and security alerts appear here.") }
        }
    }
}
