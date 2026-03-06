Release 1.3.0

- Removed coordinate-based interaction tools from the MCP surface to keep automation element-driven and avoid host mouse or focus dependencies.
- Added `find_elements(query, max_results)` to return ranked accessibility matches without traversing the full UI tree client-side.
- Added `get_element_actions(identifier)` so clients can inspect supported accessibility actions before interacting with an element.
- Added `wait_for_any_element(identifiers, timeout)` to proceed as soon as the first matching element appears.
- Added `double_tap(identifier, interval)` with bounded AXPress execution to prevent hangs when accessibility stalls.
- Added `app_info(bundle_id, device_id)` to expose normalized `simctl appinfo` metadata for installed simulator apps.
- Expanded datasource, use case, and MCP integration coverage for the new tools and release surface.
