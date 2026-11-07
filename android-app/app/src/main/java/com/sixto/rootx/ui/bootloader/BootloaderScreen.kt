package com.sixto.rootx.ui.bootloader

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel

@Composable
fun BootloaderScreen(viewModel: BootloaderViewModel = hiltViewModel()) {
    val state = viewModel.state.collectAsState().value
    var deviceId by remember { mutableStateOf("") }
    var unlocked by remember { mutableStateOf(false) }
    var wipe by remember { mutableStateOf(false) }
    var authDone by remember { mutableStateOf(false) }

    LazyColumn(modifier = Modifier.fillMaxSize().padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item {
            Text("Bootloader Unlock", style = MaterialTheme.typography.headlineMedium)
            Text("Legitimate unlock with your consent. Never FRP/account-lock bypass. Unlocking wipes data.", style = MaterialTheme.typography.bodySmall)
        }
        item {
            Card(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(16.dp)) {
                    Text("Detected status", style = MaterialTheme.typography.titleMedium)
                    if (state.loading) CircularProgressIndicator()
                    state.status?.let { Text(it) }
                    state.eligibility?.let { Text(it) }
                    state.error?.let { Text(state.error!!, color = MaterialTheme.colorScheme.error) }
                    Spacer(Modifier.height(8.dp))
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        Button(onClick = { viewModel.refresh() }) { Text("Re-detect") }
                        OutlinedTextField(value = deviceId, onValueChange = { deviceId = it },
                            label = { Text("Device ID") }, singleLine = true)
                    }
                }
            }
        }
        item {
            Card(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(16.dp)) {
                    Text("1. Plan unlock (device must be eligible)", style = MaterialTheme.typography.titleMedium)
                    Button(onClick = { if (deviceId.isNotBlank()) viewModel.plan(deviceId) }, enabled = deviceId.isNotBlank()) {
                        Text("Generate unlock plan")
                    }
                    state.plan?.let {
                        Text(it, style = MaterialTheme.typography.bodySmall)
                    }
                    state.operationId?.let {
                        Button(onClick = { viewModel.authorize(it) }, modifier = Modifier.padding(top = 8.dp)) {
                            Text("I understand (wipe) — authorize unlock")
                        }
                    }
                }
            }
        }
        if (state.operationId != null) {
            item {
                Card(Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(16.dp)) {
                        Text("2. Verify unlock (all 3 required)", style = MaterialTheme.typography.titleMedium)
                        CheckRow("Bootloader unlocked", unlocked) { unlocked = it }
                        CheckRow("Data wipe acknowledged", wipe) { wipe = it }
                        CheckRow("Manufacturer auth done", authDone) { authDone = it }
                        state.operationId?.let {
                            Button(onClick = { viewModel.verify(it, unlocked, wipe, authDone) }) {
                                Text("Submit verification")
                            }
                        }
                        state.verdict?.let { Text(state.verdict!!) }
                    }
                }
            }
            item {
                Card(Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(16.dp)) {
                        Text("Recovery", style = MaterialTheme.typography.titleMedium)
                        Text("• Reinstall USB drivers, original cable\n• Xiaomi: complete Mi Unlock token wait — cannot be skipped\n• Never flash different-build boot image", style = MaterialTheme.typography.bodySmall)
                    }
                }
            }
        }
    }
}

@Composable
private fun CheckRow(label: String, value: Boolean, onChange: (Boolean) -> Unit) {
    Row { Checkbox(checked = value, onCheckedChange = onChange); Text(label, modifier = Modifier.padding(start = 8.dp, top = 12.dp)) }
}
