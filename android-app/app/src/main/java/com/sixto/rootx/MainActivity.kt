package com.sixto.rootx

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier
import dagger.hilt.android.AndroidEntryPoint
import com.sixto.rootx.ui.MainScreen
import com.sixto.rootx.ui.theme.SixtoTheme

@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    @javax.inject.Inject lateinit var push: com.sixto.rootx.data.remote.PushRegistrar
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        // Best-effort: registers FCM token when available; no-op until Firebase is configured.
        androidx.lifecycle.lifecycleScope.launch {
            runCatching { push.registerIfAvailable() }
        }
        setContent {
            SixtoTheme {
                Surface(modifier = Modifier.fillMaxSize()) {
                    MainScreen()
                }
            }
        }
    }
}
