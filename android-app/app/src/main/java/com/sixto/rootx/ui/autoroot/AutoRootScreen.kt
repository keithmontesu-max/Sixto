package com.sixto.rootx.ui.autoroot

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel

@Composable
fun AutoRootScreen(viewModel: AutoRootViewModel = hiltViewModel()) {
    val state = viewModel.state.collectAsState().value
    var deviceId by remember { mutableStateOf("") }
    var impl by remember { mutableStateOf(false) }
    var kernel by remember { mutableStateOf(false) }
    var manager by remember { mutableStateOf(false) }
    var actual by remember { mutableStateOf(false) }

    LazyColumn(modifier = Modifier.fillMaxSize().padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item {
            Text("Auto Root", style = MaterialTheme.typography.headlineMedium)
            Text("Detect → Validate → Confirm → Execute → Verify. Only approved methods run.", style = MaterialTheme.typography.bodySmall)
        }
        item {
            Card(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(16.dp)) {
                    Text("1. Pick your registered device", style = MaterialTheme.typography.titleMedium)
                    OutlinedTextField(value = deviceId, onValueChange = { deviceId = it },
                        label = { Text("Device ID") }, modifier = Modifier.fillMaxWidth(), singleLine = true)
                    Spacer(Modifier.height(8.dp))
                    Button(onClick = { if (deviceId.isNotBlank()) viewModel.plan(deviceId) }, enabled = !state.loading) {
                        Text("Generate plan")
                    }
                    state.error?.let { Text(state.error!!, color = MaterialTheme.colorScheme.error) }
                    if (state.loading) CircularProgressIndicator(Modifier.padding(top = 8.dp))
                }
            }
        }
        if (state.method != null) {
            item {
                Card(Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(16.dp)) {
                        Text("2. Prerequisites (${state.method})", style = MaterialTheme.typography.titleMedium)
                        state.prerequisites.forEach { Text("• $it") }
                        Text("\nStatus: ${state.status}", style = MaterialTheme.typography.labelLarge)
                        state.operationId?.let {
                            Button(onClick = { viewModel.authorize(it) }, enabled = true) {
                                Text("I understand + authorize this operation")
                            }
                        }
                        state.verdict?.let { Text(it, style = MaterialTheme.typography.bodySmall) }
                    }
                }
            }
            item {
                Card(Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(16.dp)) {
                        Text("3. Steps (allowlisted only)", style = MaterialTheme.typography.titleMedium)
                        state.steps.forEachIndexed { i, s ->
                            Text("${i + 1}. ${s["name"]} — ${s["description"]}")
                            Text("   expected: ${s["expected_result"]} • verify: ${s["verification"]}", style = MaterialTheme.typography.bodySmall)
                        }
                    }
                }
            }
            item {
                Card(Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(16.dp)) {
                        Text("4. Verify (all four required)", style = MaterialTheme.typography.titleMedium)
                        listOf(
                            "Implementation installed" to impl,
                            "Kernel/boot compatible" to kernel,
                            "Manager installed" to manager,
                            "Actual root available" to actual
                        ).forEachIndexed { _, pair ->
                            // Row with checkbox handled below via individual states.
                        }
                        RowRow(impl, { impl = it }, "Implementation installed")
                        RowRow(kernel, { kernel = it }, "Kernel/boot compatible")
                        RowRow(manager, { manager = it }, "Manager installed")
                        RowRow(actual, { actual = it }, "Actual root available")
                        Spacer(Modifier.height(8.dp))
                        state.operationId?.let {
                            Button(onClick = { viewModel.verify(it, impl, kernel, manager, actual) }) {
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
                        state.recovery.forEach { Text("• $it") }
                        Text("Never blind-retry destructive steps after timeout. Check device state first.", style = MaterialTheme.typography.bodySmall)
                    }
                }
            }
        }
    }
}

@Composable
private fun RowRow(checked: Boolean, onChange: (Boolean) -> Unit, label: String) {
    Row {
        Checkbox(checked = checked, onCheckedChange = onChange)
        Text(label, modifier = Modifier.padding(start = 8.dp, top = 12.dp))
    }
}
