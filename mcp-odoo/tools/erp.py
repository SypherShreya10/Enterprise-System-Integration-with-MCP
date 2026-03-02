from typing import Optional, List, Dict, Any
import logging
import datetime
from odoo_client import OdooClient

logger = logging.getLogger(__name__)
client = OdooClient()


#section 4: tool 17 - get product
def get_product(
    *,
    product_id: Optional[int] = None,
    name: Optional[str] = None,
    default_code: Optional[str] = None,
    categ_id: Optional[int] = None,
    type: Optional[str] = None,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """
    Fetch sellable product details (product.product).

    Search and filter products available for sale.

    Args:
        product_id: Specific product ID
        name: Search by product name (partial match)
        default_code: Search by SKU/internal reference (partial match)
        categ_id: Filter by product category
        type: Filter by product type ('product', 'consu', or 'service')
        limit: Maximum records (default=10, max=100)

    Returns:
        List of product dictionaries with:
        - id, name, default_code (SKU)
        - list_price (selling price - customer-facing)
        - type, categ_id, uom_id
        - active, sale_ok, purchase_ok

    Raises:
        ValueError: If invalid parameters or no filters provided
        RuntimeError: If Odoo operation fails

    Safety Guarantees:
        - Read-only operation
        - NO cost fields (standard_price excluded)
        - NO supplier pricing
        - Active products only
        - Sellable products only (sale_ok=True)
        - At least one filter required (prevents full scans)
        - Company-scoped automatically
        - Bounded results

    Business Use Cases:
        - "What's the price of Product X?"
        - "Find product by SKU"
        - "List all service products"

    Security:
        - Cost information (standard_price) deliberately excluded
        - Supplier-specific pricing excluded
        - Only public customer-facing data exposed

    Compliance:
        - AI Safety & Execution Constraints
        - Cost-safe operations
    """

    # ------------------------------------------------------------------
    # Input Validation
    # ------------------------------------------------------------------

    if limit < 1 or limit > 100:
        raise ValueError(f"Limit must be between 1 and 100, got: {limit}")

    # ------------------------------------------------------------------
    # Domain Construction (STRICT)
    # ------------------------------------------------------------------

    # Base restrictions (ALWAYS enforced)
    domain = [
        ("active", "=", True),      # Active products only
        ("sale_ok", "=", True),     # Sellable products only
    ]

    # Search filters (at least one required)
    if product_id is not None:
        if not isinstance(product_id, int) or product_id <= 0:
            raise ValueError(f"product_id must be positive integer, got: {product_id}")
        domain.append(("id", "=", product_id))

    if name is not None:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be non-empty string")
        domain.append(("name", "ilike", name.strip()))

    if default_code is not None:
        if not isinstance(default_code, str) or not default_code.strip():
            raise ValueError("default_code must be non-empty string")
        domain.append(("default_code", "ilike", default_code.strip()))

    if categ_id is not None:
        if not isinstance(categ_id, int) or categ_id <= 0:
            raise ValueError(f"categ_id must be positive integer, got: {categ_id}")
        domain.append(("categ_id", "=", categ_id))

    if type is not None:
        allowed_types = ["product", "consu", "service"]
        if type not in allowed_types:
            raise ValueError(
                f"type must be one of {allowed_types}, got: '{type}'"
            )
        domain.append(("type", "=", type))

    # CRITICAL: Prevent full table scans
    # Base domain has 2 items (active, sale_ok)
    # Need at least 1 search filter
    if len(domain) <= 2:
        raise ValueError(
            "At least one search filter required: "
            "product_id, name, default_code, categ_id, or type"
        )

    # ------------------------------------------------------------------
    # Allowed Fields (COST-SAFE)
    # ------------------------------------------------------------------

    fields = [
        "id",
        "name",
        "default_code",     # SKU/Internal Reference
        "list_price",       # ✅ Selling price (customer-facing)
        "type",             # product/consu/service
        "categ_id",         # Returns (id, name)
        "uom_id",           # Unit of measure
        "active",
        "sale_ok",          # Can be sold
        "purchase_ok",      # Can be purchased
    ]

    # FORBIDDEN FIELDS (documented for clarity):
    # - standard_price: Internal cost (competitive information)
    # - supplier_taxes_id: Supplier-specific data
    # - seller_ids: Supplier pricing
    # - Any accounting/costing fields

    # ------------------------------------------------------------------
    # Audit Logging
    # ------------------------------------------------------------------

    logger.info(
        "MCP Tool: get_product",
        extra={
            "model": "product.product",
            "operation": "search_read",
            "domain": domain,
            "fields": fields,
            "limit": limit,
            "company_id": client.company_id,
            "user_id": client.uid,
            "search_params": {
                "product_id": product_id,
                "name": name,
                "default_code": default_code,
                "categ_id": categ_id,
                "type": type,
            },
        },
    )

    # ------------------------------------------------------------------
    # Execute with Error Handling
    # ------------------------------------------------------------------

    try:
        records = client.search_read(
            model="product.product",
            domain=domain,
            fields=fields,
            limit=limit,
        )

        # Log success
        logger.info(
            f"get_product completed: {len(records)} product(s) found",
            extra={
                "record_count": len(records),
                "search_params": {
                    "product_id": product_id,
                    "name": name,
                    "default_code": default_code,
                },
            },
        )

        return records

    except Exception as exc:
        # Log failure
        logger.error(
            f"get_product failed: {type(exc).__name__}: {str(exc)}",
            extra={
                "domain": domain,
                "error_type": type(exc).__name__,
                "search_params": {
                    "product_id": product_id,
                    "name": name,
                    "default_code": default_code,
                    "categ_id": categ_id,
                    "type": type,
                },
            },
            exc_info=True,
        )
        raise RuntimeError(
            f"Failed to fetch product data: {str(exc)}"
        ) from exc
    

# section 4: tool 18: get product stock
def get_product_stock(
    *,
    product_id: int,
    location_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Check inventory quantity for a product (stock.quant).

    Get current stock levels with location breakdown and reserved quantities.

    Args:
        product_id: Product ID to check (required)
        location_id: Specific warehouse/location (optional, aggregates if not provided)

    Returns:
        Dictionary with:
        - product_id: Product ID
        - product_name: Product name
        - total_quantity: Total quantity across all locations
        - total_reserved: Total reserved quantity
        - total_available: Available quantity (total - reserved)
        - locations: List of location breakdowns with:
            - location_id, location_name
            - quantity, reserved_quantity, available_quantity

    Raises:
        ValueError: If invalid product_id or location_id
        RuntimeError: If Odoo operation fails

    Safety Guarantees:
        - Read-only operation
        - NO inventory adjustments allowed
        - NO cost fields exposed
        - Company-scoped automatically
        - Internal warehouse locations only
        - Only locations with stock > 0

    Business Use Cases:
        - "Do we have 100 units in stock?"
        - "Check warehouse inventory for Product X"
        - "What's available vs reserved?"

    Aggregation Logic:
        If location_id not specified, sums quantities across
        all internal warehouse locations with stock > 0.

    Compliance:
        - AI Safety & Execution Constraints
        - Read-only operations
    """

    # ------------------------------------------------------------------
    # Input Validation
    # ------------------------------------------------------------------

    if not isinstance(product_id, int) or product_id <= 0:
        raise ValueError(
            f"product_id must be positive integer, got: {product_id}"
        )

    if location_id is not None:
        if not isinstance(location_id, int) or location_id <= 0:
            raise ValueError(
                f"location_id must be positive integer, got: {location_id}"
            )

    # ------------------------------------------------------------------
    # Verify Product Exists (Optional but Recommended)
    # ------------------------------------------------------------------

    try:
        product = client.search_read(
            model="product.product",
            domain=[
                ("id", "=", product_id),
                ("active", "=", True),
            ],
            fields=["id", "name"],
            limit=1,
        )

        if not product:
            raise ValueError(
                f"Product with id={product_id} not found or is inactive"
            )

        product_name = product[0]["name"]

    except ValueError:
        raise
    except Exception as e:
        # If product check fails, continue (stock check will return empty anyway)
        logger.warning(
            f"Could not verify product {product_id}: {e}",
            extra={"product_id": product_id},
        )
        product_name = f"Product {product_id}"

    # ------------------------------------------------------------------
    # Domain Construction (STRICT)
    # ------------------------------------------------------------------

    domain = [
        ("product_id", "=", product_id),
        ("quantity", ">", 0),                    # Only locations with stock
        ("location_id.usage", "=", "internal"),  # Warehouses only (not customers/suppliers)
    ]

    if location_id is not None:
        domain.append(("location_id", "=", location_id))

    # ------------------------------------------------------------------
    # Allowed Fields (NO COST DATA)
    # ------------------------------------------------------------------

    fields = [
        "product_id",           # Returns (id, name)
        "location_id",          # Returns (id, name)
        "quantity",             # Total quantity at location
        "reserved_quantity",    # Reserved for orders/production
    ]

    # FORBIDDEN FIELDS:
    # - inventory_value
    # - Any costing fields

    # ------------------------------------------------------------------
    # Audit Logging
    # ------------------------------------------------------------------

    logger.info(
        "MCP Tool: get_product_stock",
        extra={
            "model": "stock.quant",
            "operation": "search_read",
            "domain": domain,
            "fields": fields,
            "product_id": product_id,
            "location_id": location_id,
            "company_id": client.company_id,
            "user_id": client.uid,
        },
    )

    # ------------------------------------------------------------------
    # Execute with Error Handling
    # ------------------------------------------------------------------

    try:
        records = client.search_read(
            model="stock.quant",
            domain=domain,
            fields=fields,
            limit=100,
        )

        # Handle no stock found
        if not records:
            logger.info(
                f"No stock found for product {product_id} ({product_name})",
                extra={"product_id": product_id, "product_name": product_name},
            )
            
            return {
                "product_id": product_id,
                "product_name": product_name,
                "total_quantity": 0,
                "total_reserved": 0,
                "total_available": 0,
                "locations": [],
            }

        # Aggregate stock across locations
        total_quantity = 0
        total_reserved = 0
        locations: List[Dict[str, Any]] = []

        for r in records:
            qty = r["quantity"]
            reserved = r["reserved_quantity"]
            available = qty - reserved

            total_quantity += qty
            total_reserved += reserved

            locations.append({
                "location_id": r["location_id"][0],
                "location_name": r["location_id"][1],
                "quantity": qty,
                "reserved_quantity": reserved,
                "available_quantity": available,
            })

        total_available = total_quantity - total_reserved

        # Log success
        logger.info(
            f"get_product_stock completed: Product {product_id} ({product_name}) - "
            f"{total_quantity} total ({total_available} available) across {len(locations)} location(s)",
            extra={
                "product_id": product_id,
                "product_name": product_name,
                "total_quantity": total_quantity,
                "total_available": total_available,
                "location_count": len(locations),
            },
        )

        return {
            "product_id": product_id,
            "product_name": product_name,
            "total_quantity": total_quantity,
            "total_reserved": total_reserved,
            "total_available": total_available,
            "locations": locations,
        }

    except ValueError:
        # Re-raise validation errors
        raise

    except Exception as exc:
        # Log failure
        logger.error(
            f"get_product_stock failed: {type(exc).__name__}: {str(exc)}",
            extra={
                "product_id": product_id,
                "location_id": location_id,
                "domain": domain,
                "error_type": type(exc).__name__,
            },
            exc_info=True,
        )
        raise RuntimeError(
            f"Failed to fetch stock data for product {product_id}: {str(exc)}"
        ) from exc


#section 4: tool 19 - check product availability
def check_product_availability(
    *,
    product_id: int,
    quantity: float,
    date_required: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Determine whether requested quantity of a product can be fulfilled.

    Composite tool combining product, stock, and purchase order data
    to provide comprehensive availability analysis.

    Args:
        product_id: Product ID to check (required)
        quantity: Required quantity (required, must be positive)
        date_required: Target delivery date in YYYY-MM-DD format (optional)

    Returns:
        Dictionary with:
        - product_id, product_name, product_type
        - requested_quantity
        - date_required
        - current_stock (available after reserved)
        - current_stock_total (before reserved)
        - current_stock_reserved
        - incoming_quantity (from purchase orders)
        - can_fulfill (boolean)
        - shortage (quantity short if can't fulfill)
        - recommended_action (next steps)

    Raises:
        ValueError: If invalid parameters
        RuntimeError: If Odoo operations fail

    Safety Guarantees:
        - Read-only composite operation
        - No inventory mutations
        - Company-scoped automatically
        - No cost data exposed

    Business Use Cases:
        - "Can we fulfill order for 200 units by Dec 15?"
        - "Do we have enough stock for this sale?"
        - "When can we deliver if stock is low?"

    Logic:
        1. Verify product exists and is active
        2. Handle non-stockable items (consumables/services)
        3. Aggregate current stock (total - reserved)
        4. Check incoming purchase orders (if date specified)
        5. Calculate availability and provide recommendation

    Compliance:
        - AI Safety & Execution Constraints
        - Read-only operations
    """

    # ------------------------------------------------------------------
    # Input Validation
    # ------------------------------------------------------------------

    if not isinstance(product_id, int) or product_id <= 0:
        raise ValueError(
            f"product_id must be positive integer, got: {product_id}"
        )

    if not isinstance(quantity, (int, float)) or quantity <= 0:
        raise ValueError(
            f"quantity must be positive number, got: {quantity}"
        )

    required_date_obj = None
    if date_required:
        try:
            required_date_obj = datetime.date.fromisoformat(date_required)
        except (ValueError, TypeError) as e:
            raise ValueError(
                f"date_required must be in YYYY-MM-DD format, got: {date_required}"
            ) from e

    # ------------------------------------------------------------------
    # Audit Logging (Start)
    # ------------------------------------------------------------------

    logger.info(
        "MCP Tool: check_product_availability",
        extra={
            "model": "product.product + stock.quant + purchase.order.line (composite)",
            "operation": "availability_check",
            "product_id": product_id,
            "requested_quantity": quantity,
            "date_required": date_required,
            "company_id": client.company_id,
            "user_id": client.uid,
        },
    )

    # ------------------------------------------------------------------
    # Step 1: Verify Product Exists
    # ------------------------------------------------------------------

    try:
        product = client.search_read(
            model="product.product",
            domain=[
                ("id", "=", product_id),
                ("active", "=", True),
            ],
            fields=["id", "name", "type"],
            limit=1,
        )

        if not product:
            raise ValueError(
                f"Product with id={product_id} not found or inactive"
            )

        product_data = product[0]
        product_name = product_data["name"]
        product_type = product_data["type"]

    except ValueError:
        raise
    except Exception as exc:
        logger.error(
            f"Product lookup failed: {type(exc).__name__}: {str(exc)}",
            extra={"product_id": product_id},
            exc_info=True,
        )
        raise RuntimeError(
            f"Failed to verify product {product_id}: {str(exc)}"
        ) from exc

    # ------------------------------------------------------------------
    # Step 2: Handle Non-Stocked Products
    # ------------------------------------------------------------------

    # Consumables and services don't track physical stock
    # if product_type in ["consu", "service"]:
    #     logger.info(
    #         f"Product {product_id} ({product_name}) is {product_type} - no stock tracking",
    #         extra={"product_type": product_type},
    #     )
        
    #     return {
    #         "product_id": product_id,
    #         "product_name": product_name,
    #         "product_type": product_type,
    #         "requested_quantity": quantity,
    #         "date_required": date_required,
    #         "current_stock": None,
    #         "current_stock_total": None,
    #         "current_stock_reserved": None,
    #         "incoming_quantity": None,
    #         "can_fulfill": True,
    #         "shortage": 0.0,
    #         "recommended_action": f"{product_type.capitalize()} item - no stock tracking required",
    #     }

    # ------------------------------------------------------------------
    # Step 3: Get Current Stock
    # ------------------------------------------------------------------

    try:
        quants = client.search_read(
            model="stock.quant",
            domain=[
                ("product_id", "=", product_id),
                ("quantity", ">", 0),
                ("location_id.usage", "=", "internal"),
            ],
            fields=["quantity", "reserved_quantity"],
            limit=100,
        )

        total_qty = sum(q["quantity"] for q in quants)
        total_reserved = sum(q["reserved_quantity"] for q in quants)
        total_available = total_qty - total_reserved

    except Exception as exc:
        logger.error(
            f"Stock lookup failed: {type(exc).__name__}: {str(exc)}",
            extra={"product_id": product_id},
            exc_info=True,
        )
        raise RuntimeError(
            f"Failed to fetch stock for product {product_id}: {str(exc)}"
        ) from exc

    # ------------------------------------------------------------------
    # Step 4: Basic Fulfillment Check
    # ------------------------------------------------------------------

    can_fulfill = total_available >= quantity
    shortage = max(quantity - total_available, 0.0)
    incoming_qty = 0.0

    # ------------------------------------------------------------------
    # Step 5: Check Incoming Purchase Orders (if date specified)
    # ------------------------------------------------------------------

    if required_date_obj and not can_fulfill:
        try:
            purchase_lines = client.search_read(
                model="purchase.order.line",
                domain=[
                    ("product_id", "=", product_id),
                    ("order_id.state", "=", "purchase"),  # Confirmed POs only
                ],
                fields=[
                    "product_qty",
                    "qty_received",
                    "date_planned",  # ✅ Direct field on line
                ],
                limit=100,
            )

            for line in purchase_lines:
                # Calculate remaining quantity to be received
                remaining = line["product_qty"] - line["qty_received"]
                
                if remaining <= 0:
                    continue

                # Check planned delivery date
                if line.get("date_planned"):
                    planned_date_str = line["date_planned"]
                    
                    # Handle datetime format (might have time component)
                    if isinstance(planned_date_str, str):
                        planned_date_str = planned_date_str.split(" ")[0]
                        try:
                            planned_date = datetime.date.fromisoformat(planned_date_str)
                            
                            # Only count if arriving before required date
                            if planned_date <= required_date_obj:
                                incoming_qty += remaining
                        except:
                            # If date parsing fails, count it anyway (conservative)
                            incoming_qty += remaining
                else:
                    # No planned date - count it anyway
                    incoming_qty += remaining

            # Recalculate fulfillment with incoming stock
            if (total_available + incoming_qty) >= quantity:
                can_fulfill = True
                shortage = 0.0

        except Exception as exc:
            logger.error(
                f"Purchase order lookup failed: {type(exc).__name__}: {str(exc)}",
                extra={"product_id": product_id},
                exc_info=True,
            )
            # Don't fail - just log warning and continue without PO data
            logger.warning(
                f"Could not evaluate incoming POs for product {product_id}",
                extra={"error": str(exc)},
            )

    # ------------------------------------------------------------------
    # Step 6: Recommended Action
    # ------------------------------------------------------------------

    if can_fulfill:
        if incoming_qty > 0:
            recommended_action = "Sufficient with incoming stock - proceed with sale"
        else:
            recommended_action = "Stock sufficient - proceed with sale"
    else:
        if incoming_qty > 0:
            recommended_action = f"Short {shortage} units even with incoming - create urgent purchase order"
        else:
            recommended_action = f"Short {shortage} units - create purchase order"

    # ------------------------------------------------------------------
    # Audit Logging (Result)
    # ------------------------------------------------------------------

    logger.info(
        f"check_product_availability completed: Product {product_id} ({product_name}) - "
        f"Requested: {quantity}, Available: {total_available}, Incoming: {incoming_qty}, "
        f"Can fulfill: {can_fulfill}",
        extra={
            "product_id": product_id,
            "product_name": product_name,
            "requested_quantity": quantity,
            "available_quantity": total_available,
            "incoming_quantity": incoming_qty,
            "can_fulfill": can_fulfill,
            "shortage": shortage,
        },
    )

    # ------------------------------------------------------------------
    # Return Comprehensive Result
    # ------------------------------------------------------------------

    return {
        "product_id": product_id,
        "product_name": product_name,
        "product_type": product_type,
        "requested_quantity": quantity,
        "date_required": date_required,
        "current_stock": total_available,
        "current_stock_total": total_qty,
        "current_stock_reserved": total_reserved,
        "incoming_quantity": incoming_qty,
        "can_fulfill": can_fulfill,
        "shortage": shortage,
        "recommended_action": recommended_action,
    }


#section 4: tool 20 - get stock location 
def get_stock_location(
    *,
    location_id: Optional[int] = None,
    name: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """
    Fetch internal warehouse/stock location information.

    Get details about company warehouses and storage locations.
    Customer, supplier, and transit locations excluded for security.

    Args:
        location_id: Specific location ID
        name: Search by location name (partial match)
        limit: Maximum records (default=50, max=100)

    Returns:
        List of location dictionaries with:
        - id, name, complete_name (full hierarchical path)
        - usage (always 'internal')
        - company_id

    Raises:
        ValueError: If invalid parameters
        RuntimeError: If Odoo operation fails

    Safety Guarantees:
        - Read-only operation
        - Internal locations only (warehouses)
        - Customer/supplier/transit locations excluded
        - Company-scoped automatically
        - Bounded results

    Business Use Cases:
        - "What warehouses do we have?"
        - "Where is Warehouse A?"
        - "List all storage locations"

    Security:
        Only internal warehouse locations exposed.
        External locations (customer, supplier) hidden for security.

    Compliance:
        - AI Safety & Execution Constraints
        - Domain-restricted operations
    """

    # ------------------------------------------------------------------
    # Input Validation
    # ------------------------------------------------------------------

    if limit < 1 or limit > 100:
        raise ValueError(f"Limit must be between 1 and 100, got: {limit}")

    # ------------------------------------------------------------------
    # Domain Construction (STRICT - Internal Only)
    # ------------------------------------------------------------------

    # ALWAYS restrict to internal locations
    domain = [
        ("usage", "=", "internal"),  # Warehouses only
    ]

    # Search filters
    if location_id is not None:
        if not isinstance(location_id, int) or location_id <= 0:
            raise ValueError(
                f"location_id must be positive integer, got: {location_id}"
            )
        domain.append(("id", "=", location_id))

    if name is not None:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be non-empty string")
        domain.append(("name", "ilike", name.strip()))

    # ------------------------------------------------------------------
    # Allowed Fields
    # ------------------------------------------------------------------

    fields = [
        "id",
        "name",
        "complete_name",  # Full hierarchical path
        "usage",          # Always 'internal'
        "company_id",     # Returns (id, name)
    ]

    # ------------------------------------------------------------------
    # Audit Logging
    # ------------------------------------------------------------------

    logger.info(
        "MCP Tool: get_stock_location",
        extra={
            "model": "stock.location",
            "operation": "search_read",
            "domain": domain,
            "fields": fields,
            "limit": limit,
            "company_id": client.company_id,
            "user_id": client.uid,
            "search_params": {
                "location_id": location_id,
                "name": name,
            },
        },
    )

    # ------------------------------------------------------------------
    # Execute with Error Handling
    # ------------------------------------------------------------------

    try:
        records = client.search_read(
            model="stock.location",
            domain=domain,
            fields=fields,
            limit=limit,
        )

        # Log success
        logger.info(
            f"get_stock_location completed: {len(records)} location(s) found",
            extra={"record_count": len(records)},
        )

        return records

    except Exception as exc:
        # Log failure
        logger.error(
            f"get_stock_location failed: {type(exc).__name__}: {str(exc)}",
            extra={
                "domain": domain,
                "error_type": type(exc).__name__,
                "search_params": {
                    "location_id": location_id,
                    "name": name,
                },
            },
            exc_info=True,
        )
        raise RuntimeError(
            f"Failed to fetch stock locations: {str(exc)}"
        ) from exc