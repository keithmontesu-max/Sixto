package com.sixto.techtool

import android.annotation.SuppressLint
import android.net.Uri
import android.os.Bundle
import android.webkit.ValueCallback
import android.webkit.WebChromeClient
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.activity.ComponentActivity
import androidx.activity.result.contract.ActivityResultContracts

/**
 * TECHTOOL APK (Owner-Only). Separate package com.sixto.techtool.
 * Never shipped to customers. WebView wrapper for TECHTOOL web (:3001)
 * + localhost console (127.0.0.1:8001) when on rooted host.
 * OWNER token stored in WebView localStorage via login — never in APK.
 */
class MainActivity : ComponentActivity() {

    private var fileCallback: ValueCallback<Array<Uri>>? = null
    private val picker = registerForActivityResult(ActivityResultContracts.GetContent()) { uri: Uri? ->
        fileCallback?.onReceiveValue(if (uri != null) arrayOf(uri) else null)
        fileCallback = null
    }

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val web = WebView(this).apply {
            settings.javaScriptEnabled = true
            settings.domStorageEnabled = true
            settings.allowFileAccess = true
            settings.allowContentAccess = true
            webViewClient = WebViewClient()
            webChromeClient = object : WebChromeClient() {
                override fun onShowFileChooser(
                    view: WebView?,
                    callback: ValueCallback<Array<Uri>>?,
                    params: android.webkit.WebChromeClient.FileChooserParams?
                ): Boolean {
                    fileCallback = callback
                    picker.launch("image/*")
                    return true
                }
            }
        }
        setContentView(web)
        web.loadUrl(BuildConfig.TECHTOOL_URL)
    }
}
