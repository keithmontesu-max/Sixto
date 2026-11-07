package com.sixto.rootx.ui.diagnostics

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel

@Composable
fun DiagnosticsScreen(viewModel: DiagnosticsViewModel = hiltViewModel()) {
    val state = viewModel.state.collectAsState().value
    LazyColumn(modifier = Modifier.fillMaxSize().padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item {
            Text("Diagnostics", style = MaterialTheme.typography.headlineMedium)
            Text("Full device report. Available even when root is UNKNOWN.", style = MaterialTheme.typography.bodySmall)
        }
        item {
            Card(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(16.dp)) {
                    Text("Device report", style = MaterialTheme.typography.titleMedium)
                    if (state.loading) CircularProgressIndicator()
                    state.device?.let {
                        Text("${it.manufacturer} ${it.model} (${it.modelId})")
                        Text("Android ${it.androidVersion} • Kernel: ${it.kernelVersion.take(80)}")
                        Text("Fingerprint: ${it.buildFingerprint.take(80)}")
                        Text("Bootloader: ${it.bootloaderStatus}")
                        Text("Root: ${if (it.isRooted) it.rootManager else "Not detected (or not granted)"}")
                    }
                    state.error?.let { Text(state.error!!, color = MaterialTheme.colorScheme.error) }
                    Spacer(Modifier.height(8.dp))
                    Button(onClick = { viewModel.refresh() }) { Text("Re-run diagnostics") }
                }
            }
        }
    }
}
