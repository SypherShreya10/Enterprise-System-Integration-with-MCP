from typing import Optional, List, Dict, Any
import logging
from datetime import datetime, date
from odoo_client import OdooClient, ValidationError
from validators import validate_write_payload

logger = logging.getLogger(__name__)
client = OdooClient()


def format_response(data, summary=None, insights=None, meta=None):
    return {
        "data": data,
        "summary": summary or {},
        "insights": insights or [],
        "meta": meta or {}
    }

def wrap_response(data, summary=None, insights=None, model=None):
    return {
        "data": data,
        "summary": summary or {},
        "insights": insights or [],
        "meta": {
            "model": model,
            "record_count": len(data) if isinstance(data, list) else 1
        }
    }

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
        "write_date",       # Last update timestamp
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

        # return records
        insights = []
        if records:
            insights.append(f"Found {len(records)} matching products")
        else:
            insights.append("No matching products found")

        return format_response(
            data=records,
            summary={"count": len(records)},
            insights=insights,
            meta={
                "model": "product.product",
                "record_count": len(records)
            }
        )

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
        "write_date",           # Last update timestamp
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
        # if not records:
        #     logger.info(
        #         f"No stock found for product {product_id} ({product_name})",
        #         extra={"product_id": product_id, "product_name": product_name},
        #     )
            
        #     return {
        #         "product_id": product_id,
        #         "product_name": product_name,
        #         "total_quantity": 0,
        #         "total_reserved": 0,
        #         "total_available": 0,
        #         "locations": [],
        #     }

        if not records:
            logger.info(
                f"No stock found for product {product_id} ({product_name})",
                extra={"product_id": product_id, "product_name": product_name},
            )

            insights = [
                "No stock available for this product in any warehouse",
                "No internal locations contain this product"
            ]

            return format_response(
                data={
                    "product_id": product_id,
                    "product_name": product_name,
                    "locations": []
                },
                summary={
                    "total_quantity": 0,
                    "total_reserved": 0,
                    "total_available": 0
                },
                insights=insights,
                meta={
                    "model": "stock.quant",
                    "record_count": 0
                }
            )

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

        # ------------------------------------------------------------------
        # Insights (Reasoning Hints)
        # ------------------------------------------------------------------

        insights = []

        if total_available > 0:
            insights.append(f"{total_available} units available across warehouses")
        else:
            insights.append("No available stock after reservations")

        if total_reserved > 0:
            insights.append(f"{total_reserved} units are reserved for existing orders")

        if len(locations) > 1:
            insights.append(f"Stock distributed across {len(locations)} locations")

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

        return format_response(
        data={
            "product_id": product_id,
            "product_name": product_name,
            "locations": locations
        },
        summary={
            "total_quantity": total_quantity,
            "total_reserved": total_reserved,
            "total_available": total_available
        },
        insights=insights,
        meta={
            "model": "stock.quant",
            "record_count": len(records)
        }
    )
    

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

        # Consumables and services do not require stock reservation
    if product_type in ["consu", "service"]:

        logger.info(
            f"Product {product_id} ({product_name}) is non-stockable",
            extra={"product_type": product_type},
        )

        recommendation = (
            "Service product — stock availability is not required."
            if product_type == "service"
            else "Consumable product — stock tracking may not apply."
        )

        return wrap_response(
            data={
                "product_id": product_id,
                "product_name": product_name,
                "product_type": product_type,
                "requested_quantity": quantity,
                "date_required": date_required,
                "current_stock": None,
                "current_stock_total": None,
                "current_stock_reserved": None,
                "incoming_quantity": None,
                "can_fulfill": True,
                "shortage": 0.0,
                "recommended_action": recommendation,
            },
            summary={
                "availability_status": "non_stockable",
            },
            insights=[
                recommendation,
            ],
            model="product.product",
        )

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

    insights = []
    next_action = None

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

    # ----------------------------
    # Insights (simple reasoning)
    # ----------------------------

    if can_fulfill:
        insights.append("Enough stock available")
    else:
        insights.append(f"Shortage of {shortage} units")

    if incoming_qty > 0:
        insights.append(f"{incoming_qty} units coming from purchase orders")
    else:
        insights.append("No incoming stock found")

    if total_reserved > 0:
        insights.append(f"{total_reserved} units are reserved")

    if not can_fulfill:
        next_action = "create_purchase_order"


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

    return format_response(
    data={
        "product_id": product_id,
        "product_name": product_name,
        "product_type": product_type,
        "requested_quantity": quantity,
        "date_required": date_required,
        "current_stock": total_available,
        "current_stock_total": total_qty,
        "current_stock_reserved": total_reserved,
        "incoming_quantity": incoming_qty,
    },
    summary={
        "can_fulfill": can_fulfill,
        "shortage": shortage,
        "recommended_action": recommended_action,
    },
    insights=insights,
    meta={
        "model": "stock.quant + purchase.order.line",
        "record_count": len(quants),
        "next_action": next_action
    }
)


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
        "write_date",     # Last update timestamp
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

        insights = []

        if records:
            insights.append(f"{len(records)} internal locations found")
        else:
            insights.append("No internal warehouse locations found")

        return format_response(
            data=records,
            summary={
                "count": len(records)
            },
            insights=insights,
            meta={
                "model": "stock.location",
                "record_count": len(records)
            }
        )

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
        "write_date",
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

    insights = []

    if records:
        insights.append(f"{len(records)} sales orders found")
    else:
        insights.append("No sales orders found")

    states = list(set(r["state"] for r in records)) if records else []

    if states:
        insights.append(f"Orders are in states: {states}")

    return format_response(
    data=records,
    summary={
        "count": len(records),
        "states": states
    },
    insights=insights,
    meta={
        "model": "sale.order",
        "record_count": len(records)
    }
)


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
        "write_date",
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

    insights = []

    total_items = sum(r["product_uom_qty"] for r in records) if records else 0

    if records:
        insights.append(f"{len(records)} line items found")
        insights.append(f"Total quantity across items: {total_items}")
    else:
        insights.append("No line items found for this order")

    return format_response(
    data=records,
    summary={
        "line_count": len(records),
        "total_items": total_items
    },
    insights=insights,
    meta={
        "model": "sale.order.line",
        "record_count": len(records)
    }
)


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
    # Centralized validation layer
    # ------------------------------------------------------------------

    validation = validate_write_payload(
        client=client,
        model_name="sale.order",
        values=values,
        operation="create",
    )

    if not validation["valid"]:
        raise ValidationError(
            "Payload validation failed: "
            + "; ".join(validation["errors"])
        )

    values = validation["cleaned_values"]

    insights = []

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

    # ----------------------------
    # Insights (reasoning hints)
    # ----------------------------

    insights.append("Sales order created in draft state")

    if created["state"] == "draft":
        insights.append("Order requires confirmation before processing")

    if any(line["stock_warning"] for line in line_summary):
        insights.append("Some products have low stock warnings")
    else:
        insights.append("All products have sufficient stock at order time")

    return format_response(
    data={
        "order_id": created["id"],
        "order_name": created["name"],
        "partner_id": partner_id,
        "partner_name": partner_name,
        "lines": line_summary,
    },
    summary={
        "amount_total": created["amount_total"],
        "state": created["state"],
        "date_order": created["date_order"],
        "validity_date": created.get("validity_date"),
    },
    insights=insights,
    meta={
        "model": "sale.order",
        "record_count": 1,
        "operation": "create"
    }
)


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
            "write_date",
        ],
        limit=100,
        order="date_order desc",
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

    # ----------------------------
    # Insights (simple reasoning)
    # ----------------------------

    insights = []

    if total_orders > 0:
        insights.append(f"Customer has {total_orders} total orders")

    if total_orders > 100:
        insights.append("Order list is truncated to latest 100 records")

    if total_revenue > 0:
        insights.append(f"Total revenue from confirmed orders is {round(total_revenue, 2)}")

    if average_order_value > 0:
        insights.append(f"Average order value is {round(average_order_value, 2)}")

    if most_recent_order_date:
        insights.append(f"Most recent order date is {most_recent_order_date}")

    # ------------------------------------------------------------------
    # Return
    # ------------------------------------------------------------------
    return format_response(
    data={
        "partner_id": partner_id,
        "partner_name": partner_name,
        "orders": orders,
    },
    summary={
        "total_orders": total_orders,
        "total_orders_returned": len(orders),
        "truncated": total_orders > 100,
        "total_revenue": round(total_revenue, 2),
        "average_order_value": round(average_order_value, 2),
        "most_recent_order_date": most_recent_order_date,
        "most_recent_active_order_date": most_recent_active_order_date,
        "state_breakdown": state_breakdown,
    },
    insights=insights,
    meta={
        "model": "sale.order",
        "record_count": len(orders)
    }
)

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
            "wrie_date",
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

    insights = []

    if records:
        insights.append(f"{len(records)} purchase orders found")
    else:
        insights.append("No purchase orders found")

    states = list(set(r["state"] for r in records)) if records else []

    if states:
        insights.append(f"Orders are in states: {states}")

    return format_response(
    data=records,
    summary={
        "count": len(records),
        "states": states
    },
    insights=insights,
    meta={
        "model": "purchase.order",
        "record_count": len(records)
    }
)

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
            "write_date",
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

    insights = []

    total_items = sum(r["product_qty"] for r in records) if records else 0

    if records:
        insights.append(f"{len(records)} purchase order lines found")
        insights.append(f"Total quantity ordered: {total_items}")
    else:
        insights.append("No line items found for this purchase order")

    return format_response(
    data=records,
    summary={
        "line_count": len(records),
        "total_items": total_items
    },
    insights=insights,
    meta={
        "model": "purchase.order.line",
        "record_count": len(records)
    }
)


#section 6: tool 27 - check material availability
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

    insights = []
    next_action = None

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

    # ----------------------------
    # Insights (reasoning)
    # ----------------------------

    if can_fulfill:
        insights.append("Sufficient material available to fulfill requirement")
    else:
        insights.append(f"Material shortage of {shortage} units")

    if current_stock > 0:
        insights.append(f"Current stock available: {round(current_stock, 2)}")

    if incoming_qty > 0:
        insights.append(f"Incoming purchase quantity: {round(incoming_qty, 2)}")
    else:
        insights.append("No incoming purchase orders found")

    if expected_available_date:
        insights.append(f"Material expected to be available by {expected_available_date}")

    if not can_fulfill:
        next_action = "create_purchase_order"

    # ------------------------------------------------------------------
    # Return
    # ------------------------------------------------------------------
    return wrap_response(
    data={
        "product_id": product_id,
        "product_name": product_name,
        "current_stock": round(current_stock, 2),
        "incoming_qty": round(incoming_qty, 2),
        "total_available": round(total_available, 2),
        "quantity_needed": quantity_needed,
        "expected_available_date": expected_available_date,
    },
    summary={
        "can_fulfill": can_fulfill,
        "shortage": shortage
    },
    insights=insights,
    model="stock.quant + purchase.order.line"
)

#section 7: tool 28 - get manufacturing order
def get_manufacturing_order(
    *,
    production_id: Optional[int] = None,
    product_id: Optional[int] = None,
    state: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 10,
) -> List[Dict[str, Any]]:

    client = OdooClient()

    if limit > 100:
        raise ValidationError("Limit cannot exceed 100.")

    if production_id:
        limit = 1

    allowed_states = ["draft", "confirmed", "progress", "done", "cancel"]

    if state and state not in allowed_states:
        raise ValidationError(
            f"Invalid state '{state}'. Allowed: {allowed_states}"
        )

    if date_from:
        try:
            datetime.date.fromisoformat(date_from)
        except ValueError:
            raise ValidationError("date_from must be YYYY-MM-DD")

    if date_to:
        try:
            datetime.date.fromisoformat(date_to)
        except ValueError:
            raise ValidationError("date_to must be YYYY-MM-DD")

    if date_from and date_to and date_to < date_from:
        raise ValidationError("date_to cannot be before date_from")

    domain = []

    if production_id:
        domain.append(("id", "=", production_id))

    if product_id:
        domain.append(("product_id", "=", product_id))

    if state:
        domain.append(("state", "=", state))

    if date_from:
        domain.append(("date_start", ">=", date_from))

    if date_to:
        domain.append(("date_start", "<=", date_to))

    if not domain:
        raise ValidationError(
            "At least one filter required."
        )

    records = client.search_read(
        model="mrp.production",
        domain=domain,
        fields=[
            "id",
            "name",
            "product_id",
            "product_qty",
            "qty_produced",
            "date_start",
            "date_finished",
            "state",
            "write_date",
        ],
        limit=limit,
    )

    for r in records:

        if r.get("product_id"):
            r["product_name"] = r["product_id"][1]
            r["product_id"] = r["product_id"][0]

        produced = r.get("qty_produced") or 0
        planned = r.get("product_qty") or 0

        remaining = max(planned - produced, 0)

        r["remaining_qty"] = round(remaining, 2)

    insights = []

    if records:
        insights.append(f"{len(records)} manufacturing orders found")
    else:
        insights.append("No manufacturing orders found")

    states = list(set(r["state"] for r in records)) if records else []

    if states:
        insights.append(f"Orders are in states: {states}")

    in_progress = [r for r in records if r.get("state") == "progress"]

    if in_progress:
        insights.append(f"{len(in_progress)} orders currently in production")

    return wrap_response(
    data=records,
    summary={
        "count": len(records),
        "states": states
    },
    insights=insights,
    model="mrp.production"
)

#section 7: tool 29 - check manufacturing capacity
def check_manufacturing_capacity(
    *,
    date_from: str,
    date_to: str,
    theoretical_capacity: Optional[float] = None,
) -> Dict[str, Any]:

    client = OdooClient()

    try:
        datetime.date.fromisoformat(date_from)
        datetime.date.fromisoformat(date_to)
    except ValueError:
        raise ValidationError("Dates must be YYYY-MM-DD")

    if date_to < date_from:
        raise ValidationError("date_to cannot be before date_from")

    base_domain = [
        ("date_start", ">=", date_from),
        ("date_start", "<=", date_to),
        ("state", "in", ["confirmed", "progress"]),
    ]

    # ------------------------------------------------
    # Aggregate total planned production (server-side)
    # ------------------------------------------------

    agg = client.read_group(
        model="mrp.production",
        domain=base_domain,
        fields=["product_qty:sum"],
        groupby=[],
    )

    total_planned = (
        agg[0].get("product_qty", 0.0)
        if agg else 0.0
    )

    # ------------------------------------------------
    # Accurate order count
    # ------------------------------------------------

    scheduled_orders = client.search_count(
        model="mrp.production",
        domain=base_domain,
    )

    # ------------------------------------------------
    # Capacity calculations
    # ------------------------------------------------

    estimated_capacity_used = None
    available_capacity = None

    insights = []

    if theoretical_capacity:

        if theoretical_capacity <= 0:
            raise ValidationError("theoretical_capacity must be positive")

        estimated_capacity_used = round(
            (total_planned / theoretical_capacity) * 100,
            2
        )

        available_capacity = round(
            max(theoretical_capacity - total_planned, 0),
            2
        )
    
    if scheduled_orders > 0:
        insights.append(f"{scheduled_orders} manufacturing orders scheduled")

    if total_planned > 0:
        insights.append(f"Total planned production: {round(total_planned, 2)} units")

    if theoretical_capacity:
        insights.append(f"Theoretical capacity: {theoretical_capacity}")

        if estimated_capacity_used is not None:
            insights.append(f"Capacity utilization: {estimated_capacity_used}%")

        if available_capacity is not None:
            insights.append(f"Available capacity: {available_capacity}")
    else:
        insights.append("No theoretical capacity provided")

    return wrap_response(
    data={
        "date_range": {
            "from": date_from,
            "to": date_to,
        },
        "scheduled_orders": scheduled_orders,
        "total_scheduled_qty": round(total_planned, 2),
    },
    summary={
        "theoretical_capacity": theoretical_capacity,
        "estimated_capacity_used": estimated_capacity_used,
        "available_capacity": available_capacity,
    },
    insights=insights,
    model="mrp.production"
)

#section 7: tool 30 - get bill of materials
def get_bill_of_materials(
    *,
    product_id: int,
) -> Dict[str, Any]:

    client = OdooClient()

    if not product_id:
        raise ValidationError("product_id is required")

    product = client.search_read(
        model="product.product",
        domain=[
            ("id", "=", product_id),
            ("active", "=", True),
        ],
        fields=["id", "name", "product_tmpl_id"],
        limit=1,
    )

    if not product:
        raise ValidationError(
            f"Product {product_id} does not exist."
        )

    product_name = product[0]["name"]
    template_id = product[0]["product_tmpl_id"][0]

    bom_count = client.search_count(
        model="mrp.bom",
        domain=[
            ("product_tmpl_id", "=", template_id),
            ("type", "=", "normal"),
        ],
    )

    if bom_count == 0:
        return wrap_response(
            data={
                "product_id": product_id,
                "product_name": product_name,
                "bom_line_ids": [],
            },
            summary={
                "bom_id": None,
                "bom_qty": None,
                "multiple_boms": False,
                "components_truncated": False,
            },
            insights=["No bill of materials found for this product"],
            model="mrp.bom"
        )

    bom = client.search_read(
        model="mrp.bom",
        domain=[
            ("product_tmpl_id", "=", template_id),
            ("type", "=", "normal"),
        ],
        fields=["id", "product_qty"],
        limit=1,
    )

    bom_id = bom[0]["id"]
    bom_qty = bom[0].get("product_qty", 1)

    line_count = client.search_count(
        model="mrp.bom.line",
        domain=[("bom_id", "=", bom_id)],
    )

    lines = client.search_read(
        model="mrp.bom.line",
        domain=[("bom_id", "=", bom_id)],
        fields=["product_id", "product_qty"],
        limit=100,
    )

    insights = []
    components = []

    for l in lines:

        comp_id = None
        comp_name = None

        if l.get("product_id"):
            comp_id = l["product_id"][0]
            comp_name = l["product_id"][1]

        qty = l.get("product_qty") or 0

        components.append({
            "component_id": comp_id,
            "component_name": comp_name,
            "product_qty": qty,
            "component_per_unit": round(qty / bom_qty, 6) if bom_qty else None
        })

    if components:
        insights.append(f"{len(components)} components found in BOM")
    else:
        insights.append("No components found in BOM")

    if bom_count > 1:
        insights.append("Multiple BOMs exist for this product")

    if line_count > 100:
        insights.append("Component list truncated to 100 records")

    return wrap_response(
    data={
        "product_id": product_id,
        "product_name": product_name,
        "bom_line_ids": components,
    },
    summary={
        "bom_id": bom_id,
        "bom_qty": bom_qty,
        "multiple_boms": bom_count > 1,
        "components_truncated": line_count > 100,
    },
    insights=insights,
    model="mrp.bom"
)

#section 7: tool 31 - check manufacturing feasibility
def check_manufacturing_feasibility(
    *,
    product_id: int,
    quantity: float,
    date_needed: Optional[str] = None,
    theoretical_capacity: Optional[float] = None,
) -> Dict[str, Any]:

    if not product_id:
        raise ValidationError("product_id is required.")

    if quantity <= 0:
        raise ValidationError("quantity must be positive.")
    
    insights = []

    # ------------------------------------------------
    # STEP 1 — Fetch BOM
    # ------------------------------------------------

    bom_response = get_bill_of_materials(product_id=product_id)

    bom_data = bom_response["data"]
    bom_summary = bom_response["summary"]

    if not bom_summary.get("bom_id"):
        insights.append("No bill of materials defined for this product")

        return wrap_response(
            data={
                "materials": [],
                "blocking_components": [],
            },
            summary={
                "feasible": False,
                "reason": "no_bom_defined",
                "max_producible_quantity": 0,
                "capacity": None,
            },
            insights=insights,
            model="mrp.production"
        )

    components = bom_data.get("bom_line_ids", [])

    material_results = []
    blocking_components = []

    max_producible = float("inf")
    latest_material_date = None

    # ------------------------------------------------
    # STEP 2 — Evaluate each component
    # ------------------------------------------------

    for comp in components:

        comp_id = comp.get("component_id")
        comp_name = comp.get("component_name")

        if not comp_id:
            continue

        per_unit = comp.get("component_per_unit") or 0
        required_qty = round(per_unit * quantity, 2)

        availability_response = check_material_availability(
        product_id=comp_id,
        quantity_needed=required_qty,
        date_needed=date_needed,
    )

        availability_data = availability_response["data"]
        availability_summary = availability_response["summary"]

        available_total = availability_data.get("total_available", 0)

        result = {
        "component_id": comp_id,
        "component_name": comp_name,
        "required_qty": required_qty,
        "available_now": availability_data.get("current_stock", 0),
        "incoming_qty": availability_data.get("incoming_qty", 0),
        "total_available": available_total,
        "can_fulfill": availability_summary.get("can_fulfill", False),
        "shortage": availability_summary.get("shortage", 0),
    }

        material_results.append(result)

        # ------------------------------------------------
        # Bottleneck detection
        # ------------------------------------------------

        if per_unit > 0:
            possible_units = available_total / per_unit
            max_producible = min(max_producible, possible_units)

        if not availability_summary.get("can_fulfill", False):

            expected_date = availability_data.get("expected_available_date")

            blocking_components.append({
                "component_id": comp_id,
                "component_name": comp_name,
                "shortage": availability_summary.get("shortage", 0),
                "expected_available_date": expected_date,
            })

            if expected_date:
                if (
                    latest_material_date is None
                    or expected_date > latest_material_date
                ):
                    latest_material_date = expected_date

    if max_producible == float("inf"):
        max_producible = 0
    else:
        max_producible = int(max_producible)

    # ------------------------------------------------
    # STEP 3 — Material feasibility
    # ------------------------------------------------

    if blocking_components:

        insights.append("Material shortage detected")

        return wrap_response(
            data={
                "materials": material_results,
                "blocking_components": blocking_components,
            },
            summary={
                "feasible": False,
                "reason": "material_shortage",
                "max_producible_quantity": max_producible,
                "materials_ready_date": latest_material_date,
                "capacity": None,
            },
            insights=insights,
            model="mrp.production"
        )

    # ------------------------------------------------
    # STEP 4 — Capacity analysis
    # ------------------------------------------------

    capacity = None

    if date_needed and theoretical_capacity:
        today = date.today()

        required_date = datetime.strptime(
            date_needed,
            "%Y-%m-%d"
        ).date()
    
        capacity_window_start = today.isoformat()
        capacity_window_end = required_date.isoformat()

        capacity_response = check_manufacturing_capacity(
            date_from=capacity_window_start,
            date_to=capacity_window_end,
            theoretical_capacity=theoretical_capacity,
        )

        capacity_data = capacity_response["data"]
        capacity_summary = capacity_response["summary"]

        if capacity_summary.get("available_capacity") is not None:

            if capacity_summary["available_capacity"] < quantity:

                insights.append("Insufficient manufacturing capacity")

                return wrap_response(
                    data={
                        "materials": material_results,
                        "blocking_components": [],
                    },
                    summary={
                        "feasible": False,
                        "reason": "insufficient_capacity",
                        "max_producible_quantity": max_producible,
                        "capacity": capacity_summary,
                    },
                    insights=insights,
                    model="mrp.production"
                )

    # ------------------------------------------------
    # STEP 5 — Success
    # ------------------------------------------------

    insights.append("Manufacturing is feasible")

    return wrap_response(
        data={
            "materials": material_results,
            "blocking_components": [],
        },
        summary={
            "feasible": True,
            "reason": None,
            "max_producible_quantity": max_producible,
            "capacity": capacity,
        },
        insights=insights,
        model="mrp.production"
    )

# section 7: tool 32 - explode bill of materials
def explode_bill_of_materials(
    *,
    product_id: int,
    quantity: float = 1,
    depth: int = 5,
    _bom_cache: Optional[Dict[int, Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:

    if depth <= 0:
        return []

    if _bom_cache is None:
        _bom_cache = {}

    # ------------------------------------------------
    # Fetch BOM (with caching)
    # ------------------------------------------------

    try:

        if product_id in _bom_cache:
            bom_data, bom_summary = _bom_cache[product_id]
        else:
            bom_response = get_bill_of_materials(product_id=product_id)
            bom_data = bom_response["data"]
            bom_summary = bom_response["summary"]
            _bom_cache[product_id] = (bom_data, bom_summary)

    except ValidationError:
        return []

    if not bom_summary.get("bom_id"):
        return []

    exploded_components: Dict[int, Dict[str, Any]] = {}

    # ------------------------------------------------
    # Expand BOM
    # ------------------------------------------------

    for comp in bom_data.get("bom_line_ids", []):

        comp_id = comp.get("component_id")
        comp_name = comp.get("component_name")
        per_unit = comp.get("component_per_unit") or 0

        if not comp_id:
            continue

        required_qty = per_unit * quantity

        # ------------------------------------------------
        # Check if component has its own BOM
        # ------------------------------------------------

        try:

            if comp_id in _bom_cache:
                sub_bom_data, sub_bom_summary = _bom_cache[comp_id]
            else:
                sub_bom_response = get_bill_of_materials(product_id=comp_id)
                sub_bom_data = sub_bom_response["data"]
                sub_bom_summary = sub_bom_response["summary"]
                _bom_cache[comp_id] = (sub_bom_data, sub_bom_summary)

        except ValidationError:
            continue

        if sub_bom_summary.get("bom_id"):

            sub_components = explode_bill_of_materials(
                product_id=comp_id,
                quantity=required_qty,
                depth=depth - 1,
                _bom_cache=_bom_cache,
            )

            for sc in sub_components:

                cid = sc["component_id"]

                if cid not in exploded_components:

                    exploded_components[cid] = {
                        "component_id": cid,
                        "component_name": sc["component_name"],
                        "required_qty": sc["required_qty"],
                    }

                else:

                    exploded_components[cid]["required_qty"] += sc["required_qty"]

        else:

            if comp_id not in exploded_components:

                exploded_components[comp_id] = {
                    "component_id": comp_id,
                    "component_name": comp_name,
                    "required_qty": round(required_qty, 2),
                }

            else:

                exploded_components[comp_id]["required_qty"] += round(required_qty, 2)

    return list(exploded_components.values())


# section 8: tool 33 - get customer invoices
def get_customer_invoices(
    *,
    partner_id: Optional[int] = None,
    move_type: Optional[str] = None,
    payment_state: Optional[str] = None,
    invoice_date_from: Optional[str] = None,
    invoice_date_to: Optional[str] = None,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """
    Tool ID: 033
    Model: account.move
    Risk: LOW (Read Only)

    Returns customer invoices and refunds matching the given filters.

    Safety guarantees:
    - Always restricted to out_invoice and out_refund
    - Cancelled invoices excluded
    - At least one filter required (prevents full table scan)
    - Maximum 100 records per request
    - Company scope enforced at OdooClient level
    """

    client = OdooClient()

    # ----------------------------------------------------------
    # Validate limit
    # ----------------------------------------------------------
    if limit <= 0:
        raise ValidationError("limit must be positive.")

    if limit > 100:
        raise ValidationError("Limit cannot exceed 100.")

    # ----------------------------------------------------------
    # Validate move_type
    # ----------------------------------------------------------
    allowed_move_types = ["out_invoice", "out_refund"]

    if move_type and move_type not in allowed_move_types:
        raise ValidationError(
            f"Invalid move_type '{move_type}'. Allowed: {allowed_move_types}"
        )

    # ----------------------------------------------------------
    # Validate payment_state
    # ----------------------------------------------------------
    allowed_payment_states = [
        "not_paid",
        "in_payment",
        "paid",
        "partial",
        "reversed",
    ]

    if payment_state and payment_state not in allowed_payment_states:
        raise ValidationError(
            f"Invalid payment_state '{payment_state}'. "
            f"Allowed: {allowed_payment_states}"
        )

    # ----------------------------------------------------------
    # Validate date formats
    # ----------------------------------------------------------
    if invoice_date_from:
        try:
            datetime.date.fromisoformat(invoice_date_from)
        except ValueError:
            raise ValidationError(
                "invoice_date_from must be in YYYY-MM-DD format."
            )

    if invoice_date_to:
        try:
            datetime.date.fromisoformat(invoice_date_to)
        except ValueError:
            raise ValidationError(
                "invoice_date_to must be in YYYY-MM-DD format."
            )

    if invoice_date_from and invoice_date_to and invoice_date_to < invoice_date_from:
        raise ValidationError(
            "invoice_date_to cannot be before invoice_date_from."
        )

    # ----------------------------------------------------------
    # Require at least one filter (prevents full table scan)
    # ----------------------------------------------------------
    if not any([
        partner_id,
        move_type,
        payment_state,
        invoice_date_from,
        invoice_date_to,
    ]):
        raise ValidationError(
            "At least one filter is required."
        )

    # ----------------------------------------------------------
    # Build domain
    # Base domain always enforces safety restrictions
    # ----------------------------------------------------------
    domain = [
        ("state", "!=", "cancel"),
        ("move_type", "in", ["out_invoice", "out_refund"]),
    ]

    if partner_id:
        domain.append(("partner_id", "=", partner_id))

    if move_type:
        domain.append(("move_type", "=", move_type))

    if payment_state:
        domain.append(("payment_state", "=", payment_state))

    if invoice_date_from:
        domain.append(("invoice_date", ">=", invoice_date_from))

    if invoice_date_to:
        domain.append(("invoice_date", "<=", invoice_date_to))

    # ----------------------------------------------------------
    # Execute query
    # ----------------------------------------------------------
    records = client.search_read(
        model="account.move",
        domain=domain,
        fields=[
            "id",
            "name",
            "move_type",
            "partner_id",
            "invoice_date",
            "invoice_date_due",
            "amount_total",
            "amount_residual",
            "payment_state",
            "state",
            "write_date",
        ],
        limit=limit,
    )

    # ----------------------------------------------------------
    # Normalize Many2one fields
    # ----------------------------------------------------------
    for r in records:
        if r.get("partner_id"):
            r["partner_name"] = r["partner_id"][1]
            r["partner_id"] = r["partner_id"][0]

    insights = []

    if records:
        insights.append(f"{len(records)} invoices found")
    else:
        insights.append("No invoices found")

    states = list(set(r["state"] for r in records)) if records else []
    if states:
        insights.append(f"Invoices in states: {states}")

    payment_states = list(set(r["payment_state"] for r in records)) if records else []
    if payment_states:
        insights.append(f"Payment states observed: {payment_states}")

    return wrap_response(
    data=records,
    summary={
        "count": len(records),
        "states": states,
        "payment_states": payment_states,
    },
    insights=insights,
    model="account.move"
)


# section 8: tool 34 - check customer credit
def check_customer_credit(
    *,
    partner_id: int,
) -> Dict[str, Any]:
    """
    Tool ID: 034
    Model: res.partner + account.move (Composite Read)
    Risk: LOW (Read Only)

    Returns credit status for a customer.

    Financial aggregations are server-side — no truncation possible.

    total_due includes:
        - not_paid
        - partial

    Excludes:
        - in_payment (payment already in transit)

    Returns:
        {
            partner_id,
            partner_name,
            credit_limit,
            total_due,
            available_credit,
            can_extend_credit,
            credit_status,
            overdue_invoices: {
                count,
                total_amount,
                oldest_due_date
            },
            total_due_note
        }
    """

    client = OdooClient()

    # ----------------------------------------------------------
    # Validate partner_id
    # ----------------------------------------------------------
    if not isinstance(partner_id, int) or partner_id <= 0:
        raise ValidationError("partner_id must be a positive integer.")

    # ----------------------------------------------------------
    # Validate customer exists
    # ----------------------------------------------------------
    partner = client.search_read(
        model="res.partner",
        domain=[
            ("id", "=", partner_id),
            ("customer_rank", ">", 0),
        ],
        fields=[
            "id",
            "name",
            "credit_limit",
        ],
        limit=1,
    )

    if not partner:
        raise ValidationError(
            f"Customer {partner_id} does not exist or is not a customer."
        )

    partner_name = partner[0]["name"]

    # Treat False / 0 as "no credit limit configured"
    credit_limit = partner[0].get("credit_limit") or None
    if credit_limit == 0:
        credit_limit = None

    # ----------------------------------------------------------
    # Base invoice domain for unpaid invoices
    # ----------------------------------------------------------
    unpaid_domain = [
        ("partner_id", "=", partner_id),
        ("move_type", "=", "out_invoice"),
        ("state", "=", "posted"),
        ("payment_state", "in", ["not_paid", "partial"]),
    ]

    # ----------------------------------------------------------
    # Total outstanding balance (server-side aggregation)
    # ----------------------------------------------------------
    due_agg = client.read_group(
        model="account.move",
        domain=unpaid_domain,
        fields=["amount_residual:sum"],
        groupby=[],
    )

    total_due = (
        due_agg[0].get("amount_residual", 0.0)
        if due_agg else 0.0
    )

    # ----------------------------------------------------------
    # Overdue invoices
    # ----------------------------------------------------------
    today = datetime.date.today().isoformat()

    overdue_domain = unpaid_domain + [
        ("invoice_date_due", "<", today)
    ]

    overdue_agg = client.read_group(
        model="account.move",
        domain=overdue_domain,
        fields=["amount_residual:sum"],
        groupby=[],
    )

    overdue_total = (
        overdue_agg[0].get("amount_residual", 0.0)
        if overdue_agg else 0.0
    )

    overdue_count = client.search_count(
        model="account.move",
        domain=overdue_domain,
    )

    # ----------------------------------------------------------
    # Oldest overdue invoice
    # ----------------------------------------------------------
    oldest_due_date = None

    if overdue_count > 0:

        oldest = client.search_read(
            model="account.move",
            domain=overdue_domain,
            fields=["invoice_date_due"],
            limit=1,
            order="invoice_date_due asc",
        )

        if oldest:
            oldest_due_date = oldest[0].get("invoice_date_due")

    # ----------------------------------------------------------
    # Credit calculations
    # ----------------------------------------------------------
    available_credit = None
    can_extend_credit = None

    if credit_limit is not None:

        available_credit = round(
            max(credit_limit - total_due, 0),
            2
        )

        can_extend_credit = total_due <= credit_limit

    # ----------------------------------------------------------
    # Credit status classification
    # ----------------------------------------------------------
    if credit_limit is None:
        credit_status = "no_limit_configured"

    elif overdue_count > 0:
        credit_status = "overdue"

    elif total_due > credit_limit:
        credit_status = "over_limit"

    elif credit_limit > 0 and available_credit < credit_limit * 0.1:
        credit_status = "near_limit"

    else:
        credit_status = "good_standing"

    insights = []

    if credit_limit is None:
        insights.append("Customer has no credit limit configured")

    if total_due > 0:
        insights.append(f"Customer has outstanding balance of {round(total_due, 2)}")

    if overdue_count > 0:
        insights.append(f"{overdue_count} overdue invoices detected")

    if available_credit is not None:
        insights.append(f"Available credit: {available_credit}")

    insights.append(f"Credit status classified as '{credit_status}'")

    # ----------------------------------------------------------
    # Return structured result
    # ----------------------------------------------------------
    return wrap_response(
    data={
        "partner_id": partner_id,
        "partner_name": partner_name,
        "overdue_invoices": {
            "count": overdue_count,
            "total_amount": round(overdue_total, 2),
            "oldest_due_date": oldest_due_date,
        },
    },
    summary={
        "credit_limit": credit_limit,
        "total_due": round(total_due, 2),
        "available_credit": available_credit,
        "can_extend_credit": can_extend_credit,
        "credit_status": credit_status,
        "total_due_note": (
            "Includes not_paid and partial invoices only. "
            "Excludes in_payment (payment already in transit)."
        ),
    },
    insights=insights,
    model="res.partner + account.move"
)


# section 8: tool 35 - get payment history
def get_payment_history(
    *,
    partner_id: int,
    limit: int = 50,
) -> Dict[str, Any]:
    """
    Tool ID: 035
    Model: account.move (paid invoices only)
    Risk: LOW (Read Only)

    Returns paid invoice history for a customer as a proxy for
    payment behavior.

    IMPORTANT — What 'payment_terms_days' actually measures:
        invoice_date_due - invoice_date = payment terms length.
        This reflects agreed payment terms, NOT actual lateness.

    Actual payment date is not stored directly on account.move.

    Summary analytics are server-side (always accurate regardless of limit).
    Display list is paginated (max 100, truncated flag included).
    """

    client = OdooClient()

    # ----------------------------------------------------------
    # Validate parameters
    # ----------------------------------------------------------
    if not isinstance(partner_id, int) or partner_id <= 0:
        raise ValidationError("partner_id must be a positive integer.")

    if limit <= 0:
        raise ValidationError("limit must be positive.")

    if limit > 100:
        raise ValidationError("Limit cannot exceed 100.")

    # ----------------------------------------------------------
    # Validate customer exists
    # ----------------------------------------------------------
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
            f"Customer {partner_id} does not exist or is not a customer."
        )

    partner_name = partner[0]["name"]

    # ----------------------------------------------------------
    # Base domain for paid invoices
    # ----------------------------------------------------------
    paid_domain = [
        ("partner_id", "=", partner_id),
        ("move_type", "=", "out_invoice"),
        ("state", "=", "posted"),
        ("payment_state", "=", "paid"),
    ]

    # ----------------------------------------------------------
    # Server-side aggregation (always accurate)
    # ----------------------------------------------------------
    summary_agg = client.read_group(
        model="account.move",
        domain=paid_domain,
        fields=["amount_total:sum"],
        groupby=[],
    )

    total_paid_amount = (
        summary_agg[0].get("amount_total", 0.0)
        if summary_agg else 0.0
    )

    total_paid_count = (
        summary_agg[0].get("__count", 0)
        if summary_agg else 0
    )

    # ----------------------------------------------------------
    # Paginated invoice list
    # ----------------------------------------------------------
    invoices = client.search_read(
        model="account.move",
        domain=paid_domain,
        fields=[
            "id",
            "name",
            "invoice_date",
            "invoice_date_due",
            "amount_total",
        ],
        limit=limit,
        order="invoice_date desc",
    )

    payment_records: List[Dict[str, Any]] = []
    terms_days_list: List[int] = []

    for inv in invoices:

        invoice_date = inv.get("invoice_date")
        due_date = inv.get("invoice_date_due")

        payment_terms_days = None

        if invoice_date and due_date:
            try:
                d1 = datetime.date.fromisoformat(str(invoice_date))
                d2 = datetime.date.fromisoformat(str(due_date))

                payment_terms_days = (d2 - d1).days
                terms_days_list.append(payment_terms_days)

            except Exception:
                pass

        payment_records.append({
            "invoice_id": inv["id"],
            "invoice_number": inv["name"],
            "invoice_date": invoice_date,
            "invoice_date_due": due_date,
            "amount": float(inv.get("amount_total") or 0.0),
            "payment_terms_days": payment_terms_days,
        })

    # ----------------------------------------------------------
    # Average payment terms
    # ----------------------------------------------------------
    average_payment_terms_days = (
        round(sum(terms_days_list) / len(terms_days_list), 2)
        if terms_days_list else None
    )

    # ----------------------------------------------------------
    # Payment profile classification
    # ----------------------------------------------------------
    if total_paid_count == 0:
        payment_profile = "no_payment_history"

    elif total_paid_count >= 10:
        payment_profile = "established_customer"

    elif total_paid_count >= 3:
        payment_profile = "active_customer"

    else:
        payment_profile = "new_customer"

    insights = []

    if total_paid_count > 0:
        insights.append(f"{total_paid_count} paid invoices found")

    if total_paid_amount > 0:
        insights.append(f"Total paid amount is {round(total_paid_amount, 2)}")

    if average_payment_terms_days is not None:
        insights.append(f"Average payment terms: {average_payment_terms_days} days")

    insights.append(f"Customer classified as '{payment_profile}'")

    if total_paid_count > limit:
        insights.append("Displayed results are truncated to limit")

    # ----------------------------------------------------------
    # Final result
    # ----------------------------------------------------------
    return wrap_response(
    data={
        "partner_id": partner_id,
        "partner_name": partner_name,
        "payments": payment_records,
    },
    summary={
        "total_paid_invoices": total_paid_count,
        "total_paid_amount": round(total_paid_amount, 2),
        "total_returned": len(payment_records),
        "truncated": total_paid_count > limit,
        "average_payment_terms_days": average_payment_terms_days,
        "payment_profile": payment_profile,
        "data_note": (
            "payment_terms_days = invoice_date_due minus invoice_date. "
            "This reflects agreed payment terms, not actual lateness. "
            "Actual payment date is not stored on account.move."
        ),
    },
    insights=insights,
    model="account.move"
)

# section 9: tool 36 - check order fulfillment feasibility
def check_order_fulfillment_feasibility(
    *,
    partner_id: int,
    product_id: int,
    quantity: float,
    date_required: str,
) -> Dict[str, Any]:

    client = OdooClient()

    # ------------------------------------------------
    # INPUT VALIDATION
    # ------------------------------------------------

    if not partner_id:
        raise ValidationError("partner_id is required.")

    if not product_id:
        raise ValidationError("product_id is required.")

    if quantity <= 0:
        raise ValidationError("quantity must be positive.")

    try:
        required_date = datetime.date.fromisoformat(date_required)
    except ValueError:
        raise ValidationError("date_required must be YYYY-MM-DD.")

    today = datetime.date.today()

    if required_date < today:
        raise ValidationError("date_required cannot be in the past.")

    # ------------------------------------------------
    # VALIDATE CUSTOMER
    # ------------------------------------------------

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
            f"Customer {partner_id} does not exist or is not a customer."
        )

    partner_name = partner[0]["name"]

    # ------------------------------------------------
    # VALIDATE PRODUCT
    # ------------------------------------------------

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
            f"Product {product_id} does not exist or is inactive."
        )

    product_name = product[0]["name"]

    # ------------------------------------------------
    # CUSTOMER CREDIT ANALYSIS
    # ------------------------------------------------

    credit_response = check_customer_credit(partner_id=partner_id)

    credit_data = credit_response["data"]
    credit_summary = credit_response["summary"]

    credit_status = credit_summary.get("credit_status")

    credit_approved = credit_status in [
        "good_standing",
        "no_limit_configured",
    ]

    customer_analysis = {
        "partner_id": partner_id,
        "partner_name": partner_name,
        "credit_limit": credit_summary.get("credit_limit"),
        "available_credit": credit_summary.get("available_credit"),
        "credit_status": credit_status,
        "credit_approved": credit_approved,
        "overdue_invoices": credit_data.get("overdue_invoices"),
    }

    # ------------------------------------------------
    # INVENTORY ANALYSIS
    # ------------------------------------------------

    stock_response = check_material_availability(
    product_id=product_id,
    quantity_needed=quantity,
    date_needed=date_required,
)

    stock_data = stock_response["data"]
    stock_summary = stock_response["summary"]

    can_ship_from_stock = stock_summary.get("can_fulfill", False)

    inventory_analysis = {
        "current_stock": stock_data.get("current_stock"),
        "incoming_qty": stock_data.get("incoming_qty"),
        "total_available": stock_data.get("total_available"),
        "can_ship_from_stock": can_ship_from_stock,
        "shortage_qty": stock_summary.get("shortage"),
        "expected_available_date": stock_data.get("expected_available_date"),
    }

    # ------------------------------------------------
    # MANUFACTURING ANALYSIS (Tool 31)
    # ------------------------------------------------

    manufacturing_analysis = None

    if not can_ship_from_stock:

        manufacturing_response = check_manufacturing_feasibility(
        product_id=product_id,
        quantity=quantity,
        date_needed=date_required,
    )

    manufacturing_data = manufacturing_response["data"]
    manufacturing_summary = manufacturing_response["summary"]

    manufacturing_analysis = {
        "materials": manufacturing_data.get("materials"),
        "blocking_components": manufacturing_data.get("blocking_components"),
        "feasible": manufacturing_summary.get("feasible"),
        "max_producible_quantity": manufacturing_summary.get("max_producible_quantity"),
        "capacity": manufacturing_summary.get("capacity"),
    }

    # ------------------------------------------------
    # RESOURCE ANALYSIS
    # ------------------------------------------------

    dept = client.search_read(
        model="hr.department",
        domain=[("name", "ilike", "manufactur")],
        fields=["id"],
        limit=1,
    )

    dept_id = dept[0]["id"] if dept else None

    staff_count = 0

    if dept_id:

        staff_count = client.search_count(
            model="hr.employee",
            domain=[
                ("active", "=", True),
                ("department_id", "=", dept_id),
            ],
        )

    resource_analysis = {
        "manufacturing_staff_headcount": staff_count
    }

    # ------------------------------------------------
    # DECISION LOGIC
    # ------------------------------------------------

    risks: List[str] = []
    action_items: List[str] = []

    if not credit_approved:
        risks.append("Customer credit not approved.")
        action_items.append("Resolve credit issue before confirming order.")

    if can_ship_from_stock and credit_approved:

        can_fulfill = True
        confidence = "high"

        recommended_date = (
            today + datetime.timedelta(days=2)
        ).isoformat()

        action_items.append("Reserve stock and ship order.")

    elif manufacturing_summary.get("feasible") and credit_approved:

        can_fulfill = True
        confidence = "medium"

        recommended_date = date_required

        action_items.append("Create manufacturing order.")

    else:

        can_fulfill = False
        confidence = "low"

        recommended_date = None

        risks.append("Order cannot be fulfilled with current resources.")

    insights = []

    if not credit_approved:
        insights.append("Customer credit is not approved")

    if can_ship_from_stock:
        insights.append("Order can be fulfilled from current stock")

    elif manufacturing_analysis and manufacturing_summary.get("feasible"):
        insights.append("Order can be fulfilled via manufacturing")

    else:
        insights.append("Order cannot be fulfilled with current conditions")

    insights.append(f"Confidence level: {confidence}")

    # ------------------------------------------------
    # FINAL RESPONSE
    # ------------------------------------------------

    return wrap_response(
    data={
        "request": {
            "partner_id": partner_id,
            "partner_name": partner_name,
            "product_id": product_id,
            "product_name": product_name,
            "quantity": quantity,
            "date_required": date_required,
        },
        "customer_analysis": customer_analysis,
        "inventory_analysis": inventory_analysis,
        "manufacturing_analysis": manufacturing_analysis,
        "resource_analysis": resource_analysis,
    },
    summary={
        "can_fulfill": can_fulfill,
        "confidence_level": confidence,
        "recommended_delivery_date": recommended_date,
        "risks": risks,
        "action_items": action_items,
    },
    insights=insights,
    model="composite.order.fulfillment"
)

# section 9: tool 37 - analyze customer relationship
def analyze_customer_relationship(
    *,
    partner_id: int,
) -> Dict[str, Any]:

    client = OdooClient()

    if not partner_id:
        raise ValidationError("partner_id is required.")

    # ------------------------------------------------
    # CUSTOMER PROFILE
    # ------------------------------------------------

    partner = client.search_read(
        model="res.partner",
        domain=[
            ("id", "=", partner_id),
            ("customer_rank", ">", 0),
        ],
        fields=["id", "name", "email", "phone"],
        limit=1,
    )

    if not partner:
        raise ValidationError(
            f"Customer {partner_id} does not exist."
        )

    partner = partner[0]

    partner_name = partner["name"]

    # ------------------------------------------------
    # SALES ANALYSIS
    # ------------------------------------------------

    sales = client.read_group(
        model="sale.order",
        domain=[
            ("partner_id", "=", partner_id),
            ("state", "in", ["sale", "done"]),
        ],
        fields=["amount_total:sum"],
        groupby=[],
    )

    lifetime_value = (
        sales[0].get("amount_total", 0.0) if sales else 0.0
    )

    order_count = client.search_count(
        model="sale.order",
        domain=[
            ("partner_id", "=", partner_id),
            ("state", "in", ["sale", "done"]),
        ],
    )

    # ------------------------------------------------
    # CRM OPPORTUNITIES
    # ------------------------------------------------

    opportunities = client.read_group(
        model="crm.lead",
        domain=[
            ("partner_id", "=", partner_id),
            ("type", "=", "opportunity"),
            ("probability", "<", 100),
        ],
        fields=["expected_revenue:sum"],
        groupby=[],
    )

    open_opportunity_value = (
        opportunities[0].get("expected_revenue", 0.0)
        if opportunities else 0.0
    )

    open_opportunity_count = client.search_count(
        model="crm.lead",
        domain=[
            ("partner_id", "=", partner_id),
            ("type", "=", "opportunity"),
            ("probability", "<", 100),
        ],
    )

    # ------------------------------------------------
    # PAYMENT BEHAVIOR
    # ------------------------------------------------

    invoices_response = get_payment_history(partner_id=partner_id)

    payment_data = invoices_response["data"]
    payment_summary = invoices_response["summary"]

    credit_response = check_customer_credit(partner_id=partner_id)

    credit_data = credit_response["data"]
    credit_summary = credit_response["summary"]

    overdue_count = credit_data.get("overdue_invoices", {}).get("count", 0)

    # ------------------------------------------------
    # RELATIONSHIP SCORE
    # ------------------------------------------------

    if lifetime_value > 100000 and overdue_count == 0:
        score = "excellent"
    elif lifetime_value > 20000:
        score = "good"
    elif lifetime_value > 0:
        score = "fair"
    else:
        score = "poor"

    # ------------------------------------------------
    # RECOMMENDATIONS
    # ------------------------------------------------

    actions: List[str] = []

    if score == "excellent":
        actions.append("Consider loyalty rewards or strategic partnership.")

    elif score == "good":
        actions.append("Maintain engagement and explore upsell opportunities.")

    elif score == "fair":
        actions.append("Increase engagement and monitor payment behavior.")

    else:
        actions.append("Evaluate credit risk before new orders.")


    insights = []

    insights.append(f"Customer lifetime value: {round(lifetime_value, 2)}")

    if order_count > 0:
        insights.append(f"{order_count} completed sales orders")

    if open_opportunity_count > 0:
        insights.append(f"{open_opportunity_count} active opportunities")

    if overdue_count > 0:
        insights.append(f"{overdue_count} overdue invoices detected")

    insights.append(f"Relationship classified as '{score}'")


    # ------------------------------------------------
    # RESPONSE
    # ------------------------------------------------

    return wrap_response(
    data={
        "customer_profile": {
            "partner_id": partner_id,
            "partner_name": partner_name,
            "email": partner.get("email"),
            "phone": partner.get("phone"),
        },
        "sales_summary": {
            "lifetime_value": round(lifetime_value, 2),
            "total_orders": order_count,
        },
        "crm_opportunities": {
            "open_opportunity_count": open_opportunity_count,
            "open_opportunity_value": round(open_opportunity_value, 2),
        },
        "payment_behavior": payment_summary,
    },
    summary={
        "relationship_health": score,
        "recommended_actions": actions,
    },
    insights=insights,
    model="composite.customer.relationship"
)

# tool 38 - evaluate purchase order
# tool 38 - evaluate purchase order
def evaluate_purchase_order(
    *,
    order_id: int,
) -> Dict[str, Any]:

    client = OdooClient()

    if not order_id:
        raise ValidationError("order_id is required")

    # ------------------------------------------------
    # STEP 1 — Fetch PO
    # ------------------------------------------------

    po = client.search_read(
        model="purchase.order",
        domain=[("id", "=", order_id)],
        fields=[
            "id",
            "name",
            "amount_total",
            "partner_id",
            "state",
        ],
        limit=1,
    )

    if not po:
        raise ValidationError(f"Purchase Order {order_id} not found")

    po = po[0]
    amount = po.get("amount_total") or 0

    # ------------------------------------------------
    # STEP 2 — Fetch PO Lines
    # ------------------------------------------------

    lines_response = get_purchase_order_lines(order_id=order_id)
    lines = lines_response.get("data", [])

    material_analysis = []
    unnecessary_items = []
    shortage_items = []

    # ------------------------------------------------
    # STEP 3 — Check Material Need
    # ------------------------------------------------

    for line in lines:

        product_id = line.get("product_id")
        qty = line.get("product_qty")

        if not product_id or not qty:
            continue

        availability = check_material_availability(
            product_id=product_id,
            quantity_needed=qty,
        )

        data = availability.get("data", {})
        summary = availability.get("summary", {})

        can_fulfill = summary.get("can_fulfill", False)
        shortage = summary.get("shortage", 0)

        material_analysis.append({
            "product_id": product_id,
            "product_name": line.get("product_name"),
            "required_qty": qty,
            "available": data.get("current_stock"),
            "incoming": data.get("incoming_qty"),
            "can_fulfill": can_fulfill,
            "shortage": shortage,
        })

        if can_fulfill:
            unnecessary_items.append(line.get("product_name"))
        else:
            shortage_items.append(line.get("product_name"))

    # ------------------------------------------------
    # STEP 4 — Fetch Policy
    # ------------------------------------------------

    company = client.search_read(
        model="res.company",
        domain=[("id", "=", client.company_id)],
        fields=[
            "po_double_validation",
            "po_double_validation_amount"
        ],
        limit=1,
    )

    validation_type = company[0].get("po_double_validation") if company else None
    threshold = company[0].get("po_double_validation_amount") if company else 0

    # ------------------------------------------------
    # STEP 5 — Evaluate Conditions
    # ------------------------------------------------

    conditions = []

    # Policy
    if validation_type == "one_step":
        conditions.append("Company policy does not require approval.")
        policy_ok = True
    else:
        if amount <= threshold:
            conditions.append(f"Amount {amount} is within threshold {threshold}.")
            policy_ok = True
        else:
            conditions.append(f"Amount {amount} exceeds threshold {threshold}.")
            policy_ok = False

    # State
    if po.get("state") not in ["draft", "sent"]:
        conditions.append(f"PO is in '{po.get('state')}' state and cannot be approved.")
        state_ok = False
    else:
        conditions.append("PO is in approvable state.")
        state_ok = True

    # Material necessity
    if unnecessary_items:
        conditions.append(
            f"Some items already available in stock: {', '.join(unnecessary_items)}"
        )

    if shortage_items:
        conditions.append(
            f"Shortage detected for: {', '.join(shortage_items)}"
        )

    # ------------------------------------------------
    # STEP 6 — Final Decision (ONLY SUGGESTION)
    # ------------------------------------------------

    can_be_approved = policy_ok and state_ok

    if shortage_items:
        recommendation = "PO is justified due to material shortage. User may approve."
    elif unnecessary_items:
        recommendation = "PO may not be necessary. Review before approving."
    else:
        recommendation = "Review required before approval."

    # ------------------------------------------------
    # FINAL RESPONSE
    # ------------------------------------------------

    return {
        "order_id": order_id,
        "order_name": po.get("name"),
        "amount": amount,
        "can_be_approved": can_be_approved,
        "material_analysis": material_analysis,
        "conditions": conditions,
        "recommendation": recommendation,
    }