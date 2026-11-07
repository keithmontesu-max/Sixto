# SIXTO TECHTOOL APK (Owner-Only)

**Separate APK. Separate package `com.sixto.techtool`. Never ship to customers.**

## What it is
- WebView wrapper for TECHTOOL web (`:3001`) — Dashboard, Photo Check, Console (OTG), Methods, Security.
- File chooser for Photo Check images, camera for screenshots.
- `usesCleartextTraffic=true` + `network_security_config` allows localhost (`127.0.0.1:8001` console runner) when on rooted host.

## Build
```bash
cd techtool-app
# Android Studio → Sync → Release (R8 on, sign with owner keystore)
./gradlew assembleRelease
# APK: app/build/outputs/apk/release/app-release.apk
```

## Config
- `TECHTOOL_URL` (BuildConfig): debug `http://10.0.2.2:3001`, release `https://techtool.sixto.example.com`.
- `API_BASE_URL` for Retrofit (future native tabs).
- No OWNER credentials in APK. Login via web (MFA). Token lives in WebView `localStorage`.

## Security
- `allowBackup=false`, no secret URLs in APK beyond base URLs.
- Server enforces OWNER role — modified APK still 403 on `/tech/*`.
- Sign release with owner keystore (CI secret), never commit key.
