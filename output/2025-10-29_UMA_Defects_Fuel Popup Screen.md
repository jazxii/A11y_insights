## Defect 1

**Title:** A11y_2.4.3 Focus Order – Android – Fuel Popup Screen – Focus order incorrect when popup appears

**Priority:** High

**OS/Browser:** Android 15 / Ver.2025.23.0 (PROD)

**Screen Reader:** TalkBack

**Steps to Reproduce:**
1. Launch the app and log in.
2. Navigate to the home screen and click on the more button.
3. Click on the Fuel button from the popup window.
4. Observe the focus order when the PICK YOUR PUMP screen and its popup appear.

**Actual Result:**
Once the PICK YOUR PUMP screen's popup is open, the focus goes through the parent page behind first before going into the popup screen.

**Expected Result:**
The focus should directly go to the popup screen when it appears, without going through the parent page behind.

**User Impact:**
This incorrect focus order can confuse screen reader users and make it difficult for them to understand and interact with the popup screen.

**Suggested Fix:**
Ensure that the focus order is logical and predictable. When a popup appears, the focus should move directly to it.

**WCAG Reference:**
https://www.w3.org/WAI/WCAG22/Understanding/focus-order.html

## Defect 2

**Title:** A11y_2.2.2 Pause, Stop, Hide – Android – Fuel Popup Screen – PICK YOUR PUMP screen moving up and down

**Priority:** Medium

**OS/Browser:** Android 15 / Ver.2025.23.0 (PROD)

**Screen Reader:** TalkBack

**Steps to Reproduce:**
1. Launch the app and log in.
2. Navigate to the home screen and click on the more button.
3. Click on the Fuel button from the popup window.
4. Observe the PICK YOUR PUMP screen.

**Actual Result:**
The PICK YOUR PUMP screen appears to be moving up and down.

**Expected Result:**
The PICK YOUR PUMP screen should be static and not move up and down.

**User Impact:**
The moving screen can disorient and confuse users, especially those with cognitive disabilities.

**Suggested Fix:**
Ensure that the PICK YOUR PUMP screen is static and does not move up and down.

**WCAG Reference:**
https://www.w3.org/WAI/WCAG21/Understanding/pause-stop-hide.html