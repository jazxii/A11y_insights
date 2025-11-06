## Defect 1

**Title:** A11y_4.1.2 Name, Role, Value – Web/NVDA – www.safeway.com/games/game-grid – "Opens in new tab" not announced by NVDA for "Official Rules" and "Privacy Policy" links

**Priority:** High

**OS/Browser:** Windows 10 / Chrome 96.0.4664.45

**Screen Reader:** NVDA 2021.2

**Steps to Reproduce:**
1. Login in to www.safeway.com
2. Navigate to www.safeway.com/games/game-grid
3. Click on the "Start Playing" button on one of the games to open a modal dialog box.
4. Navigate to the "Official Rules" and "Privacy Policy" links.

**Actual Result:**
NVDA does not announce "opens in new tab" information for the "Official Rules" and "Privacy Policy" links.

**Expected Result:**
NVDA should announce "opens in new tab" information for the "Official Rules" and "Privacy Policy" links.

**User Impact:**
Screen reader users may not be aware that these links open in a new tab, which can lead to confusion and disorientation.

**Suggested Fix:**
Ensure that the "aria-describedby" attribute is used to provide the "opens in new tab" information for the "Official Rules" and "Privacy Policy" links.

**WCAG Reference:**
https://www.w3.org/WAI/WCAG22/Understanding/name-role-value.html