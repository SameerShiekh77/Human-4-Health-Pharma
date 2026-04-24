from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from decimal import Decimal, InvalidOperation
from typing import Any, Callable

from crm_products.models import Division, ProductMaster, BatchManagement, CompanyStock
from crm_sales.models import Region, Area, MedicalRepresentative
from crm_doctors.models import Doctor, DoctorPracticeLocation, DoctorVisit
from crm_distributors.models import Distributor, DistributorStockEntry, DistributorSalesValue
from crm_stores.models import MedicalStore, StoreProductTracking


@dataclass(frozen=True)
class ExportColumn:
    header: str
    getter: Callable[[Any], Any]


@dataclass(frozen=True)
class ImportColumn:
    header: str
    field_name: str | None = None
    kind: str = 'text'
    required: bool = False
    lookup_model: Any = None
    lookup_field: str = 'name'
    choices: list[tuple[str, str]] | None = None
    many: bool = False
    delimiter: str = ';'
    default: Any = ''
    create_if_missing: bool = False
    create_defaults: dict[str, Any] | None = None


class ImportErrorRow(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def export_text(header: str, getter: Callable[[Any], Any]) -> ExportColumn:
    return ExportColumn(header=header, getter=getter)


def import_text(
    header: str,
    field_name: str,
    required: bool = False,
    default: Any = '',
) -> ImportColumn:
    return ImportColumn(header=header, field_name=field_name, kind='text', required=required, default=default)


def import_int(header: str, field_name: str, required: bool = False, default: Any = 0) -> ImportColumn:
    return ImportColumn(header=header, field_name=field_name, kind='int', required=required, default=default)


def import_decimal(header: str, field_name: str, required: bool = False, default: Any = Decimal('0.00')) -> ImportColumn:
    return ImportColumn(header=header, field_name=field_name, kind='decimal', required=required, default=default)


def import_date(header: str, field_name: str, required: bool = False) -> ImportColumn:
    return ImportColumn(header=header, field_name=field_name, kind='date', required=required)


def import_time(header: str, field_name: str, required: bool = False) -> ImportColumn:
    return ImportColumn(header=header, field_name=field_name, kind='time', required=required)


def import_bool(header: str, field_name: str, required: bool = False, default: Any = True) -> ImportColumn:
    return ImportColumn(header=header, field_name=field_name, kind='bool', required=required, default=default)


def import_choice(
    header: str,
    field_name: str,
    choices: list[tuple[str, str]],
    required: bool = False,
    default: Any = '',
) -> ImportColumn:
    return ImportColumn(header=header, field_name=field_name, kind='choice', required=required, choices=choices, default=default)


def import_fk(
    header: str,
    field_name: str,
    lookup_model: Any,
    lookup_field: str = 'name',
    required: bool = False,
    default: Any = None,
    create_if_missing: bool = False,
    create_defaults: dict[str, Any] | None = None,
) -> ImportColumn:
    return ImportColumn(
        header=header,
        field_name=field_name,
        kind='fk',
        required=required,
        lookup_model=lookup_model,
        lookup_field=lookup_field,
        default=default,
        create_if_missing=create_if_missing,
        create_defaults=create_defaults or {},
    )


def import_m2m(
    header: str,
    field_name: str,
    lookup_model: Any,
    lookup_field: str = 'name',
    required: bool = False,
) -> ImportColumn:
    return ImportColumn(
        header=header,
        field_name=field_name,
        kind='m2m',
        required=required,
        lookup_model=lookup_model,
        lookup_field=lookup_field,
        many=True,
    )


def _choice_label_map(choices: list[tuple[str, str]] | None) -> dict[str, str]:
    mapping: dict[str, str] = {}
    if not choices:
        return mapping
    for key, label in choices:
        mapping[str(key).strip().lower()] = key
        mapping[str(label).strip().lower()] = key
    return mapping


def _parse_bool(value: Any) -> bool:
    text = str(value).strip().lower()
    return text in {'1', 'true', 'yes', 'y', 'active', 'on'}


def _parse_decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        raise ImportErrorRow(f'Invalid decimal value: {value}')


def _parse_int(value: Any) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        raise ImportErrorRow(f'Invalid integer value: {value}')


def _parse_date(value: Any) -> date:
    text = str(value).strip()
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y'):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise ImportErrorRow(f'Invalid date value: {value} (expected YYYY-MM-DD)')


def _parse_time(value: Any) -> time:
    text = str(value).strip()
    for fmt in ('%H:%M:%S', '%H:%M'):
        try:
            return datetime.strptime(text, fmt).time()
        except ValueError:
            continue
    raise ImportErrorRow(f'Invalid time value: {value} (expected HH:MM or HH:MM:SS)')


def _parse_choice(value: Any, choices: list[tuple[str, str]] | None) -> str:
    value_text = str(value).strip().lower()
    mapping = _choice_label_map(choices)
    if value_text in mapping:
        return mapping[value_text]
    valid = ', '.join([f'{k} / {label}' for k, label in (choices or [])])
    raise ImportErrorRow(f'Invalid choice: {value}. Valid values: {valid}')


def _resolve_fk(column: ImportColumn, raw_value: Any):
    if raw_value in (None, ''):
        if column.required:
            raise ImportErrorRow(f'{column.header} is required')
        return None

    lookup_value = str(raw_value).strip()
    query = {column.lookup_field: lookup_value}
    obj = column.lookup_model.objects.filter(**query).first()
    if obj:
        return obj

    if column.create_if_missing:
        defaults = dict(column.create_defaults or {})
        defaults.setdefault(column.lookup_field, lookup_value)
        return column.lookup_model.objects.create(**defaults)

    raise ImportErrorRow(f'Could not find related {column.lookup_model.__name__} for {column.header}: {lookup_value}')


def _resolve_m2m(column: ImportColumn, raw_value: Any):
    if raw_value in (None, ''):
        return []
    values = [part.strip() for part in str(raw_value).split(column.delimiter) if part.strip()]
    results = []
    missing = []
    for value in values:
        obj = column.lookup_model.objects.filter(**{column.lookup_field: value}).first()
        if obj:
            results.append(obj)
        else:
            missing.append(value)
    if missing:
        raise ImportErrorRow(
            f'Could not find related {column.lookup_model.__name__}(s) for {column.header}: {", ".join(missing)}'
        )
    return results


def export_value(column: ExportColumn, obj: Any) -> str:
    value = column.getter(obj)
    if value is None:
        return ''
    if isinstance(value, bool):
        return 'Yes' if value else 'No'
    if isinstance(value, (date, time, datetime)):
        return value.isoformat()
    return str(value)


def parse_row(columns: list[ImportColumn], row: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    cleaned: dict[str, Any] = {}
    errors: list[str] = []

    for column in columns:
        raw_value = row.get(column.header, '')
        if isinstance(raw_value, str):
            raw_value = raw_value.strip()

        if raw_value in (None, ''):
            if column.required:
                errors.append(f'{column.header} is required')
            else:
                cleaned[column.field_name or column.header] = column.default
            continue

        try:
            if column.kind == 'text':
                cleaned[column.field_name or column.header] = str(raw_value).strip()
            elif column.kind == 'int':
                cleaned[column.field_name or column.header] = _parse_int(raw_value)
            elif column.kind == 'decimal':
                cleaned[column.field_name or column.header] = _parse_decimal(raw_value)
            elif column.kind == 'date':
                cleaned[column.field_name or column.header] = _parse_date(raw_value)
            elif column.kind == 'time':
                cleaned[column.field_name or column.header] = _parse_time(raw_value)
            elif column.kind == 'bool':
                cleaned[column.field_name or column.header] = _parse_bool(raw_value)
            elif column.kind == 'choice':
                cleaned[column.field_name or column.header] = _parse_choice(raw_value, column.choices)
            elif column.kind == 'fk':
                cleaned[column.field_name or column.header] = _resolve_fk(column, raw_value)
            elif column.kind == 'm2m':
                cleaned[column.field_name or column.header] = _resolve_m2m(column, raw_value)
            else:
                cleaned[column.field_name or column.header] = raw_value
        except ImportErrorRow as exc:
            errors.append(str(exc))

    return cleaned, errors


DATA_MODELS: dict[str, dict[str, Any]] = {
    'territory': {
        'model': Division,
        'title': 'Territories',
        'slug': 'territory',
        'list_url': 'crm_products:division_list',
        'create_url': 'crm_products:division_create',
        'label': 'Territory',
        'file_prefix': 'territories',
        'lookup': lambda data: {'name': data.get('name')},
        'export_columns': [
            export_text('Territory ID', lambda obj: obj.division_id),
            export_text('Territory Name', lambda obj: obj.name),
            export_text('Territory Manager', lambda obj: obj.manager_name),
            export_text('Active', lambda obj: obj.is_active),
        ],
        'import_columns': [
            import_text('Territory Name', 'name', required=True),
            import_text('Territory Manager', 'manager_name'),
            import_bool('Active', 'is_active', default=True),
        ],
        'sample_row': {
            'Territory Name': 'North Territory',
            'Territory Manager': 'Test Manager',
            'Active': 'Yes',
        },
    },
    'product': {
        'model': ProductMaster,
        'title': 'Products',
        'slug': 'product',
        'list_url': 'crm_products:product_list',
        'create_url': 'crm_products:product_create',
        'label': 'Product',
        'file_prefix': 'products',
        'lookup': lambda data: {
            'product_name': data.get('Product Name'),
            'generic_name': data.get('Generic Name'),
            'brand_name': data.get('Brand Name'),
        },
        'export_columns': [
            export_text('Product ID', lambda obj: obj.product_id),
            export_text('Product Name', lambda obj: obj.product_name),
            export_text('Generic Name', lambda obj: obj.generic_name),
            export_text('Brand Name', lambda obj: obj.brand_name),
            export_text('Category', lambda obj: obj.get_category_display()),
            export_text('Territory', lambda obj: obj.division.name if obj.division else ''),
            export_text('Strength', lambda obj: obj.strength),
            export_text('Packing Size', lambda obj: obj.packing_size),
            export_text('Manufacturing / Factory Price', lambda obj: obj.manufacturing_cost_per_unit),
            export_text('Distributor Price', lambda obj: obj.distributor_price),
            export_text('Trade Price', lambda obj: obj.trade_price),
            export_text('Retail Price', lambda obj: obj.retail_price),
            export_text('Status', lambda obj: obj.get_status_display()),
            export_text('Description', lambda obj: obj.description),
        ],
        'import_columns': [
            import_text('Product Name', 'product_name', required=True),
            import_text('Generic Name', 'generic_name', required=True),
            import_text('Brand Name', 'brand_name', required=True),
            import_choice('Category', 'category', ProductMaster.CATEGORY_CHOICES, required=True),
            import_fk('Territory', 'division', Division, 'name', required=False),
            import_text('Strength', 'strength', required=True),
            import_text('Packing Size', 'packing_size', required=True),
            import_decimal('Manufacturing / Factory Price', 'manufacturing_cost_per_unit', default=Decimal('0.00')),
            import_decimal('Distributor Price', 'distributor_price', default=Decimal('0.00')),
            import_decimal('Trade Price', 'trade_price', default=Decimal('0.00')),
            import_decimal('Retail Price', 'retail_price', default=Decimal('0.00')),
            import_choice('Status', 'status', ProductMaster.STATUS_CHOICES, default='active'),
            import_text('Description', 'description'),
        ],
        'sample_row': {
            'Product Name': 'Amoxicillin 500mg',
            'Generic Name': 'Amoxicillin',
            'Brand Name': 'Amoxi-Test',
            'Category': 'Tablet',
            'Territory': 'North Territory',
            'Strength': '500mg',
            'Packing Size': '10x10',
            'Manufacturing / Factory Price': '40.00',
            'Distributor Price': '88.00',
            'Trade Price': '82.36',
            'Retail Price': '100.00',
            'Status': 'Active',
            'Description': 'Sample product row',
        },
    },
    'batch': {
        'model': BatchManagement,
        'title': 'Batches',
        'slug': 'batch',
        'list_url': 'crm_products:batch_list',
        'create_url': 'crm_products:batch_create',
        'label': 'Batch',
        'file_prefix': 'batches',
        'lookup': lambda data: {'batch_number': data.get('Batch Number')},
        'export_columns': [
            export_text('Batch Number', lambda obj: obj.batch_number),
            export_text('Product', lambda obj: obj.product.product_name),
            export_text('Manufacturing Date', lambda obj: obj.manufacturing_date),
            export_text('Expiry Date', lambda obj: obj.expiry_date),
            export_text('Quantity Manufactured', lambda obj: obj.quantity_manufactured),
            export_text('Quantity Sent To Distributors', lambda obj: obj.quantity_sent_to_distributors),
            export_text('Batch Status', lambda obj: obj.get_batch_status_display()),
            export_text('Notes', lambda obj: obj.notes),
        ],
        'import_columns': [
            import_text('Batch Number', 'batch_number', required=True),
            import_fk('Product', 'product', ProductMaster, 'product_name', required=True),
            import_date('Manufacturing Date', 'manufacturing_date', required=True),
            import_date('Expiry Date', 'expiry_date', required=True),
            import_int('Quantity Manufactured', 'quantity_manufactured', default=0),
            import_int('Quantity Sent To Distributors', 'quantity_sent_to_distributors', default=0),
            import_text('Notes', 'notes'),
        ],
        'sample_row': {
            'Batch Number': 'BT-2026-001',
            'Product': 'Amoxicillin 500mg',
            'Manufacturing Date': '2026-04-01',
            'Expiry Date': '2027-04-01',
            'Quantity Manufactured': '1000',
            'Quantity Sent To Distributors': '120',
            'Notes': 'Sample batch',
        },
    },
    'company_stock': {
        'model': CompanyStock,
        'title': 'Company Stock',
        'slug': 'company-stock',
        'list_url': 'crm_products:stock_list',
        'create_url': 'crm_products:stock_create',
        'label': 'Company Stock',
        'file_prefix': 'company_stock',
        'lookup': lambda data: {'batch__batch_number': data.get('Batch')},
        'export_columns': [
            export_text('Product', lambda obj: obj.product.product_name),
            export_text('Batch', lambda obj: obj.batch.batch_number),
            export_text('Warehouse Location', lambda obj: obj.warehouse_location),
            export_text('Low Stock Threshold', lambda obj: obj.low_stock_threshold),
        ],
        'import_columns': [
            import_fk('Product', 'product', ProductMaster, 'product_name', required=True),
            import_fk('Batch', 'batch', BatchManagement, 'batch_number', required=True),
            import_choice('Warehouse Location', 'warehouse_location', CompanyStock.WAREHOUSE_CHOICES, default='main'),
            import_int('Low Stock Threshold', 'low_stock_threshold', default=100),
        ],
        'sample_row': {
            'Product': 'Amoxicillin 500mg',
            'Batch': 'BT-2026-001',
            'Warehouse Location': 'Main Warehouse',
            'Low Stock Threshold': '100',
        },
    },
    'distributor': {
        'model': Distributor,
        'title': 'Distributors',
        'slug': 'distributor',
        'list_url': 'crm_distributors:distributor_list',
        'create_url': 'crm_distributors:distributor_create',
        'label': 'Distributor',
        'file_prefix': 'distributors',
        'lookup': lambda data: {'license_number': data.get('License Number')},
        'export_columns': [
            export_text('Distributor ID', lambda obj: obj.distributor_id),
            export_text('Distributor Name', lambda obj: obj.distributor_name),
            export_text('Owner Name', lambda obj: obj.owner_name),
            export_text('Contact Number', lambda obj: obj.contact_number),
            export_text('Email', lambda obj: obj.email),
            export_text('Address', lambda obj: obj.address),
            export_text('City', lambda obj: obj.city),
            export_text('Region', lambda obj: obj.region),
            export_text('License Number', lambda obj: obj.license_number),
            export_text('NTN Number', lambda obj: obj.ntn_number),
            export_text('Status', lambda obj: obj.get_status_display()),
            export_text('Credit Limit', lambda obj: obj.credit_limit),
        ],
        'import_columns': [
            import_text('Distributor Name', 'distributor_name', required=True),
            import_text('Owner Name', 'owner_name', required=True),
            import_text('Contact Number', 'contact_number', required=True),
            import_text('Email', 'email'),
            import_text('Address', 'address', required=True),
            import_text('City', 'city', required=True),
            import_text('Region', 'region', required=True),
            import_text('License Number', 'license_number', required=True),
            import_text('NTN Number', 'ntn_number'),
            import_choice('Status', 'status', Distributor.STATUS_CHOICES, default='active'),
            import_decimal('Credit Limit', 'credit_limit', default=Decimal('0.00')),
        ],
        'sample_row': {
            'Distributor Name': 'City Distributors',
            'Owner Name': 'Ali Khan',
            'Contact Number': '+92 300 0000000',
            'Email': 'city@example.com',
            'Address': 'Main Boulevard Lahore',
            'City': 'Lahore',
            'Region': 'Central',
            'License Number': 'LIC-1001',
            'NTN Number': '1234567-1',
            'Status': 'Active',
            'Credit Limit': '500000',
        },
    },
    'distributor_stock_entry': {
        'model': DistributorStockEntry,
        'title': 'Distributor Stock Entries',
        'slug': 'distributor-stock-entry',
        'list_url': 'crm_distributors:stock_entry_list',
        'create_url': 'crm_distributors:stock_entry_create',
        'label': 'Distributor Stock Entry',
        'file_prefix': 'distributor_stock_entries',
        'lookup': lambda data: {
            'distributor__license_number': data.get('Distributor License Number'),
            'product__product_name': data.get('Product'),
            'report_period_start': data.get('Report Period Start'),
            'report_period_end': data.get('Report Period End'),
        },
        'export_columns': [
            export_text('Distributor License Number', lambda obj: obj.distributor.license_number),
            export_text('Product', lambda obj: obj.product.product_name),
            export_text('Batch', lambda obj: obj.batch.batch_number if obj.batch else ''),
            export_text('Opening Stock', lambda obj: obj.opening_stock),
            export_text('Received Quantity', lambda obj: obj.received_quantity),
            export_text('Sold Quantity', lambda obj: obj.sold_quantity),
            export_text('Expired Quantity', lambda obj: obj.expired_quantity),
            export_text('Near Expiry Quantity', lambda obj: obj.near_expiry_quantity),
            export_text('Report Period Start', lambda obj: obj.report_period_start),
            export_text('Report Period End', lambda obj: obj.report_period_end),
            export_text('Notes', lambda obj: obj.notes),
        ],
        'import_columns': [
            import_fk('Distributor License Number', 'distributor', Distributor, 'license_number', required=True),
            import_fk('Product', 'product', ProductMaster, 'product_name', required=True),
            import_fk('Batch', 'batch', BatchManagement, 'batch_number', required=False),
            import_int('Opening Stock', 'opening_stock', default=0),
            import_int('Received Quantity', 'received_quantity', default=0),
            import_int('Sold Quantity', 'sold_quantity', default=0),
            import_int('Expired Quantity', 'expired_quantity', default=0),
            import_int('Near Expiry Quantity', 'near_expiry_quantity', default=0),
            import_date('Report Period Start', 'report_period_start', required=True),
            import_date('Report Period End', 'report_period_end', required=True),
            import_text('Notes', 'notes'),
        ],
        'sample_row': {
            'Distributor License Number': 'LIC-1001',
            'Product': 'Amoxicillin 500mg',
            'Batch': 'BT-2026-001',
            'Opening Stock': '100',
            'Received Quantity': '500',
            'Sold Quantity': '200',
            'Expired Quantity': '0',
            'Near Expiry Quantity': '10',
            'Report Period Start': '2026-04-01',
            'Report Period End': '2026-04-30',
            'Notes': 'Monthly stock entry',
        },
    },
    'distributor_sales_value': {
        'model': DistributorSalesValue,
        'title': 'Distributor Sales Values',
        'slug': 'distributor-sales-value',
        'list_url': 'crm_distributors:sales_value_list',
        'create_url': 'crm_distributors:sales_value_create',
        'label': 'Distributor Sales Value',
        'file_prefix': 'distributor_sales_values',
        'lookup': lambda data: {
            'distributor__license_number': data.get('Distributor License Number'),
            'product__product_name': data.get('Product'),
            'sale_date': data.get('Sale Date'),
        },
        'export_columns': [
            export_text('Distributor License Number', lambda obj: obj.distributor.license_number),
            export_text('Product', lambda obj: obj.product.product_name),
            export_text('Quantity Sold', lambda obj: obj.quantity_sold),
            export_text('Price Per Unit', lambda obj: obj.price_per_unit),
            export_text('Sale Date', lambda obj: obj.sale_date),
        ],
        'import_columns': [
            import_fk('Distributor License Number', 'distributor', Distributor, 'license_number', required=True),
            import_fk('Product', 'product', ProductMaster, 'product_name', required=True),
            import_int('Quantity Sold', 'quantity_sold', default=0),
            import_decimal('Price Per Unit', 'price_per_unit', required=True),
            import_date('Sale Date', 'sale_date', required=True),
        ],
        'sample_row': {
            'Distributor License Number': 'LIC-1001',
            'Product': 'Amoxicillin 500mg',
            'Quantity Sold': '120',
            'Price Per Unit': '100.00',
            'Sale Date': '2026-04-20',
        },
    },
    'region': {
        'model': Region,
        'title': 'Regions',
        'slug': 'region',
        'list_url': 'crm_sales:region_list',
        'create_url': 'crm_sales:region_create',
        'label': 'Region',
        'file_prefix': 'regions',
        'lookup': lambda data: {
            'region_name': data.get('Region Name'),
            'division__name': data.get('Territory'),
        },
        'export_columns': [
            export_text('Region ID', lambda obj: obj.region_id),
            export_text('Region Name', lambda obj: obj.region_name),
            export_text('Territory', lambda obj: obj.division.name),
            export_text('Regional Manager', lambda obj: obj.regional_manager),
            export_text('Active', lambda obj: obj.is_active),
        ],
        'import_columns': [
            import_text('Region Name', 'region_name', required=True),
            import_fk('Territory', 'division', Division, 'name', required=True),
            import_text('Regional Manager', 'regional_manager'),
            import_bool('Active', 'is_active', default=True),
        ],
        'sample_row': {
            'Region Name': 'Lahore North',
            'Territory': 'North Territory',
            'Regional Manager': 'Manager Name',
            'Active': 'Yes',
        },
    },
    'area': {
        'model': Area,
        'title': 'Areas',
        'slug': 'area',
        'list_url': 'crm_sales:area_list',
        'create_url': 'crm_sales:area_create',
        'label': 'Area',
        'file_prefix': 'areas',
        'lookup': lambda data: {
            'area_name': data.get('Area Name'),
            'region__region_name': data.get('Region'),
        },
        'export_columns': [
            export_text('Area ID', lambda obj: obj.area_id),
            export_text('Area Name', lambda obj: obj.area_name),
            export_text('Region', lambda obj: obj.region.region_name),
            export_text('Territory', lambda obj: obj.region.division.name),
            export_text('Area Manager', lambda obj: obj.area_manager),
            export_text('Active', lambda obj: obj.is_active),
        ],
        'import_columns': [
            import_text('Area Name', 'area_name', required=True),
            import_fk('Region', 'region', Region, 'region_name', required=True),
            import_text('Area Manager', 'area_manager'),
            import_bool('Active', 'is_active', default=True),
        ],
        'sample_row': {
            'Area Name': 'Gulberg',
            'Region': 'Lahore North',
            'Area Manager': 'Area Manager Name',
            'Active': 'Yes',
        },
    },
    'mr': {
        'model': MedicalRepresentative,
        'title': 'Medical Representatives',
        'slug': 'mr',
        'list_url': 'crm_sales:mr_list',
        'create_url': 'crm_sales:mr_create',
        'label': 'Medical Representative',
        'file_prefix': 'medical_representatives',
        'lookup': lambda data: {'cnic': data.get('CNIC')},
        'export_columns': [
            export_text('MR ID', lambda obj: obj.mr_id),
            export_text('Name', lambda obj: obj.name),
            export_text('CNIC', lambda obj: obj.cnic),
            export_text('Phone Number', lambda obj: obj.phone_number),
            export_text('Email', lambda obj: obj.email),
            export_text('Address', lambda obj: obj.address),
            export_text('Territory', lambda obj: obj.division.name if obj.division else ''),
            export_text('Region', lambda obj: obj.region.region_name if obj.region else ''),
            export_text('Area', lambda obj: obj.area.area_name if obj.area else ''),
            export_text('Date Of Joining', lambda obj: obj.date_of_joining),
            export_text('Salary', lambda obj: obj.salary),
            export_text('Status', lambda obj: obj.get_status_display()),
            export_text('Assigned Doctors', lambda obj: '; '.join(obj.assigned_doctors.values_list('doctor_id', flat=True))),
        ],
        'import_columns': [
            import_text('Name', 'name', required=True),
            import_text('CNIC', 'cnic', required=True),
            import_text('Phone Number', 'phone_number', required=True),
            import_text('Email', 'email'),
            import_text('Address', 'address'),
            import_fk('Territory', 'division', Division, 'name', required=True),
            import_fk('Region', 'region', Region, 'region_name', required=False),
            import_fk('Area', 'area', Area, 'area_name', required=False),
            import_date('Date Of Joining', 'date_of_joining', required=False),
            import_decimal('Salary', 'salary', default=Decimal('0.00')),
            import_choice('Status', 'status', MedicalRepresentative.STATUS_CHOICES, default='active'),
            import_m2m('Assigned Doctors', 'assigned_mrs', Doctor, 'doctor_id', required=False),
        ],
        'sample_row': {
            'Name': 'Test MR',
            'CNIC': '12345-1234567-1',
            'Phone Number': '+92 300 1111111',
            'Email': 'testmr@example.com',
            'Address': 'Test Address',
            'Territory': 'North Territory',
            'Region': 'Lahore North',
            'Area': 'Gulberg',
            'Date Of Joining': '2026-04-01',
            'Salary': '65000',
            'Status': 'Active',
            'Assigned Doctors': 'DOC-00001',
        },
    },
    'doctor': {
        'model': Doctor,
        'title': 'Doctors',
        'slug': 'doctor',
        'list_url': 'crm_doctors:doctor_list',
        'create_url': 'crm_doctors:doctor_create',
        'label': 'Doctor',
        'file_prefix': 'doctors',
        'lookup': lambda data: {'doctor_name': data.get('Doctor Name'), 'specialty': data.get('Specialty'), 'city': data.get('City')},
        'export_columns': [
            export_text('Doctor ID', lambda obj: obj.doctor_id),
            export_text('Doctor Name', lambda obj: obj.doctor_name),
            export_text('Specialty', lambda obj: obj.specialty),
            export_text('Qualification', lambda obj: obj.qualification),
            export_text('Hospital Name', lambda obj: obj.hospital_name),
            export_text('Clinic Name', lambda obj: obj.clinic_name),
            export_text('City', lambda obj: obj.city),
            export_text('Area', lambda obj: obj.area.area_name if obj.area else ''),
            export_text('Contact Number', lambda obj: obj.contact_number),
            export_text('Email', lambda obj: obj.email),
            export_text('Patients Per Day', lambda obj: obj.estimated_patients_per_day),
            export_text('Prescription Potential', lambda obj: obj.estimated_prescription_potential),
            export_text('Status', lambda obj: obj.get_status_display()),
            export_text('Assigned MRs', lambda obj: '; '.join(obj.assigned_mrs.values_list('mr_id', flat=True))),
        ],
        'import_columns': [
            import_text('Doctor Name', 'doctor_name', required=True),
            import_text('Specialty', 'specialty', required=True),
            import_text('Qualification', 'qualification'),
            import_text('Hospital Name', 'hospital_name'),
            import_text('Clinic Name', 'clinic_name'),
            import_text('City', 'city', required=True),
            import_fk('Area', 'area', Area, 'area_name', required=False),
            import_text('Contact Number', 'contact_number'),
            import_text('Email', 'email'),
            import_int('Patients Per Day', 'estimated_patients_per_day', default=0),
            import_decimal('Prescription Potential', 'estimated_prescription_potential', default=Decimal('0.00')),
            import_choice('Status', 'status', Doctor.STATUS_CHOICES, default='active'),
            import_m2m('Assigned MRs', 'assigned_mrs', MedicalRepresentative, 'mr_id', required=False),
        ],
        'sample_row': {
            'Doctor Name': 'Dr. Ali Hassan',
            'Specialty': 'General Physician',
            'Qualification': 'MBBS, FCPS',
            'Hospital Name': 'City Care Hospital',
            'Clinic Name': 'Ali Clinic',
            'City': 'Lahore',
            'Area': 'Gulberg',
            'Contact Number': '+92 321 2222222',
            'Email': 'ali.hassan@example.com',
            'Patients Per Day': '45',
            'Prescription Potential': '85000',
            'Status': 'Active',
            'Assigned MRs': 'MR-00001',
        },
    },
    'doctor_location': {
        'model': DoctorPracticeLocation,
        'title': 'Doctor Practice Locations',
        'slug': 'doctor-location',
        'list_url': 'crm_doctors:doctor_list',
        'create_url': 'crm_doctors:doctor_create',
        'label': 'Doctor Practice Location',
        'file_prefix': 'doctor_practice_locations',
        'lookup': lambda data: {'doctor__doctor_name': data.get('Doctor Name'), 'location_name': data.get('Location Name')},
        'export_columns': [
            export_text('Doctor Name', lambda obj: obj.doctor.doctor_name),
            export_text('Location Name', lambda obj: obj.location_name),
            export_text('Location Type', lambda obj: obj.get_location_type_display()),
            export_text('Address', lambda obj: obj.address),
            export_text('Active', lambda obj: obj.is_active),
        ],
        'import_columns': [
            import_fk('Doctor Name', 'doctor', Doctor, 'doctor_name', required=True),
            import_text('Location Name', 'location_name', required=True),
            import_choice('Location Type', 'location_type', DoctorPracticeLocation.LOCATION_TYPE_CHOICES, default='clinic'),
            import_text('Address', 'address'),
            import_bool('Active', 'is_active', default=True),
        ],
        'sample_row': {
            'Doctor Name': 'Dr. Ali Hassan',
            'Location Name': 'City Care Hospital',
            'Location Type': 'Hospital',
            'Address': 'Main Boulevard, Lahore',
            'Active': 'Yes',
        },
    },
    'doctor_visit': {
        'model': DoctorVisit,
        'title': 'Doctor Visits',
        'slug': 'doctor-visit',
        'list_url': 'crm_doctors:visit_list',
        'create_url': 'crm_doctors:visit_create',
        'label': 'Doctor Visit',
        'file_prefix': 'doctor_visits',
        'lookup': lambda data: {'doctor__doctor_name': data.get('Doctor Name'), 'mr__mr_id': data.get('MR ID'), 'visit_date': data.get('Visit Date'), 'visit_time': data.get('Visit Time')},
        'export_columns': [
            export_text('MR ID', lambda obj: obj.mr.mr_id),
            export_text('Doctor Name', lambda obj: obj.doctor.doctor_name),
            export_text('Visit Location', lambda obj: obj.visit_location.location_name if obj.visit_location else obj.hospital_clinic_name),
            export_text('Visit Date', lambda obj: obj.visit_date),
            export_text('Visit Time', lambda obj: obj.visit_time),
            export_text('Visit Status', lambda obj: obj.get_visit_type_display()),
            export_text('Hospital / Clinic Name', lambda obj: obj.hospital_clinic_name),
            export_text('GPS Latitude', lambda obj: obj.gps_latitude),
            export_text('GPS Longitude', lambda obj: obj.gps_longitude),
            export_text('GPS Address', lambda obj: obj.gps_address),
            export_text('GPS Verified', lambda obj: obj.is_gps_verified),
            export_text('Next Follow Up Date', lambda obj: obj.next_follow_up_date),
            export_text('Remarks', lambda obj: obj.remarks),
        ],
        'import_columns': [
            import_fk('MR ID', 'mr', MedicalRepresentative, 'mr_id', required=True),
            import_fk('Doctor Name', 'doctor', Doctor, 'doctor_name', required=True),
            import_text('Visit Location', 'visit_location_name', required=False),
            import_date('Visit Date', 'visit_date', required=True),
            import_time('Visit Time', 'visit_time', required=True),
            import_choice('Visit Status', 'visit_type', DoctorVisit.VISIT_TYPE_CHOICES, default='follow_up'),
            import_text('Hospital / Clinic Name', 'hospital_clinic_name'),
            import_decimal('GPS Latitude', 'gps_latitude', default=None),
            import_decimal('GPS Longitude', 'gps_longitude', default=None),
            import_text('GPS Address', 'gps_address'),
            import_bool('GPS Verified', 'is_gps_verified', default=False),
            import_date('Next Follow Up Date', 'next_follow_up_date', required=False),
            import_text('Remarks', 'remarks'),
        ],
        'sample_row': {
            'MR ID': 'MR-00001',
            'Doctor Name': 'Dr. Ali Hassan',
            'Visit Location': 'City Care Hospital',
            'Visit Date': '2026-04-22',
            'Visit Time': '10:30',
            'Visit Status': 'Call Done',
            'Hospital / Clinic Name': 'City Care Hospital',
            'GPS Latitude': '31.5204000',
            'GPS Longitude': '74.3587000',
            'GPS Address': 'City Care Hospital, Lahore',
            'GPS Verified': 'Yes',
            'Next Follow Up Date': '2026-04-29',
            'Remarks': 'Test visit',
        },
    },
    'medical_store': {
        'model': MedicalStore,
        'title': 'Medical Stores',
        'slug': 'medical-store',
        'list_url': 'crm_stores:store_list',
        'create_url': 'crm_stores:store_create',
        'label': 'Medical Store',
        'file_prefix': 'medical_stores',
        'lookup': lambda data: {'store_name': data.get('Store Name'), 'address': data.get('Address')},
        'export_columns': [
            export_text('Store ID', lambda obj: obj.store_id),
            export_text('Store Name', lambda obj: obj.store_name),
            export_text('Owner Name', lambda obj: obj.owner_name),
            export_text('Phone', lambda obj: obj.phone),
            export_text('Address', lambda obj: obj.address),
            export_text('Area', lambda obj: obj.area.area_name if obj.area else ''),
            export_text('Distributor', lambda obj: obj.distributor.distributor_name if obj.distributor else ''),
            export_text('Drug License Number', lambda obj: obj.drug_license_number),
            export_text('Status', lambda obj: obj.get_status_display()),
            export_text('Linked Doctors', lambda obj: '; '.join(obj.linked_doctors.values_list('doctor_id', flat=True))),
        ],
        'import_columns': [
            import_text('Store Name', 'store_name', required=True),
            import_text('Owner Name', 'owner_name', required=True),
            import_text('Phone', 'phone'),
            import_text('Address', 'address', required=True),
            import_fk('Area', 'area', Area, 'area_name', required=False),
            import_fk('Distributor', 'distributor', Distributor, 'distributor_name', required=False),
            import_text('Drug License Number', 'drug_license_number'),
            import_choice('Status', 'status', MedicalStore.STATUS_CHOICES, default='active'),
            import_m2m('Linked Doctors', 'linked_doctors', Doctor, 'doctor_id', required=False),
        ],
        'sample_row': {
            'Store Name': 'Medicare Pharmacy',
            'Owner Name': 'Asif',
            'Phone': '+92 333 4444444',
            'Address': 'Near City Care Hospital',
            'Area': 'Gulberg',
            'Distributor': 'City Distributors',
            'Drug License Number': 'DL-1234',
            'Status': 'Active',
            'Linked Doctors': 'DOC-00001',
        },
    },
    'store_tracking': {
        'model': StoreProductTracking,
        'title': 'Store Product Trackings',
        'slug': 'store-tracking',
        'list_url': 'crm_stores:store_list',
        'create_url': 'crm_stores:store_product_form',
        'label': 'Store Product Tracking',
        'file_prefix': 'store_product_trackings',
        'lookup': lambda data: {'store__store_name': data.get('Store Name'), 'product__product_name': data.get('Product')},
        'export_columns': [
            export_text('Store Name', lambda obj: obj.store.store_name),
            export_text('Product', lambda obj: obj.product.product_name),
            export_text('Availability', lambda obj: obj.get_availability_display()),
            export_text('Monthly Sales Estimate', lambda obj: obj.monthly_sales_estimate),
            export_text('Monthly Revenue Estimate', lambda obj: obj.monthly_revenue_estimate),
            export_text('Last Updated By MR', lambda obj: obj.last_updated_by_mr),
        ],
        'import_columns': [
            import_fk('Store Name', 'store', MedicalStore, 'store_name', required=True),
            import_fk('Product', 'product', ProductMaster, 'product_name', required=True),
            import_choice('Availability', 'availability', StoreProductTracking.AVAILABILITY_CHOICES, default='available'),
            import_int('Monthly Sales Estimate', 'monthly_sales_estimate', default=0),
            import_decimal('Monthly Revenue Estimate', 'monthly_revenue_estimate', default=Decimal('0.00')),
            import_text('Last Updated By MR', 'last_updated_by_mr'),
        ],
        'sample_row': {
            'Store Name': 'Medicare Pharmacy',
            'Product': 'Amoxicillin 500mg',
            'Availability': 'Available',
            'Monthly Sales Estimate': '120',
            'Monthly Revenue Estimate': '12000',
            'Last Updated By MR': 'Test MR',
        },
    },
}
