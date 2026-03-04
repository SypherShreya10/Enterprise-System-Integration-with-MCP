from typing import Optional, List, Dict, Any
import logging
import datetime
from odoo_client import OdooClient, ValidationError

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


#section 5: tool 21 - get sale order
def get_sale_order(
    order_id: Optional[int] = None,
    name: Optional[str] = None,
    partner_id: Optional[int] = None,
    state: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """
    Tool ID: 021
    Model: sale.order
    Risk: LOW (Read Only)

    Returns sales order records matching the given filters.
    All states including 'cancel' are readable (audit/history use case).
    Company scope is enforced at OdooClient connection level.

    Derived fields (computed during normalization, not fetched from Odoo):
        - partner_name: human-readable customer name (from partner_id)
        - salesperson_name: human-readable salesperson name (from user_id)
    """

    client = OdooClient()

    # ------------------------------------------------------------------
    # Validate limit
    # ------------------------------------------------------------------
    if limit > 100:
        raise ValidationError("Limit cannot exceed 100.")

    # ------------------------------------------------------------------
    # Validate state if provided
    # ------------------------------------------------------------------
    allowed_states = ["draft", "sent", "sale", "done", "cancel"]
    if state is not None:
        if state not in allowed_states:
            raise ValidationError(
                f"Invalid state '{state}'. Allowed values: {allowed_states}"
            )

    # ------------------------------------------------------------------
    # Build domain
    # ------------------------------------------------------------------
    domain = []

    if order_id:
        domain.append(("id", "=", order_id))

    if name:
        domain.append(("name", "ilike", name))

    if partner_id:
        domain.append(("partner_id", "=", partner_id))

    if state:
        domain.append(("state", "=", state))

    if date_from:
        domain.append(("date_order", ">=", date_from))

    if date_to:
        domain.append(("date_order", "<=", date_to))
    
    # Prevent full table scans
    if not domain:
        raise ValidationError(
            "At least one filter must be provided."
        )

    # ------------------------------------------------------------------
    # Allowed READ fields — strict allowlist per safety policy
    # ------------------------------------------------------------------
    fields = [
        "id",
        "name",
        "partner_id",
        "date_order",
        "validity_date",
        "amount_total",
        "amount_tax",
        "amount_untaxed",
        "state",
        "user_id",
    ]

    records = client.search_read(
        model="sale.order",
        domain=domain,
        fields=fields,
        limit=limit,
    )

    # ------------------------------------------------------------------
    # Normalize Many2one fields
    # Odoo returns these as [id, name] — split into clean separate keys
    # ------------------------------------------------------------------
    for record in records:
        if record.get("partner_id"):
            record["partner_name"] = record["partner_id"][1]
            record["partner_id"] = record["partner_id"][0]

        if record.get("user_id"):
            record["salesperson_name"] = record["user_id"][1]
            record["user_id"] = record["user_id"][0]

    return records


#section 5: tool 22 - get sale order lines
def get_sale_order_lines(
    order_id: int,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """
    Tool ID: 022
    Model: sale.order.line
    Risk: LOW (Read Only)

    Returns all line items for a given sales order.
    Works for all order states including cancelled orders (audit use case).
    Company scope is enforced at OdooClient connection level.

    Derived fields (computed during normalization, not fetched from Odoo):
        - product_name: human-readable product name (from product_id)

    Raises:
        ValidationError: if order_id is missing or order does not exist.
    """

    client = OdooClient()

    # ------------------------------------------------------------------
    # Validate inputs
    # ------------------------------------------------------------------
    if not order_id:
        raise ValidationError("order_id is required.")

    if limit > 100:
        raise ValidationError("Limit cannot exceed 100.")

    # ------------------------------------------------------------------
    # Validate parent order exists and is accessible
    # No state filter — cancelled orders are valid for audit/history
    # ------------------------------------------------------------------
    parent_order = client.search_read(
        model="sale.order",
        domain=[("id", "=", order_id)],
        fields=["id", "name", "state"],
        limit=1,
    )

    if not parent_order:
        raise ValidationError(
            f"Sales order with id {order_id} does not exist "
            "or is not accessible."
        )

    # ------------------------------------------------------------------
    # Build domain
    # ------------------------------------------------------------------
    domain = [("order_id", "=", order_id)]

    # ------------------------------------------------------------------
    # Allowed READ fields — strict allowlist per safety policy
    # ------------------------------------------------------------------
    fields = [
        "id",
        "order_id",
        "product_id",
        "product_uom_qty",
        "price_unit",
        "price_subtotal",
        "price_total",
        "discount",
    ]

    records = client.search_read(
        model="sale.order.line",
        domain=domain,
        fields=fields,
        limit=limit,
    )

    # ------------------------------------------------------------------
    # Normalize Many2one fields
    # ------------------------------------------------------------------
    for record in records:
        if record.get("product_id"):
            record["product_name"] = record["product_id"][1]
            record["product_id"] = record["product_id"][0]

        if record.get("order_id"):
            record["order_id"] = record["order_id"][0]

    return records


#section 5: tool 23 - create sale order
def create_sale_order(
    *,
    partner_id: int,
    order_lines: List[Dict[str, Any]],
    date_order: Optional[str] = None,
    validity_date: Optional[str] = None,
    client_order_ref: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Tool ID: 023
    Model: sale.order + sale.order.line
    Risk: MEDIUM (Create with heavy validation)

    Creates a draft sales order after strict validation.
    Order remains in 'draft' state — requires human confirmation before processing.

    Args:
        partner_id: Customer partner ID (must be an existing customer)
        order_lines: List of dicts with product_id and product_uom_qty
        date_order: Order date in YYYY-MM-DD format (defaults to today)
        validity_date: Quote expiry date in YYYY-MM-DD format
        client_order_ref: Customer's own reference/PO number (optional)

    Returns:
        Created order summary including order_id, name, totals, and line summary.
    """

    client = OdooClient()

    # ------------------------------------------------------------------
    # Validate date formats upfront
    # ------------------------------------------------------------------
    if date_order:
        try:
            datetime.date.fromisoformat(date_order)
        except ValueError:
            raise ValidationError("date_order must be in YYYY-MM-DD format.")
    else:
        date_order = datetime.date.today().isoformat()

    if validity_date:
        try:
            datetime.date.fromisoformat(validity_date)
        except ValueError:
            raise ValidationError("validity_date must be in YYYY-MM-DD format.")

        if validity_date < date_order:
            raise ValidationError("validity_date cannot be before date_order.")

    # ------------------------------------------------------------------
    # Validate partner — must exist and be a customer
    # ------------------------------------------------------------------
    partner = client.search_read(
        model="res.partner",
        domain=[
            ("id", "=", partner_id),
            ("customer_rank", ">", 0),
        ],
        fields=["id", "name"],
        limit=1,
    )

    if not partner:
        raise ValidationError(
            f"Partner {partner_id} does not exist or is not a customer."
        )

    partner_name = partner[0]["name"]

    # ------------------------------------------------------------------
    # Validate order lines — must be a non-empty list
    # ------------------------------------------------------------------
    if not order_lines or not isinstance(order_lines, list):
        raise ValidationError("order_lines must be a non-empty list.")

    # ------------------------------------------------------------------
    # Check for duplicate products across lines
    # ------------------------------------------------------------------
    seen_products = set()
    for line in order_lines:
        pid = line.get("product_id")
        if pid in seen_products:
            raise ValidationError(
                f"Duplicate product_id {pid} in order_lines. "
                "Combine quantities into a single line."
            )
        seen_products.add(pid)

    # ------------------------------------------------------------------
    # Validate each line
    # ------------------------------------------------------------------
    validated_lines = []
    line_summary = []

    for line in order_lines:

        product_id = line.get("product_id")
        qty = line.get("product_uom_qty")

        if not product_id or not qty or qty <= 0:
            raise ValidationError(
                "Each order line must have a valid product_id "
                "and a positive product_uom_qty."
            )

        # Price override is forbidden — price comes from product list_price
        if "price_unit" in line:
            raise ValidationError(
                "Manual price override is not allowed. "
                "Price is derived from the product list_price."
            )

        # Validate product exists, is active, and is sellable
        product = client.search_read(
            model="product.product",
            domain=[
                ("id", "=", product_id),
                ("active", "=", True),
                ("sale_ok", "=", True),
            ],
            fields=["id", "name", "list_price"],
            limit=1,
        )

        if not product:
            raise ValidationError(
                f"Product {product_id} does not exist, "
                "is archived, or is not sellable."
            )

        product_data = product[0]
        product_name = product_data["name"]
        list_price = product_data["list_price"]

        # Stock check — warning only, not a hard block
        # Order is in draft; no stock is committed at this stage
        stock = client.search_read(
            model="stock.quant",
            domain=[
                ("product_id", "=", product_id),
                ("quantity", ">", 0),
                ("location_id.usage", "=", "internal"),
            ],
            fields=["quantity", "reserved_quantity"],
            limit=100,
        )

        total_qty = sum(q.get("quantity") or 0 for q in stock)
        total_reserved = sum(q.get("reserved_quantity") or 0 for q in stock)
        available = total_qty - total_reserved

        stock_warning = None
        if available < qty:
            stock_warning = (
                f"Low stock: {available} units available, "
                f"{qty} requested. Human review required before confirming."
            )

        validated_lines.append((0, 0, {
            "product_id": product_id,
            "product_uom_qty": qty,
            "price_unit": list_price,
        }))

        line_summary.append({
            "product_id": product_id,
            "product_name": product_name,
            "quantity": qty,
            "unit_price": list_price,
            "stock_available": available,
            "stock_warning": stock_warning,
        })

    # ------------------------------------------------------------------
    # Prepare order values
    # Forbidden fields: company_id (auto-set), state (always draft on create)
    # ------------------------------------------------------------------
    values = {
        "partner_id": partner_id,
        "order_line": validated_lines,
        "date_order": date_order,
    }

    if validity_date:
        values["validity_date"] = validity_date

    if client_order_ref:
        values["client_order_ref"] = client_order_ref

    # ------------------------------------------------------------------
    # Create order — Odoo sets state='draft' automatically
    # ------------------------------------------------------------------
    order_id = client.create("sale.order", values)

    created = client.search_read(
        model="sale.order",
        domain=[("id", "=", order_id)],
        fields=[
            "id",
            "name",
            "amount_total",
            "state",
            "date_order",
            "validity_date",
        ],
        limit=1,
    )[0]

    return {
        "order_id": created["id"],
        "order_name": created["name"],
        "partner_id": partner_id,
        "partner_name": partner_name,
        "amount_total": created["amount_total"],
        "state": created["state"],
        "date_order": created["date_order"],
        "validity_date": created.get("validity_date"),
        "lines": line_summary,
    }


#section 5: tool 24 - get customer order history
def get_customer_order_history(
    *,
    partner_id: int,
) -> Dict[str, Any]:
    """
    Tool ID: 024
    Model: sale.order (read-only)
    Risk: LOW (Aggregated read)

    Retrieve all sales orders for a specific customer,
    along with accurate buying pattern summary and analytics.

    Analytics are computed server-side via read_group — always accurate
    regardless of how many orders the customer has.

    Orders list is paginated (max 100 for display) and clearly marked
    as truncated if the customer has more than 100 orders.

    Args:
        partner_id: Customer partner ID (must exist and be a customer)

    Returns:
        {
            "partner_id": int,
            "partner_name": str,
            "orders": [
                {
                    "id": int,
                    "name": str,
                    "date_order": str (YYYY-MM-DD),
                    "amount_total": float,
                    "state": str,
                    "salesperson_id": int | None,
                    "salesperson_name": str | None,
                }
            ],
            "summary": {
                "total_orders": int,           # always accurate — all records
                "total_orders_returned": int,  # what is in orders list
                "truncated": bool,             # true if customer has >100 orders
                "total_revenue": float,        # sale + done only, always accurate
                "average_order_value": float,  # sale + done only, always accurate
                "most_recent_order_date": str | None,
                "most_recent_active_order_date": str | None,
                "state_breakdown": {           # always accurate — all records
                    "draft": int,
                    "sent": int,
                    "sale": int,
                    "done": int,
                    "cancel": int,
                }
            }
        }
    """

    client = OdooClient()

    # ------------------------------------------------------------------
    # Validate partner exists and is a customer
    # ------------------------------------------------------------------
    partner = client.search_read(
        model="res.partner",
        domain=[
            ("id", "=", partner_id),
            ("customer_rank", ">", 0),
        ],
        fields=["id", "name"],
        limit=1,
    )

    if not partner:
        raise ValidationError(
            f"Partner {partner_id} does not exist or is not a customer."
        )

    partner_name = partner[0]["name"]

    # ------------------------------------------------------------------
    # SERVER-SIDE ANALYTICS — always accurate, regardless of order count
    # These calls ask Odoo to compute aggregates on ALL records.
    # Never affected by the 100-record display limit.
    # ------------------------------------------------------------------

    # Total order count across all states
    total_orders = client.search_count(
        model="sale.order",
        domain=[("partner_id", "=", partner_id)],
    )

    # Revenue aggregation — confirmed and done orders only
    # Cancelled and draft orders must never inflate revenue figures
    revenue_agg = client.read_group(
        model="sale.order",
        domain=[
            ("partner_id", "=", partner_id),
            ("state", "in", ["sale", "done"]),
        ],
        fields=["amount_total:sum"],
        groupby=[],
    )

    total_revenue = 0.0
    total_revenue_orders = 0
    if revenue_agg:
        total_revenue = revenue_agg[0].get("amount_total", 0.0) or 0.0
        total_revenue_orders = revenue_agg[0].get("__count", 0) or 0

    average_order_value = (
        total_revenue / total_revenue_orders
        if total_revenue_orders > 0
        else 0.0
    )

    # State breakdown — across all orders, not just returned 100
    state_agg = client.read_group(
        model="sale.order",
        domain=[("partner_id", "=", partner_id)],
        fields=["state"],
        groupby=["state"],
    )

    state_breakdown = {
        "draft": 0,
        "sent": 0,
        "sale": 0,
        "done": 0,
        "cancel": 0,
    }
    for group in state_agg:
        state = group.get("state")
        if state in state_breakdown:
            state_breakdown[state] = group.get("__count", 0)

    # ------------------------------------------------------------------
    # DISPLAY LIST — paginated, max 100 records
    # Used only for showing orders to the user.
    # Analytics above are independent of this limit.
    # ------------------------------------------------------------------
    orders_raw = client.search_read(
        model="sale.order",
        domain=[("partner_id", "=", partner_id)],
        fields=[
            "id",
            "name",
            "date_order",
            "amount_total",
            "state",
            "user_id",
        ],
        limit=100,
    )

    # ------------------------------------------------------------------
    # Normalize orders list
    # ------------------------------------------------------------------
    orders = []
    for o in orders_raw:

        # Normalize date — handle both "2026-03-04 10:30:00" and "2026-03-04"
        raw_date = o.get("date_order") or ""
        clean_date = (
            raw_date.split(" ")[0].split("T")[0]
            if raw_date else None
        )

        # Normalize salesperson Many2one [id, name] → separate keys
        salesperson_id = None
        salesperson_name = None
        if o.get("user_id"):
            salesperson_id = o["user_id"][0]
            salesperson_name = o["user_id"][1]

        orders.append({
            "id": o["id"],
            "name": o["name"],
            "date_order": clean_date,
            "amount_total": o.get("amount_total", 0.0),
            "state": o.get("state"),
            "salesperson_id": salesperson_id,
            "salesperson_name": salesperson_name,
        })

    # ------------------------------------------------------------------
    # Date analytics — computed from display list
    # Note: if truncated, this reflects most recent within returned 100.
    # For full date accuracy on large customers, use date_order sort.
    # ------------------------------------------------------------------
    def latest_date(order_list):
        dates = [
            o["date_order"]
            for o in order_list
            if o.get("date_order")
        ]
        if not dates:
            return None
        return max(dates)

    active_orders = [
        o for o in orders
        if o.get("state") in ("sale", "done")
    ]

    most_recent_order_date = latest_date(orders)
    most_recent_active_order_date = latest_date(active_orders)

    # ------------------------------------------------------------------
    # Return
    # ------------------------------------------------------------------
    return {
        "partner_id": partner_id,
        "partner_name": partner_name,
        "orders": orders,
        "summary": {
            "total_orders": total_orders,
            "total_orders_returned": len(orders),
            "truncated": total_orders > 100,
            "total_revenue": round(total_revenue, 2),
            "average_order_value": round(average_order_value, 2),
            "most_recent_order_date": most_recent_order_date,
            "most_recent_active_order_date": most_recent_active_order_date,
            "state_breakdown": state_breakdown,
        },
    }

#section 6: tool 25 - get purchase order
def get_purchase_order(
    *,
    order_id: Optional[int] = None,
    partner_id: Optional[int] = None,
    state: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """
    Tool ID: 025
    Model: purchase.order
    Risk: LOW (Read Only)

    Returns purchase orders matching the given filters.
    Company scope enforced at OdooClient connection level.
    """

    client = OdooClient()

    # ------------------------------------------------------------------
    # Validate limit
    # ------------------------------------------------------------------
    if limit > 100:
        raise ValidationError("Limit cannot exceed 100.")

    # ------------------------------------------------------------------
    # Validate state
    # ------------------------------------------------------------------
    allowed_states = ["draft", "sent", "to approve", "purchase", "done", "cancel"]
    if state and state not in allowed_states:
        raise ValidationError(
            f"Invalid state '{state}'. Allowed: {allowed_states}"
        )

    # ------------------------------------------------------------------
    # Validate date formats
    # ------------------------------------------------------------------
    if date_from:
        try:
            datetime.date.fromisoformat(date_from)
        except ValueError:
            raise ValidationError("date_from must be in YYYY-MM-DD format.")

    if date_to:
        try:
            datetime.date.fromisoformat(date_to)
        except ValueError:
            raise ValidationError("date_to must be in YYYY-MM-DD format.")

    if date_from and date_to and date_to < date_from:
        raise ValidationError("date_to cannot be before date_from.")

    # ------------------------------------------------------------------
    # Build domain
    # ------------------------------------------------------------------
    domain = []

    if order_id:
        domain.append(("id", "=", order_id))
    if partner_id:
        domain.append(("partner_id", "=", partner_id))
    if state:
        domain.append(("state", "=", state))
    if date_from:
        domain.append(("date_planned", ">=", date_from))
    if date_to:
        domain.append(("date_planned", "<=", date_to))

    if not domain:
        raise ValidationError("At least one filter is required.")

    # ------------------------------------------------------------------
    # Allowed READ fields — strict allowlist per safety policy
    # ------------------------------------------------------------------
    records = client.search_read(
        model="purchase.order",
        domain=domain,
        fields=[
            "id",
            "name",
            "partner_id",
            "date_order",
            "date_planned",
            "amount_total",
            "state",
        ],
        limit=limit,
    )

    # ------------------------------------------------------------------
    # Normalize Many2one fields
    # ------------------------------------------------------------------
    for r in records:
        if r.get("partner_id"):
            r["partner_name"] = r["partner_id"][1]
            r["partner_id"] = r["partner_id"][0]

    return records

#section 6: tool 26 - get purchase order lines
def get_purchase_order_lines(
    *,
    order_id: int,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """
    Tool ID: 026
    Model: purchase.order.line
    Risk: LOW (Read Only)

    Returns all line items for a given purchase order.
    Company scope enforced at OdooClient connection level.

    Derived fields (computed during normalization):
        - product_name: human-readable product name (from product_id)

    Raises:
        ValidationError: if order_id is missing or order does not exist.
    """

    client = OdooClient()

    # ------------------------------------------------------------------
    # Validate inputs
    # ------------------------------------------------------------------
    if not order_id:
        raise ValidationError("order_id is required.")

    if limit > 100:
        raise ValidationError("Limit cannot exceed 100.")

    # ------------------------------------------------------------------
    # Validate parent order exists
    # ------------------------------------------------------------------
    parent = client.search_read(
        model="purchase.order",
        domain=[("id", "=", order_id)],
        fields=["id", "name", "state"],
        limit=1,
    )

    if not parent:
        raise ValidationError(
            f"Purchase order with id {order_id} does not exist "
            "or is not accessible."
        )

    # ------------------------------------------------------------------
    # Allowed READ fields — strict allowlist per safety policy
    # ------------------------------------------------------------------
    records = client.search_read(
        model="purchase.order.line",
        domain=[("order_id", "=", order_id)],
        fields=[
            "id",
            "order_id",
            "product_id",
            "product_qty",
            "price_unit",
            "date_planned",
        ],
        limit=limit,
    )

    # ------------------------------------------------------------------
    # Normalize Many2one fields
    # ------------------------------------------------------------------
    for r in records:
        if r.get("product_id"):
            r["product_name"] = r["product_id"][1]
            r["product_id"] = r["product_id"][0]

        if r.get("order_id"):
            r["order_id"] = r["order_id"][0]

    return records


#section 6: tol 27 - check material availability
# tools/purchasing/check_material_availability.py

import datetime
from typing import Dict, Any, Optional
from odoo_client import OdooClient, ValidationError


def check_material_availability(
    *,
    product_id: int,
    quantity_needed: float,
    date_needed: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Tool ID: 027
    Model: stock.quant + purchase.order.line (Composite Read)
    Risk: LOW (Read Only)

    Checks if a product can be fulfilled from current stock
    plus incoming approved purchase orders.

    All quantity calculations are performed server-side via read_group
    and search_count — never affected by the 100-record display limit.

    Args:
        product_id:      Product to check (must be active)
        quantity_needed: Required quantity (must be positive)
        date_needed:     Optional — filters incoming POs arriving
                         on or before this date for qty calculation.
                         Expected date always looks beyond this if needed.

    Returns:
        {
            product_id, product_name,
            current_stock,
            incoming_qty,            # server-side sum, always accurate
            total_available,
            quantity_needed,
            can_fulfill,
            shortage,
            expected_available_date  # always accurate, no truncation
        }
    """

    client = OdooClient()

    # ------------------------------------------------------------------
    # Validate inputs
    # ------------------------------------------------------------------
    if not product_id:
        raise ValidationError("product_id is required.")

    if quantity_needed <= 0:
        raise ValidationError("quantity_needed must be positive.")

    if date_needed:
        try:
            datetime.date.fromisoformat(date_needed)
        except ValueError:
            raise ValidationError(
                "date_needed must be in YYYY-MM-DD format."
            )

    # ------------------------------------------------------------------
    # Validate product exists and is active
    # ------------------------------------------------------------------
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
        raise ValidationError(
            f"Product {product_id} does not exist or is archived."
        )

    product_name = product[0]["name"]

    # ------------------------------------------------------------------
    # Current stock — server-side sum via read_group
    # quantity > 0 enforced per safety policy
    # Never truncated — aggregated on server across all locations
    # ------------------------------------------------------------------
    stock_agg = client.read_group(
        model="stock.quant",
        domain=[
            ("product_id", "=", product_id),
            ("location_id.usage", "=", "internal"),
            ("quantity", ">", 0),
        ],
        fields=["quantity:sum", "reserved_quantity:sum"],
        groupby=[],
    )

    total_qty = stock_agg[0].get("quantity", 0.0) or 0.0 if stock_agg else 0.0
    reserved = stock_agg[0].get("reserved_quantity", 0.0) or 0.0 if stock_agg else 0.0
    current_stock = total_qty - reserved

    # ------------------------------------------------------------------
    # Incoming qty — server-side sum via read_group
    # Filtered by date_needed if provided
    # Never truncated — Odoo sums all matching lines on server
    # ------------------------------------------------------------------
    po_domain_filtered = [
        ("product_id", "=", product_id),
        ("order_id.state", "=", "purchase"),
    ]

    if date_needed:
        po_domain_filtered.append(("date_planned", "<=", date_needed))

    incoming_agg = client.read_group(
        model="purchase.order.line",
        domain=po_domain_filtered,
        fields=["product_qty:sum"],
        groupby=[],
    )

    incoming_qty = (
        incoming_agg[0].get("product_qty", 0.0) or 0.0
        if incoming_agg else 0.0
    )

    # ------------------------------------------------------------------
    # Total availability
    # ------------------------------------------------------------------
    total_available = current_stock + incoming_qty
    can_fulfill = total_available >= quantity_needed
    shortage = round(max(quantity_needed - total_available, 0), 2)

    # ------------------------------------------------------------------
    # Expected availability date
    # Uses read_group grouped by date_planned — server-side, no truncation
    # NO date filter here — must look beyond date_needed if needed
    # Walks date groups cumulatively until quantity_needed is reached
    # ------------------------------------------------------------------
    expected_available_date = None

    if not can_fulfill:

        date_groups = client.read_group(
            model="purchase.order.line",
            domain=[
                ("product_id", "=", product_id),
                ("order_id.state", "=", "purchase"),
            ],
            fields=["product_qty:sum", "date_planned"],
            groupby=["date_planned"],
        )

        if date_groups:

            # Normalize and sort by date ascending
            def normalize_date(raw):
                if not raw:
                    return "9999-12-31"
                return str(raw).split(" ")[0].split("T")[0]

            sorted_groups = sorted(
                date_groups,
                key=lambda x: normalize_date(x.get("date_planned")),
            )

            running_total = current_stock

            for group in sorted_groups:
                running_total += group.get("product_qty") or 0

                if running_total >= quantity_needed:
                    raw_date = group.get("date_planned")
                    expected_available_date = normalize_date(raw_date)
                    if expected_available_date == "9999-12-31":
                        expected_available_date = None
                    break

    # ------------------------------------------------------------------
    # Return
    # ------------------------------------------------------------------
    return {
        "product_id": product_id,
        "product_name": product_name,
        "current_stock": round(current_stock, 2),
        "incoming_qty": round(incoming_qty, 2),
        "total_available": round(total_available, 2),
        "quantity_needed": quantity_needed,
        "can_fulfill": can_fulfill,
        "shortage": shortage,
        "expected_available_date": expected_available_date,
    }
