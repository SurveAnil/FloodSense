# FloodSense UI audit

## Initial issue inventory

Recorded before applying UI fixes. Findings below were reproduced against the
local `v2/full-stack` frontend with the replay-mode API.

| ID | Page/component | Reproduction | Expected | Actual | Severity | Root cause | Fix | Verification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| UI-001 | Priority hotspots / location details | Open **Priority hotspots**, select a location with its **Open details** button, then inspect the back action. | The action should describe returning to the priority list; selecting it should return to that list. | The shared detail view said **Back to dashboard**, although its priority-page handler revealed the priority list. | Low | The shared `LocationDetail` label was hard-coded while its callers displayed different parent views. | Make the back label caller-specific: dashboard details say **Back to dashboard** and priority details say **Back to priority list**. | Fixed in code; component test passes. The recorder reached the detail page and saw the correct label, but replay failed, so no browser spec was accepted. |
| UI-002 | Shared desktop sidebar | At a desktop viewport, open the long dashboard and scroll the document down 700px. | Keep primary navigation available while the main content scrolls; let the sidebar scroll independently if needed. | The sidebar was static in document flow and its top moved from y=72 to y=-628, taking all navigation out of view. | Medium | The desktop `.sidebar` had no sticky positioning or viewport-constrained scrolling. | Make the desktop sidebar sticky beneath the sticky header and independently scrollable; enable mobile sidebar scrolling when navigation exceeds available height. | Fixed; at 1440×900 the sidebar remained at y=72 after 700px page scroll; at 320×480 the open admin menu scrolled and its last item was reachable. |
| UI-003 | Dashboard at narrow mobile width | At 320×640, open the dashboard and inspect the top heading/status area. | Keep the heading actions and replay notice readable and reachable without clipping. | The page's internal scroll width exceeded its viewport; the replay snapshot/refresh area and notice layout were clipped or cramped at the right edge. | Medium | The last-updated label was nowrap, and the one-column dashboard grid retained its min-content width. | Allow the timestamp to wrap beside the refresh control at very narrow widths and use a zero-minimum grid track for mobile dashboard panels. | Fixed; at 320px the dashboard, document, and page widths matched the viewport and the refresh control/timestamp remained visible. |
| UI-004 | Sign-in / initial dashboard load | Sign out, then select any demo role while the API is running. | Show a loading state until initial dashboard data is available; show an error only after a failed request. | A transient “Flood-risk information is unavailable” error screen appeared between successful authentication and the dashboard. | Medium | The authenticated view treated `data === undefined` as a completed load failure while the initial dashboard request was still in flight. | Track dashboard loading independently and render a loading message until the first request completes. | Fixed; with a delayed dashboard API response, sign-in displayed the loading state without a false error alert. |
| UI-005 | Citizen and field report counts | Submit one report and inspect the relevant report count. | Use the singular form for exactly one report. | The count read “1 reports.” | Low | Count text did not handle singular/plural forms. | Reuse `formatReportCount` for citizen and field report counts. | Fixed; citizen view displayed “1 report”; Vitest covers zero, one, and multiple reports. |

## Coverage checklist

- [x] Confirm branch and working tree before changes.
- [x] Inventory frontend pages, role-gated views, navigation, and shared shell.
- [x] Exercise admin navigation and inspect distinct page headings/content.
- [x] Check page-width behavior for all admin views at 320, 375, 768, 1024,
  and 1440 CSS pixels; record the dashboard-specific 320px clipping separately.
- [x] Inspect mobile admin navigation at 320×640; all seven navigation actions
  were visible when opened.
- [x] Exercise all three demo roles, submit and track a citizen report, verify it
  as field staff, explicitly approve it as an official problem, and assign,
  update, and review a response task.
- [x] Verify citizen-visible public response status and confirm private field
  notes stay hidden.
- [x] Fix the confirmed issues and add focused frontend regression coverage.
- [x] Attempt the detail-back browser flow; it reached the detail page but the
  recorder replay failed, so use the documented HTTP-probe fallback.
- [x] Complete standalone runtime validation: frontend build, backend tests,
  Vitest, and full-stack home-route HTTP probe all passed.
- [x] Run the final `git diff --check`; the recorded browser replay remained
  unavailable, so the documented HTTP-probe fallback was used.

## Current status and scope

The five issues above have targeted fixes. Standalone validation passed all
four assertions: frontend build, backend tests, three Vitest tests, and the
full-stack home-route HTTP probe. UI-001's label was observed on the detail
page, but the recorder replay did not pass; the HTTP-probe fallback does not
claim browser-level back-navigation coverage. The project still runs in
replay/demo mode; this audit does not establish live data integration, model
accuracy, operational alerting, or production readiness.
