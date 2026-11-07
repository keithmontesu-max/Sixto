package com.sixto.rootx.ui.orders

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@Composable
fun OrderDetailScreen(
    order: Map<String, Any>?,
    loading: Boolean = false,
    paymentMethods: String? = null,
    onSubmitRef: (String, String) -> Unit,
    submitMsg: String? = null,
    onBack: () -> Unit
) {
    var provider by remember { mutableStateOf("MANUAL") }
    var reference by remember { mutableStateOf("") }

    LazyColumn(modifier = Modifier.fillMaxSize().padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item {
            TextButton(onClick = onBack) { Text("← My Orders") }
            Text("Order Detail", style = MaterialTheme.typography.headlineMedium)
        }
        if (loading) {
            item { CircularProgressIndicator() }
        } else if (order == null) {
            item { Text("Select an order to view its timeline and completion report.") }
        } else {
            item {
                Card(Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(16.dp)) {
                        Text("Order ${order["id"].toString().take(8)}…", style = MaterialTheme.typography.titleMedium)
                        Text("Status: ${order["status"]}")
                        Text("₱${((order["total_cents"] as? Number)?.toInt() ?: 0) / 100.0} ${order["currency"]}", style = MaterialTheme.typography.bodySmall)
                        Spacer(Modifier.height(8.dp))
                        Text("Timeline", style = MaterialTheme.typography.titleMedium)
                        val timeline = (order["timeline"] as? List<*>) ?: emptyList<Any>()
                        if (timeline.isEmpty()) Text("No events yet.", style = MaterialTheme.typography.bodySmall)
                        timeline.forEach { step ->
                            val m = step as? Map<*, *>
                            Text("• ${m?.get("status")} — ${m?.get("note")}", style = MaterialTheme.typography.bodySmall)
                        }
                        val report = order["completion_report"] as? Map<*, *>
                        if (report != null && report.isNotEmpty()) {
                            Text("\nCompletion report:\n${report["report"]}", style = MaterialTheme.typography.bodySmall)
                        }
                    }
                }
            }
            // Direct-payment submit (the usable flow: pay owner → submit ref → owner confirms)
            item {
                Card(Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(16.dp)) {
                        Text("Pay the owner directly", style = MaterialTheme.typography.titleMedium)
                        paymentMethods?.let { Text(it, style = MaterialTheme.typography.bodySmall) }
                            ?: Text("Payment numbers load from backend (owner config).", style = MaterialTheme.typography.bodySmall)
                        Spacer(Modifier.height(8.dp))
                        OutlinedTextField(value = reference, onValueChange = { reference = it },
                            label = { Text("Transaction reference") }, modifier = Modifier.fillMaxWidth(), singleLine = true)
                        Spacer(Modifier.height(8.dp))
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            listOf("MANUAL", "GCASH", "MAYA").forEach { p ->
                                AssistChip(
                                    onClick = { provider = p },
                                    label = { Text(p) },
                                    trailingIcon = if (provider == p) ({ Text("✓") }) else null
                                )
                            }
                        }
                        Spacer(Modifier.height(8.dp))
                        Button(
                            onClick = {
                                if (reference.isNotBlank()) onSubmitRef(provider, reference)
                            },
                            enabled = reference.isNotBlank()
                        ) { Text("Submit payment reference for verification") }
                        submitMsg?.let { Text(submitMsg, style = MaterialTheme.typography.bodySmall) }
                        Text("The owner verifies in his wallet app. Screenshots are never accepted.", style = MaterialTheme.typography.bodySmall)
                    }
                }
            }
        }
    }
}
