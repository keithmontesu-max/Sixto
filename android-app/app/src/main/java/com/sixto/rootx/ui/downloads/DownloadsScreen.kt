package com.sixto.rootx.ui.downloads

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel

@Composable
fun DownloadsScreen(viewModel: DownloadsViewModel = hiltViewModel()) {
    val state = viewModel.state.collectAsState().value
    LazyColumn(modifier = Modifier.fillMaxSize().padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item {
            Text("Downloads", style = MaterialTheme.typography.headlineMedium)
            Text("Signed updates only. Integrity verified before install.", style = MaterialTheme.typography.bodySmall)
        }
        item {
            Card(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(16.dp)) {
                    Text("Active release", style = MaterialTheme.typography.titleMedium)
                    if (state.loading) CircularProgressIndicator()
                    state.release?.let {
                        Text("Version: ${it["version"]}")
                        Text("Notes: ${it["notes"]}")
                        Text("Signature: ${it["signature_hash"]}")
                        Text("Rollout: ${it["rollout_percent"]}%")
                    }
                    state.error?.let { Text(state.error!!, color = MaterialTheme.colorScheme.error) }
                }
            }
        }
        item {
            Text("Compatibility data auto-updates from the server. Native changes need a signed app release.", style = MaterialTheme.typography.bodySmall)
        }
    }
}
