Release 1.2.0

- Added robust `simctl` timeout, retry, and safer command error reporting.
- Added booted-device caching to reduce repeated `simctl list devices booted` overhead.
- Made simulator boot idempotent when the target device is already booted.
- Added screenshot fallback for Xcode 26 (`--type=png`) to improve cross-version reliability.
- Added accessibility trust caching to reduce repeated permission checks.
- Improved element matching accuracy with stronger identifier-first scoring.
- Added strict interaction mode via `IOS_SIM_STRICT_ACTIONS`.
- Optimized wait loops with monotonic timing and adaptive polling.
- Added dedicated optimization tests and benchmark script.
