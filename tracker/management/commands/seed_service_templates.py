"""
Management command to seed default ServiceTemplate, ServiceType, ServiceAddon,
and InvoicePatternMatcher data.
Usage: python manage.py seed_service_templates
"""

from django.core.management.base import BaseCommand
from tracker.models import ServiceTemplate, InvoicePatternMatcher, ServiceType, ServiceAddon, Brand, InventoryItem
import random


class Command(BaseCommand):
    help = 'Seed default service templates, service types, add-ons, and invoice pattern matchers'

    def handle(self, *args, **options):
        self.stdout.write('Seeding service templates, types, add-ons and patterns...')

        # Service Types - for 'Service' orders
        service_types_data = [
            {'name': 'Oil Change', 'estimated_minutes': 30},
            {'name': 'Brake Service', 'estimated_minutes': 45},
            {'name': 'Tire Rotation', 'estimated_minutes': 30},
            {'name': 'Engine Tune-up', 'estimated_minutes': 60},
            {'name': 'Transmission Service', 'estimated_minutes': 90},
            {'name': 'Battery Replacement', 'estimated_minutes': 20},
            {'name': 'Air Filter Change', 'estimated_minutes': 15},
            {'name': 'Wheel Alignment', 'estimated_minutes': 45},
            {'name': 'Suspension Repair', 'estimated_minutes': 75},
            {'name': 'Exhaust System Repair', 'estimated_minutes': 60},
            {'name': 'Radiator Flush', 'estimated_minutes': 45},
            {'name': 'AC Service', 'estimated_minutes': 60},
            {'name': 'Spark Plug Replacement', 'estimated_minutes': 30},
            {'name': 'Brake Pad Replacement', 'estimated_minutes': 25},
            {'name': 'Coolant Replacement', 'estimated_minutes': 30},
            {'name': 'Power Steering Fluid', 'estimated_minutes': 20},
            {'name': 'General Maintenance', 'estimated_minutes': 50},
        ]

        created_count = 0
        for service_data in service_types_data:
            service_type, created = ServiceType.objects.get_or_create(
                name=service_data['name'],
                defaults={
                    'estimated_minutes': service_data['estimated_minutes'],
                    'is_active': True,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created: {service_type.name} ({service_type.estimated_minutes} mins)'))
                created_count += 1
            else:
                self.stdout.write(f'  → Already exists: {service_type.name}')

        self.stdout.write(self.style.SUCCESS(f'\nService Types: {created_count} created'))

        # Service Add-ons - for 'Sales' orders (e.g., tire installation, balancing)
        service_addons_data = [
            {'name': 'Wheel Balancing', 'estimated_minutes': 20},
            {'name': 'Tire Installation', 'estimated_minutes': 30},
            {'name': 'Wheel Mounting', 'estimated_minutes': 25},
            {'name': 'Tire Repair', 'estimated_minutes': 15},
            {'name': 'Alignment Check', 'estimated_minutes': 20},
            {'name': 'Suspension Inspection', 'estimated_minutes': 30},
            {'name': 'Brake Fluid Replacement', 'estimated_minutes': 20},
            {'name': 'Engine Cleaning', 'estimated_minutes': 45},
            {'name': 'Cabin Air Filter', 'estimated_minutes': 15},
            {'name': 'Battery Testing', 'estimated_minutes': 10},
            {'name': 'Headlight Restoration', 'estimated_minutes': 20},
            {'name': 'Undercarriage Wash', 'estimated_minutes': 30},
            {'name': 'Transmission Fluid Flush', 'estimated_minutes': 45},
            {'name': 'Differential Service', 'estimated_minutes': 40},
            {'name': 'Engine Oil Top-up', 'estimated_minutes': 5},
            {'name': 'Windshield Treatment', 'estimated_minutes': 15},
        ]

        created_count = 0
        for addon_data in service_addons_data:
            addon, created = ServiceAddon.objects.get_or_create(
                name=addon_data['name'],
                defaults={
                    'estimated_minutes': addon_data['estimated_minutes'],
                    'is_active': True,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created: {addon.name} ({addon.estimated_minutes} mins)'))
                created_count += 1
            else:
                self.stdout.write(f'  → Already exists: {addon.name}')

        self.stdout.write(self.style.SUCCESS(f'\nService Add-ons: {created_count} created'))

        # Brands - for inventory items
        brands_data = [
            {'name': 'Michelin', 'description': 'Premium tires for all vehicles', 'website': 'https://www.michelin.com'},
            {'name': 'Bridgestone', 'description': 'High-performance tires', 'website': 'https://www.bridgestone.com'},
            {'name': 'Goodyear', 'description': 'Quality tires for all seasons', 'website': 'https://www.goodyear.com'},
            {'name': 'Pirelli', 'description': 'Luxury and performance tires', 'website': 'https://www.pirelli.com'},
            {'name': 'Dunlop', 'description': 'Reliable tires for everyday use', 'website': 'https://www.dunlop.com'},
            {'name': 'Continental', 'description': 'German engineering tires', 'website': 'https://www.continental.com'},
            {'name': 'Hankook', 'description': 'Affordable quality tires', 'website': 'https://www.hankook.com'},
            {'name': 'Yokohama', 'description': 'Japanese precision tires', 'website': 'https://www.yokohama.com'},
        ]

        created_count = 0
        brands_map = {}
        for brand_data in brands_data:
            brand, created = Brand.objects.get_or_create(
                name=brand_data['name'],
                defaults={
                    'description': brand_data['description'],
                    'website': brand_data.get('website'),
                    'is_active': True,
                }
            )
            brands_map[brand_data['name']] = brand
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created: {brand.name}'))
                created_count += 1
            else:
                self.stdout.write(f'  → Already exists: {brand.name}')

        self.stdout.write(self.style.SUCCESS(f'\nBrands: {created_count} created'))

        # Inventory Items - tire products for sales orders
        tire_types = ['All Season', 'Summer', 'Winter', 'Performance', 'Off-Road', 'Truck', 'Economy', 'Premium']
        tire_sizes = [
            '185/65R15', '195/65R15', '205/55R16', '215/55R16',
            '225/45R17', '235/45R17', '245/40R18', '255/40R19',
            '265/70R16', '275/65R17'
        ]

        inventory_items_data = [
            # Air filters
            {'name': 'Engine Air Filter', 'brand': 'Michelin', 'price': 45.00, 'cost_price': 25.00, 'quantity': 20},
            {'name': 'Cabin Air Filter', 'brand': 'Bridgestone', 'price': 35.00, 'cost_price': 18.00, 'quantity': 25},

            # Brake pads and fluid
            {'name': 'Brake Pad Set', 'brand': 'Continental', 'price': 85.00, 'cost_price': 50.00, 'quantity': 15},
            {'name': 'Brake Fluid (1L)', 'brand': 'Goodyear', 'price': 28.00, 'cost_price': 15.00, 'quantity': 30},

            # Oil and fluids
            {'name': 'Engine Oil (5L)', 'brand': 'Pirelli', 'price': 65.00, 'cost_price': 38.00, 'quantity': 20},
            {'name': 'Transmission Fluid (1L)', 'brand': 'Dunlop', 'price': 52.00, 'cost_price': 28.00, 'quantity': 15},
            {'name': 'Coolant (1L)', 'brand': 'Hankook', 'price': 32.00, 'cost_price': 18.00, 'quantity': 25},

            # Batteries
            {'name': 'Car Battery 12V', 'brand': 'Yokohama', 'price': 150.00, 'cost_price': 85.00, 'quantity': 8},

            # Spark plugs
            {'name': 'Spark Plug Set (4)', 'brand': 'Michelin', 'price': 48.00, 'cost_price': 26.00, 'quantity': 12},
        ]

        created_count = 0
        for item_data in inventory_items_data:
            brand = brands_map.get(item_data['brand'])

            item, created = InventoryItem.objects.get_or_create(
                name=item_data['name'],
                brand=brand,
                defaults={
                    'description': f"{item_data['name']} for automotive service",
                    'quantity': item_data['quantity'],
                    'price': item_data['price'],
                    'cost_price': item_data['cost_price'],
                    'sku': f"SKU-{item_data['name'][:3].upper()}-{random.randint(1000, 9999)}",
                    'reorder_level': 5,
                    'location': f"Aisle {random.randint(1, 5)}, Shelf {random.choice('ABCDE')}",
                    'is_active': True,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created: {item.name} ({item.quantity} units @ ${item.price})'))
                created_count += 1
            else:
                self.stdout.write(f'  → Already exists: {item.name}')

        # Create tire inventory items (with variations)
        tire_count = 0
        for brand_name in ['Michelin', 'Bridgestone', 'Goodyear', 'Continental']:
            brand = brands_map.get(brand_name)
            for tire_type in tire_types[:4]:  # Create 4 tire types per brand for diversity
                tire_size = random.choice(tire_sizes)
                tire_name = f"{brand_name} {tire_type} {tire_size}"

                tire_item, created = InventoryItem.objects.get_or_create(
                    name=tire_name,
                    brand=brand,
                    defaults={
                        'description': f"{tire_type} tire size {tire_size} from {brand_name}",
                        'quantity': random.randint(10, 50),
                        'price': round(random.uniform(80, 250), 2),
                        'cost_price': round(random.uniform(45, 150), 2),
                        'sku': f"TIRE-{brand_name[:3].upper()}-{random.randint(10000, 99999)}",
                        'barcode': f"{random.randint(1000000000000, 9999999999999)}",
                        'reorder_level': 5,
                        'location': f"Tire Rack {random.randint(1, 3)}, Section {random.choice('ABC')}",
                        'is_active': True,
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Created: {tire_item.name} ({tire_item.quantity} units @ ${tire_item.price})'))
                    tire_count += 1
                else:
                    self.stdout.write(f'  → Already exists: {tire_item.name}')

        self.stdout.write(self.style.SUCCESS(f'\nInventory Items: {created_count + tire_count} created (standard items: {created_count}, tires: {tire_count})'))

        # Common service templates for car service
        service_templates = [
            {
                'name': 'Oil Change',
                'keywords': 'oil change, oil service, oil replacement, oil top up',
                'service_type': 'service',
                'is_common': True,
            },
            {
                'name': 'Tire Rotation',
                'keywords': 'tire rotation, tyre rotation, wheel alignment, tire balance',
                'service_type': 'service',
                'is_common': True,
            },
            {
                'name': 'Brake Service',
                'keywords': 'brake, brake pads, brake fluid, brake service, brake check',
                'service_type': 'service',
                'is_common': True,
            },
            {
                'name': 'Air Filter Replacement',
                'keywords': 'air filter, air filter replacement, cabin filter',
                'service_type': 'service',
                'is_common': True,
            },
            {
                'name': 'Battery Service',
                'keywords': 'battery, battery replacement, battery service, battery check',
                'service_type': 'service',
                'is_common': True,
            },
            {
                'name': 'Tire Installation',
                'keywords': 'tire installation, tyre installation, tire mount, tyre mount, install tires',
                'service_type': 'sales',
                'is_common': True,
            },
            {
                'name': 'Tire Balancing',
                'keywords': 'balancing, balance, wheel balance, tire balance',
                'service_type': 'sales',
                'is_common': True,
            },
            {
                'name': 'General Maintenance',
                'keywords': 'maintenance, service, check, inspection, diagnostic',
                'service_type': 'service',
                'is_common': False,
            },
        ]
        
        created_count = 0
        for template_data in service_templates:
            template, created = ServiceTemplate.objects.get_or_create(
                name=template_data['name'],
                defaults={
                    'keywords': template_data['keywords'],
                    'service_type': template_data['service_type'],
                    'is_common': template_data['is_common'],
                    'is_active': True,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created: {template.name}'))
                created_count += 1
            else:
                self.stdout.write(f'  → Already exists: {template.name}')
        
        self.stdout.write(self.style.SUCCESS(f'\nService Templates: {created_count} created'))
        
        # Common invoice patterns
        invoice_patterns = [
            {
                'name': 'Plate in reference field',
                'field_type': 'plate_number',
                'regex_pattern': r'(?:REFERENCE|REF|Plate|License|plate|reference)[\s:]*([A-Z]{3}\s?[A-Z]?\s?\d+\s?[A-Z]{2,3})',
                'extract_group': 1,
                'priority': 10,
                'is_default': True,
            },
            {
                'name': 'Total amount with label',
                'field_type': 'amount',
                'regex_pattern': r'(?:Total|TOTAL|Amount|AMOUNT|Due|DUE)[\s:]*([A-Z])?[\s]*([\d,]+\.?\d{0,2})',
                'extract_group': 2,
                'priority': 10,
                'is_default': True,
            },
            {
                'name': 'Tanzania phone format',
                'field_type': 'customer_phone',
                'regex_pattern': r'(?:Phone|Tel|Mobile|Contact|phone|tel)[\s:]*(\+?255\s?\d{3}\s?\d{3}\s?\d{3}|0[67]\d{2}\s?\d{3}\s?\d{3})',
                'extract_group': 1,
                'priority': 10,
                'is_default': True,
            },
            {
                'name': 'Customer name after label',
                'field_type': 'customer_name',
                'regex_pattern': r'(?:CUSTOMER|Customer|Name|name)[\s:]*([A-Za-z\s]+?)(?:\n|$|Phone|phone|Tel|tel|Address|address)',
                'extract_group': 1,
                'priority': 10,
                'is_default': True,
            },
            {
                'name': 'Email pattern',
                'field_type': 'customer_email',
                'regex_pattern': r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                'extract_group': 1,
                'priority': 10,
                'is_default': False,
            },
            {
                'name': 'Service/Item description',
                'field_type': 'service_description',
                'regex_pattern': r'(?:SERVICE|Service|Description|Item|ITEM|item|description)[\s:]*([A-Za-z0-9\s,.-]+?)(?:\n|Qty|Quantity|qty|$)',
                'extract_group': 1,
                'priority': 10,
                'is_default': True,
            },
            {
                'name': 'Quantity field',
                'field_type': 'quantity',
                'regex_pattern': r'(?:QTY|Quantity|Qty|qty)[\s:]*(\d+)',
                'extract_group': 1,
                'priority': 10,
                'is_default': True,
            },
            {
                'name': 'Invoice/Reference number',
                'field_type': 'reference',
                'regex_pattern': r'(?:REF|Reference|Invoice|INV|reference|invoice|inv)[\s#:]*([A-Z0-9-]+)',
                'extract_group': 1,
                'priority': 10,
                'is_default': True,
            },
        ]
        
        created_count = 0
        for pattern_data in invoice_patterns:
            pattern, created = InvoicePatternMatcher.objects.get_or_create(
                name=pattern_data['name'],
                defaults={
                    'field_type': pattern_data['field_type'],
                    'regex_pattern': pattern_data['regex_pattern'],
                    'extract_group': pattern_data['extract_group'],
                    'priority': pattern_data['priority'],
                    'is_default': pattern_data['is_default'],
                    'is_active': True,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created: {pattern.name}'))
                created_count += 1
            else:
                self.stdout.write(f'  → Already exists: {pattern.name}')
        
        self.stdout.write(self.style.SUCCESS(f'\nInvoice Patterns: {created_count} created'))
        self.stdout.write(self.style.SUCCESS('\n✓ Seeding complete! Service types, add-ons, templates and patterns are ready to use.'))
