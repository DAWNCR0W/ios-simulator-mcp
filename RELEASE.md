Release 1.2.2

- Fixed `list_installed_apps` parsing for modern `simctl listapps` output by supporting OpenStep plist payloads.
- Replaced invalid `simctl push/pull` usage with reliable simulator data-path copy for `push_file` and `pull_file`.
- Normalized `file://` paths and group-container values returned by installed app metadata.
- Made `reset_app` resilient when the app is already stopped (`found nothing to terminate`), then proceeds with uninstall.
- Added bounded timeout handling for `handle_permission_alert` to prevent long stalls on complex permission dialogs.
- Capped alert-tree traversal depth for alert/button discovery paths to keep permission handling responsive.
- Added regression tests for listapps parsing, file roundtrip behavior, simulator path validation, and reset idempotency.
- Added additional alert fallback behavior tests for non-standard permission dialog accessibility trees.
