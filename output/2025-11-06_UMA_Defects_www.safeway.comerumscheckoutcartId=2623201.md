## Defect 1

**Title:** A11y_4.1.2 Name, Role, Value – Web/NVDA – Checkout Page – Field labels not announced by NVDA

**Priority:** High

**OS/Browser:** Windows 10 / Chrome 96.0.4664.45

**Screen Reader:** NVDA

**Steps to Reproduce:**
1. Login in to www.safeway.com
2. Navigate to www.safeway.com/erums/checkout?cartId=2623201
3. Click on the Cart button from the home page.
4. Click on the Checkout button to reach the Checkout page.
5. Navigate to the Order Info section and click on Edit.
6. Go to the First name and Last name fields.

**Actual Result:**
NVDA only announces “edit selected <text in field>”. It doesn’t announce the field label or Name.

**Expected Result:**
NVDA should announce the field label and the current value in the field.

**User Impact:**
Screen reader users cannot perceive the purpose of the fields.

**Suggested Fix:**
Ensure name, role, and value are properly exposed.

**WCAG Reference:**
https://www.w3.org/WAI/WCAG22/Understanding/name-role-value.html

## Defect 2

**Title:** A11y_2.4.3 Focus Order – Web/NVDA – Checkout Page – Tab navigation order is incorrect

**Priority:** High

**OS/Browser:** Windows 10 / Chrome 96.0.4664.45

**Screen Reader:** NVDA

**Steps to Reproduce:**
1. Login in to www.safeway.com
2. Navigate to www.safeway.com/erums/checkout?cartId=2623201
3. Go to the “Pay with” section.
4. Click on “confirm CVV”.
5. Tab Navigate forward.

**Actual Result:**
The focus goes to CVV, then jumps to the top SAFEWAY logo link and then we have to go through the page again to reach “Billing ZIP code” field.

**Expected Result:**
The focus should move to the next logical field, which is the “Billing ZIP code” field.

**User Impact:**
Screen reader users may find it difficult to navigate the page in a meaningful order.

**Suggested Fix:**
Ensure that the tab order is logical and predictable.

**WCAG Reference:**
https://www.w3.org/WAI/WCAG22/Understanding/focus-order.html

## Defect 3

**Title:** A11y_1.1.1 Non-text Content – Web/NVDA – Checkout Page – Info button announced as “blank”

**Priority:** Medium

**OS/Browser:** Windows 10 / Chrome 96.0.4664.45

**Screen Reader:** NVDA

**Steps to Reproduce:**
1. Login in to www.safeway.com
2. Navigate to www.safeway.com/erums/checkout?cartId=2623201
3. Under Order Summary, navigate to the Established Taxes and fees info button.

**Actual Result:**
The info button is announced by the NVDA as “blank”.

**Expected Result:**
NVDA should announce the purpose of the info button.

**User Impact:**
Screen reader users cannot perceive the purpose of the info button.

**Suggested Fix:**
Provide a meaningful name for the info button.

**WCAG Reference:**
https://www.w3.org/WAI/WCAG22/Understanding/non-text-content.html