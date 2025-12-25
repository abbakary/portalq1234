# Started Order Detail Data Saving Fix - Summary

## Problem Identified
The "Edit Order Details" modal in the `started_order_detail` page was not saving order data when users edited order details (order type, labour codes, services, items, estimated duration, etc.).

### Root Cause
The form was posting to the wrong endpoint with mismatched field names:
1. **Wrong Endpoint**: Form was POSTing to `/orders/<id>/edit/` (order_edit view using OrderForm)
2. **Field Mismatch**: The modal was submitting fields that OrderForm doesn't handle:
   - `order_type` (vs form's "type")
   - `labour_code_id` (not in form)
   - `item_id` (not in form)
   - `labour_codes` (not in form)
   - `services` (needs special mapping)
   - `estimated_duration` (not in form's Meta fields)

### Solution Implemented
Redirected the form submission to the correct endpoint with comprehensive handling:

## Changes Made

### 1. **Template Changes** (`tracker/templates/tracker/started_order_detail.html`)
- **Line 242**: Changed form action from `{% url 'tracker:order_edit' order.id %}` to `{% url 'tracker:started_order_detail' order.id %}`
- **Line 244**: Added hidden action parameter: `<input type="hidden" name="action" value="update_order_details">`
- **Lines 1265-1288**: Enhanced fetch error handling to properly follow redirects

### 2. **Form Updates** (`tracker/forms.py`)
- **Lines 482-517**: Added `estimated_duration` field to OrderForm.Meta.fields and widgets
- This allows the field to be properly handled when the form is used in other contexts

### 3. **Backend Improvements** (`tracker/views_start_order.py`)
- **Lines 459-461**: Enhanced logging at the start of update_order_details action to track input parameters
- **Lines 563-570**: Added proper error handling with:
  - Detailed error logging with stack trace
  - User-friendly error message via messages framework
  - Redirect back to the order detail page on error (instead of falling through)

## How It Works Now

1. **Form Submission Flow**:
   - User fills the "Edit Order Details" modal
   - Clicks "Save Changes"
   - Form submits via fetch to `/orders/started/<order_id>/`
   - Backend receives `action=update_order_details` parameter

2. **Backend Processing** (`started_order_detail` view):
   - Validates `action == 'update_order_details'`
   - Extracts all form fields:
     - Order type (service, sales, labour, inquiry)
     - Item selection (labour code, inventory, or manual entry)
     - Services/Labour codes (multiple selections)
     - Estimated duration
   - Updates Order model with priority logic:
     1. Labour code selection (if provided)
     2. Manual item entry (if no labour code)
     3. Inventory item (if no manual entry)
   - Updates description with services/labour codes
   - Saves the order to database
   - Redirects to dashboard on success (or back to order detail on error)

3. **Data Handled**:
   - ✅ Order type changes (service → sales, etc.)
   - ✅ Labour code selection (single or multiple)
   - ✅ Service/add-on selection (multiple)
   - ✅ Inventory item selection with quantity
   - ✅ Manual item entry with brand and quantity
   - ✅ Estimated duration calculation
   - ✅ Description building with proper formatting

## Testing Checklist

- [ ] Test updating order type from service to sales
- [ ] Test updating order type from sales to service
- [ ] Test selecting labour code for sales/service order
- [ ] Test selecting inventory item for sales order
- [ ] Test manual item entry for sales order
- [ ] Test selecting multiple labour codes for labour order
- [ ] Test selecting multiple services for service order
- [ ] Test estimated duration update
- [ ] Verify data persists after page reload
- [ ] Test error handling (invalid labour code, missing required fields)
- [ ] Check logs for proper error tracking

## Files Modified
1. `tracker/templates/tracker/started_order_detail.html` (2 changes)
2. `tracker/forms.py` (1 change)
3. `tracker/views_start_order.py` (2 changes)

## Backward Compatibility
- Changes are backward compatible
- OrderForm still works with the `estimated_duration` field addition
- The form submission to `started_order_detail` is separate from `order_edit` usage
