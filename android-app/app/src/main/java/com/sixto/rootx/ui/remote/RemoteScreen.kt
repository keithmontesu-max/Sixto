package com.sixto.rootx.ui.remote

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel

@Composable
fun RemoteScreen(viewModel: RemoteViewModel = hiltViewModel()) {
    val state = viewModel.state.collectAsState().value
    var code by remember { mutableStateOf("") }
    var msg by remember { mutableStateOf("") }

    DisposableEffect(Unit) {
        onDispose { viewModel.disconnect() }
    }

    LazyColumn(modifier = Modifier.fillMaxSize().padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item {
            Text("Remote Support", style = MaterialTheme.typography.headlineMedium)
            Text("Secure pairing via code. Cloud does NOT grant device control — on-device ops need your explicit authorization.", style = MaterialTheme.typography.bodySmall)
        }
        item {
            Card(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(16.dp)) {
                    Text("Start a session", style = MaterialTheme.typography.titleMedium)
                    Button(onClick = { viewModel.startSession() }, enabled = !state.loading) { Text("Create pairing code") }
                    state.code?.let {
                        Text("Your code: $it (valid 20 min)", style = MaterialTheme.typography.headlineSmall)
                        Spacer(Modifier.height(8.dp))
                        Button(onClick = { viewModel.connectLive(it) }) { Text("Connect live chat") }
                        if (state.live) Text("Live — messages stream here in real time.")
                    }
                    state.error?.let { Text(state.error!!, color = MaterialTheme.colorScheme.error) }
                }
            }
        }
        item {
            Card(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(16.dp)) {
                    Text("Live messages", style = MaterialTheme.typography.titleMedium)
                    if (state.messages.isEmpty()) Text("No messages yet. Start a session and connect.", style = MaterialTheme.typography.bodySmall)
                    state.messages.forEach { m ->
                        Text("• ${m["kind"]}: ${m["body"]}", style = MaterialTheme.typography.bodySmall)
                    }
                    Spacer(Modifier.height(8.dp))
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        OutlinedTextField(value = msg, onValueChange = { msg = it }, label = { Text("Message") }, modifier = Modifier.weight(1f))
                        Button(onClick = { if (msg.isNotBlank()) viewModel.sendLive(msg); msg = "" }) { Text("Send") }
                    }
                }
            }
        }
        item {
            Text("Expired sessions cannot be reused. REST history is available via GET /remote/sessions/{id}/messages.", style = MaterialTheme.typography.bodySmall)
        }
    }
}
