# Labour Code Integration for Order Item Updates

## Overview
This implementation enables the use of labour code table data for item information (name, brand, quantity, tire type) when updating order details for both **service** and **sales** order types. Users can now:

1. **Lookup labour codes** by item name or code
2. **Auto-fill item data** from the labour code table
3. **Fall back to manual entry** when labour code data is not available
4. **Use inventory items** as before for backward compatibility

---

## Changes Made

### 1. **Extended LabourCode Model** (`tracker/models.py`)
Added new fields to store item-related information:
- `item_name` (CharField, optional): Item name for sales/labour orders
- `brand` (CharField, optional): Brand name for items
- `quantity` (PositiveIntegerField, optional): Default quantity for items
- `tire_type` (CharField, optional): Type of tire (e.g., New, Used, Radial)

**New Methods:**
- `get_item_details()`: Returns labour code item details as a dictionary
- `lookup_by_name(item_name, category=None)`: Lookup labour code by item name
- `lookup_by_code(code)`: Lookup labour code by code value
- `search_by_description(search_term, category=None)`: Search labour codes by description

### 2. **Updated Admin Interface** (`tracker/admin.py`)
- Extended `LabourCodeAdmin` list display to show `item_name` and `brand`
- Added a new fieldset "Item Details" for managing item-related fields
- Updated search fields to include `item_name` and `brand`

### 3. **Updated Forms** (`tracker/forms.py`)
- Enhanced `LabourCodeForm` to include the new item fields with proper widgets
- Updated `OrderForm.clean()` method to support labour code lookup when processing sales orders
- Priority order: Labour Code → Inventory Item → Manual Entry

### 4. **New API Endpoint** (`tracker/views_start_order.py`)
Added `api_lookup_labour_code()` endpoint:
- **URL**: `/tracker/api/orders/lookup-labour-code/`
- **Method**: GET
- **Query Parameters**:
  - `item_name`: Search by item name (iexact match)
  - `code`: Search by labour code (iexact match)
  - `category`: Optional category filter (labour, service, tyre service, sales, unspecified)
- **Returns**: List of matching labour codes with full item details

### 5. **Enhanced Started Order Detail View** (`tracker/views_start_order.py`)
Updated `started_order_detail` view's `update_order_details` action:
- Now supports labour code ID in request: `labour_code_id`
- Supports manual entry fields: `item_name_manual`, `item_brand_manual`
- Priority order for item updates:
  1. Labour code (if `labour_code_id` provided)
  2. Manual entry (if `item_name_manual` provided)
  3. Inventory item (if `item_id` provided)

### 6. **Updated Started Order Detail Template** (`tracker/templates/tracker/started_order_detail.html`)
Added tabbed interface for item selection with three tabs:

#### **Tab 1: Labour Code Lookup**
- Search field for labour codes
- Auto-complete search results
- Display of selected labour code with code, name, and brand
- Clear button to reset selection

#### **Tab 2: Inventory** (Original)
- Select from existing inventory items
- Auto-fill brand information

#### **Tab 3: Manual Entry** (New Fallback)
- Free-form entry fields for:
  - Item Name
  - Brand
  - Quantity

**JavaScript Features:**
- Debounced search for better performance (300ms debounce)
- Real-time labour code lookup via API
- Tab switching between different selection methods
- Clear button to reset labour code selection

### 7. **Created Database Migration** (`tracker/migrations/0002_labourcode_item_details.py`)
Migration file to add the new fields to the LabourCode table.

### 8. **Updated URL Routing** (`tracker/urls.py`)
Added route for the new labour code lookup API:
```python
path("api/orders/lookup-labour-code/", views_start_order.api_lookup_labour_code, name="api_lookup_labour_code"),
```

---

## How to Use

### For Admin Users - Populating Labour Code Data

1. Go to **Labour Codes** management page
2. Create or edit a labour code
3. Fill in the optional **Item Details** section:
   - **Item Name**: e.g., "Michelin Tire 185/65 R15"
   - **Brand**: e.g., "Michelin"
   - **Quantity**: e.g., 1
   - **Tire Type**: e.g., "New" or "Used"
4. Save the labour code

### For Operators - Updating Order Details

#### Service Orders (with Labour Code Support)
1. Go to the started order detail page
2. Click **Edit Order Details**
3. Change order type to "Service" or "Labour"
4. Item data is now optional (can use labour codes if configured)

#### Sales Orders (with Labour Code Support)
1. Go to the started order detail page
2. Click **Edit Order Details**
3. Choose order type "Sales"
4. You now have three options:

**Option A: Use Labour Code (Recommended)**
1. Click the "Labour Code" tab
2. Type item name or labour code to search
3. Select from search results
4. Item data is auto-filled
5. Adjust quantity if needed

**Option B: Use Inventory**
1. Click the "Inventory" tab
2. Select item from dropdown
3. Brand is auto-filled
4. Adjust quantity if needed

**Option C: Manual Entry (Fallback)**
1. Click the "Manual Entry" tab
2. Type item name manually
3. Type brand manually
4. Enter quantity
5. This is useful for items not in labour codes or inventory

---

## Data Priority

When updating an order with item data, the system uses this priority:

1. **Labour Code Data** (if labour_code_id is provided)
   - Uses item_name, brand, quantity, tire_type from labour code
   - Most reliable for standardized data

2. **Manual Entry** (if item_name_manual is provided)
   - User-provided data
   - Fallback for items not in system

3. **Inventory Items** (if item_id is provided)
   - Legacy option for backward compatibility
   - Uses InventoryItem data

---

## Migration Instructions

### Step 1: Create the Migration
The migration file has been created at `tracker/migrations/0002_labourcode_item_details.py`

### Step 2: Run the Migration
```bash
python manage.py migrate
```

### Step 3: Update Existing Labour Codes (Optional)
If you have existing labour codes, you can:
- Leave the new fields empty (they're optional)
- Or populate them via admin interface with relevant item data
- Or bulk import labour codes with item data via CSV/XLSX

---

## Database Schema Changes

### LabourCode Table - New Columns
```sql
ALTER TABLE tracker_labourcode ADD COLUMN item_name VARCHAR(255) NULL;
ALTER TABLE tracker_labourcode ADD COLUMN brand VARCHAR(128) NULL;
ALTER TABLE tracker_labourcode ADD COLUMN quantity INTEGER UNSIGNED NULL;
ALTER TABLE tracker_labourcode ADD COLUMN tire_type VARCHAR(64) NULL;
```

---

## API Examples

### Search Labour Code by Name
```
GET /tracker/api/orders/lookup-labour-code/?item_name=Michelin
```

**Response:**
```json
{
  "success": true,
  "labour_codes": [
    {
      "id": 1,
      "code": "22007",
      "description": "Michelin Tire 185/65 R15",
      "item_name": "Michelin Tire 185/65 R15",
      "brand": "Michelin",
      "quantity": 1,
      "tire_type": "New",
      "category": "sales"
    }
  ]
}
```

### Search Labour Code by Code
```
GET /tracker/api/orders/lookup-labour-code/?code=22007
```

### Search by Category
```
GET /tracker/api/orders/lookup-labour-code/?item_name=service&category=service
```

---

## Backward Compatibility

✅ **All existing functionality is preserved:**
- Inventory item selection still works
- Manual order updates via classic forms still work
- Service order item selection is optional
- No breaking changes to existing APIs

---

## Features Summary

| Feature | Service Orders | Sales Orders | Labour Orders |
|---------|----------------|--------------|---------------|
| Labour Code Lookup | Optional | ✅ Available | Optional |
| Inventory Selection | No | ✅ Available | No |
| Manual Entry | No | ✅ Available | ✅ Available |
| Item Name | Auto-fill | ✅ Auto-fill | Manual |
| Brand | Auto-fill | ✅ Auto-fill | Manual |
| Quantity | Auto-fill | ✅ Auto-fill | Manual |
| Tire Type | Auto-fill | ✅ Auto-fill | Manual |

---

## Testing Checklist

- [ ] Run database migration: `python manage.py migrate`
- [ ] Create test labour code with item details via admin
- [ ] Test labour code lookup API
- [ ] Test service order update with labour code
- [ ] Test sales order update with labour code
- [ ] Test inventory item selection (backward compatibility)
- [ ] Test manual entry fallback
- [ ] Test form validation
- [ ] Verify item data is saved correctly in Order model
- [ ] Test with multiple labour codes having same item_name

---

## Performance Considerations

- Labour code lookup is optimized with `iexact` (case-insensitive) matching
- Search results are limited to 10 items by default
- Debounced search input (300ms) reduces API calls
- Indexed fields: `code`, `category`, `is_active`, `item_name`

---

## Future Enhancements

- Bulk import labour codes with item data via CSV/XLSX
- Labour code grouping by category
- Item data synchronization with inventory
- Automatic inventory adjustment based on labour code quantity
- Labour code templates for different order types
