package com.sixto.rootx.ui

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.hilt.navigation.compose.hiltViewModel
import com.sixto.rootx.ui.autoroot.AutoRootScreen
import com.sixto.rootx.ui.bootloader.BootloaderScreen
import com.sixto.rootx.ui.diagnostics.DiagnosticsScreen
import com.sixto.rootx.ui.account.AccountScreen
import com.sixto.rootx.ui.downloads.DownloadsScreen
import com.sixto.rootx.ui.home.HomeViewModel
import com.sixto.rootx.ui.notifications.NotificationsScreen
import com.sixto.rootx.ui.orders.OrdersScreen
import com.sixto.rootx.ui.remote.RemoteScreen
import com.sixto.rootx.ui.services.ServicesScreen

sealed class Route(val label: String, val icon: String) {
    object Home : Route("Home", "⌂")
    object Services : Route("Services", "⬢")
    object AutoRoot : Route("Auto Root", "⚡")
    object Bootloader : Route("Bootloader", "⬣")
    object Diagnostics : Route("Diagnostics", "◈")
    object Orders : Route("My Orders", "☰")
    object Remote : Route("Remote Support", "⇄")
    object Downloads : Route("Downloads", "↓")
    object Notifications : Route("Notifications", "♡")
    object Account : Route("Account", "◎")
}

private val tabs = listOf(
    Route.Home, Route.Services, Route.AutoRoot, Route.Bootloader, Route.Diagnostics,
    Route.Orders, Route.Remote, Route.Downloads, Route.Notifications, Route.Account
)

@Composable
fun MainScreen() {
    val nav = rememberNavController()
    var selectedTab by remember { mutableStateOf(0) }
    Scaffold(
        bottomBar = {
            NavigationBar {
                tabs.forEachIndexed { i, r ->
                    NavigationBarItem(
                        selected = selectedTab == i,
                        onClick = { selectedTab = i; nav.navigate(r.label) { popUpTo(nav.graph.startDestinationId) } },
                        label = { Text(r.label, style = MaterialTheme.typography.labelSmall) },
                        icon = { Text(r.icon) }
                    )
                }
            }
        }
    ) { padding ->
        NavHost(navController = nav, startDestination = Route.Home.label, modifier = Modifier.padding(padding)) {
            composable(Route.Home.label) { HomeScreen() }
            composable(Route.Services.label) { ServicesScreen() }
            composable(Route.AutoRoot.label) { AutoRootScreen() }
            composable(Route.Bootloader.label) { BootloaderScreen() }
            composable(Route.Diagnostics.label) { DiagnosticsScreen() }
            composable(Route.Orders.label) { OrdersScreen() }
            composable(Route.Remote.label) { RemoteScreen() }
            composable(Route.Downloads.label) { DownloadsScreen() }
            composable(Route.Notifications.label) { NotificationsScreen() }
            composable(Route.Account.label) { AccountScreen() }
        }
    }
}

@Composable
fun HomeScreen(viewModel: HomeViewModel = hiltViewModel()) {
    val state = viewModel.state.collectAsState().value
    LazyColumn(modifier = Modifier.fillMaxSize().padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item {
            Text("SIXTO ROOT X", style = MaterialTheme.typography.headlineMedium)
            Text("Device dashboard", style = MaterialTheme.typography.labelLarge)
        }
        item {
            Card(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(16.dp)) {
                    Text("Detected device", style = MaterialTheme.typography.titleMedium)
                    val info = state.device
                    if (info != null) {
                        Text("${info.manufacturer} ${info.model}")
                        Text("Android ${info.androidVersion} • Kernel: ${info.kernelVersion.take(64)}")
                        Text("Bootloader: ${info.bootloaderStatus}")
                        Text("Root: ${if (info.isRooted) "Detected (${info.rootManager})" else "Not detected"}")
                    } else if (state.loading) {
                        Text("Detecting…")
                    } else {
                        Text(state.error ?: "Detection unavailable")
                    }
                }
            }
        }
        item {
            Card(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(16.dp)) {
                    Text("Compatibility (server-verified)", style = MaterialTheme.typography.titleMedium)
                    if (state.loading) {
                        CircularProgressIndicator()
                    } else {
                        Text("Root: ${state.compatRoot ?: "UNKNOWN"}")
                        Text("Bootloader: ${state.compatBootloader ?: "UNKNOWN"}")
                        state.recommendedManager?.let {
                            Text("Recommended manager: $it")
                        }
                        state.recommendationReason?.let { Text(it) }
                        state.error?.let { Text("Error: $it", color = MaterialTheme.colorScheme.error) }
                    }
                    Spacer(Modifier.height(8.dp))
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        Button(onClick = { viewModel.runFullCheck() }, enabled = !state.loading) {
                            Text("Run compatibility check")
                        }
                        OutlinedButton(onClick = { viewModel.refresh() }) { Text("Refresh") }
                    }
                }
            }
        }
        item {
            Text("Active orders / support session / notifications load from backend once signed in.")
        }
    }
}

@Composable
fun PlaceholderScreen(title: String, body: String) {
    Column(Modifier.fillMaxSize().padding(24.dp)) {
        Text(title, style = MaterialTheme.typography.headlineMedium)
        Spacer(Modifier.height(12.dp))
        Text(body, style = MaterialTheme.typography.bodyMedium)
    }
}
