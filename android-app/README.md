# SIXTO ROOT X — Android Customer App (System A)

Kotlin + Jetpack Compose, MVVM/Clean Architecture, Coroutines/Flow, Room, Retrofit/Ktor, Hilt, WorkManager.

## Structure
```
app/src/main/java/com/sixto/rootx/
├── MainActivity.kt          # NavHost: Home, Services, Auto Root, Bootloader, Diagnostics, Orders, Remote, Downloads, Notifications, Account
├── data/
│   ├── remote/Api.kt        # Retrofit API (auth, devices, compatibility, services, orders, sessions)
│   ├── remote/AuthInterceptor.kt  # JWT, 401 refresh
│   ├── local/               # Room: device cache, orders cache
│   └── DeviceDetector.kt    # Build fields, kernel, bootloader, root presence (read-only checks)
├── domain/
│   ├── model/               # DeviceInfo, CompatibilityVerdict, Service, Order
│   └── repository/          # Interfaces
├── ui/
│   ├── home/ services/ autoroot/ bootloader/ diagnostics/
│   ├── orders/ remote/ downloads/ notifications/ account/
│   └── theme/               # Premium dark theme
└── di/                      # Hilt modules
```

## Build config
- `API_BASE_URL` via build variants (dev/staging/prod) — never hardcode prod secrets.
- Release: R8 minify + shrinkResources, debuggable=false, separate debug builds.
- Signing: release keystore in CI secret manager only.

## Screens (all must have loading / error / empty / offline / success states)
Home dashboard (device, root+bootloader status, compatibility result, active orders, session, notifications),
Services catalog (only show compatible services), Auto Root workflow, Bootloader module,
Diagnostics, My Orders (timeline tracking), Remote Support (pairing QR/code), Downloads (signed updates), Notifications, Account (devices, history, payments, security, delete request).

No dead buttons. No fake stats.
