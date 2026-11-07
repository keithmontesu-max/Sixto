package com.sixto.rootx.ui.theme

import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable

private val DarkScheme = darkColorScheme(
    primary = androidx.compose.ui.graphics.Color(0xFF6EE7B7),
    secondary = androidx.compose.ui.graphics.Color(0xFF94A3B8),
    background = androidx.compose.ui.graphics.Color(0xFF0B0F14),
    surface = androidx.compose.ui.graphics.Color(0xFF111827),
    onPrimary = androidx.compose.ui.graphics.Color(0xFF04120B),
)

@Composable
fun SixtoTheme(content: @Composable () -> Unit) {
    androidx.compose.material3.MaterialTheme(
        colorScheme = DarkScheme,
        content = content
    )
}
