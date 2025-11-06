## Defect 1

**Title:** A11y_1.4.3 Contrast (Minimum) – Web/NVDA – www.safeway.com/rewards/dashboard – Continue button on birthday dialog loses contrast on focus

**Priority:** High

**OS/Browser:** Windows 10 / Chrome 96.0.4664.45

**Screen Reader:** NVDA

**Steps to Reproduce:**
1. Login in to www.safeway.com
2. Navigate to www.safeway.com/rewards/dashboard
3. Click on the “Add your birthday to get a special offer” link on the top right corner of the page.
4. Observe the "Continue" button on the dialog that opens.

**Actual Result:**
When focus comes to the "Continue" button, both the text and the background turn white, making the button appear blank.

**Expected Result:**
The "Continue" button should maintain sufficient contrast between text and background even when in focus, to ensure visibility for all users.

**User Impact:**
Low vision users and users with certain cognitive disabilities might struggle to identify the button when it loses contrast, making it difficult for them to complete their task.

**Suggested Fix:**
Ensure that the button maintains a contrast ratio of at least 4.5:1 at all times, including when in focus. This could be achieved by changing the focus state styling to keep the text color as white while changing the background color to a darker shade.

**WCAG Reference:**
https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html