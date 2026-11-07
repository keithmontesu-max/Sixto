package com.sixto.rootx

import android.app.Application
import dagger.hilt.android.HiltAndroidApp

@HiltAndroidApp
class SixtoApplication : Application() {
    // No master secrets stored here. All secrets stay server-side.
}
