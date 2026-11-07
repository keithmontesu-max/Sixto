package com.sixto.rootx.data

import android.os.Build
import android.os.SystemProperties
import java.io.File

/**
 * Read-only device detection. Never bypasses FRP/anti-theft/account locks.
 * Root check is presence detection only — it never grants root or executes arbitrary commands.
 */
object DeviceDetector {

    data class Info(
        val manufacturer: String,
        val model: String,
        val modelId: String,
        val hardwareVariant: String,
        val chipset: String,
        val androidVersion: String,
        val kernelVersion: String,
        val buildFingerprint: String,
        val bootloaderStatus: String,
        val isRooted: Boolean,
        val rootManager: String
    )

    fun detect(): Info {
        val kernel = readKernelVersion()
        val bootloader = detectBootloader()
        val (rooted, manager) = detectRoot()
        return Info(
            manufacturer = Build.MANUFACTURER ?: "",
            model = Build.MODEL ?: "",
            modelId = Build.DEVICE ?: "",
            hardwareVariant = Build.HARDWARE ?: "",
            chipset = Build.BOARD ?: "",
            androidVersion = Build.VERSION.RELEASE ?: "",
            kernelVersion = kernel,
            buildFingerprint = Build.FINGERPRINT ?: "",
            bootloaderStatus = bootloader,
            isRooted = rooted,
            rootManager = manager
        )
    }

    private fun readKernelVersion(): String = try {
        File("/proc/version").readText().substringBefore("\n")
    } catch (_: Exception) {
        ""
    }

    private fun detectBootloader(): String {
        val verified = getProp("ro.boot.verifiedbootstate")
        val flashLocked = getProp("ro.boot.flash.locked")
        return when {
            verified == "green" -> "LOCKED"
            verified == "orange" -> "UNLOCKED"
            flashLocked == "1" -> "LOCKED"
            flashLocked == "0" -> "UNLOCKED"
            verified != "" -> verified.uppercase()
            else -> "UNKNOWN"
        }
    }

    private fun getProp(key: String): String = try {
        SystemProperties.get(key, "")
    } catch (_: Exception) {
        ""
    }

    /**
     * Presence detection via well-known manager package paths/APK info.
     * No shell execution, no privilege escalation.
     */
    private fun detectRoot(): Pair<Boolean, String> {
        val magisk = File("/sbin/.magisk").exists() || File("/cache/.magisk").exists()
        val ksu = File("/system/etc/init.d/.ksu").exists() || File("/dev/socket/ksu").exists()
        val apatch = File("/data/adb/ap").exists()
        return when {
            magisk -> true to "Magisk"
            ksu -> true to "KernelSU"
            apatch -> true to "APatch"
            else -> false to ""
        }
    }
}
