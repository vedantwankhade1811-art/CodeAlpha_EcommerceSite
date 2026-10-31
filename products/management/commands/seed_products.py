import os
import shutil
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils.text import slugify
from products.models import Category, Product, ProductImage
from PIL import Image, ImageDraw, ImageFont


CATEGORY_PALETTES = {
    'Fashion': '#EDE8E0',
    'Shoes': '#E4E2DD',
    'Accessories': '#DFE3DC',
    'Electronics': '#EBDDD3',
    'Home & Living': '#EDE8E0',
    'Lifestyle': '#E4E2DD',
}

def hex_to_rgb(hex_code):
    hex_code = hex_code.lstrip('#')
    return tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))

def get_font(size):
    # Try finding system fonts on Windows or fallback gracefully
    font_paths = [
        "C:\\Windows\\Fonts\\georgia.ttf",
        "C:\\Windows\\Fonts\\arial.ttf",
        "C:\\Windows\\Fonts\\segoeui.ttf",
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()

def generate_pillow_image(target_path, title, subtitle="", category_name="Fashion", width=800, height=1000):
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    tint = CATEGORY_PALETTES.get(category_name, '#EDE8E0')
    bg_color = hex_to_rgb(tint)

    img = Image.new('RGB', (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    # Decorative minimalist border
    draw.rectangle([(24, 24), (width - 24, height - 24)], outline=(215, 212, 206), width=2)
    draw.rectangle([(32, 32), (width - 32, height - 32)], outline=(230, 228, 224), width=1)

    # Brand header text
    brand_font = get_font(20)
    brand_text = "CARTZA STUDIO"
    draw.text((width // 2, 80), brand_text, fill=(85, 85, 85), font=brand_font, anchor="mm")

    # Category badge
    cat_font = get_font(18)
    cat_text = category_name.upper()
    draw.text((width // 2, 120), cat_text, fill=(166, 94, 63), font=cat_font, anchor="mm")

    # Center minimal geometric graphic / motif
    center_y = height // 2 - 40
    draw.rectangle([(width // 2 - 120, center_y - 120), (width // 2 + 120, center_y + 120)], outline=(190, 185, 178), width=2)
    draw.line([(width // 2 - 80, center_y), (width // 2 + 80, center_y)], fill=(166, 94, 63), width=2)

    # Title text
    title_font = get_font(34)
    # Wrap title if long
    words = title.split()
    lines = []
    current_line = []
    for w in words:
        current_line.append(w)
        if len(" ".join(current_line)) > 22:
            lines.append(" ".join(current_line[:-1]))
            current_line = [w]
    if current_line:
        lines.append(" ".join(current_line))

    text_y = height // 2 + 160
    for line in lines:
        draw.text((width // 2, text_y), line, fill=(23, 23, 23), font=title_font, anchor="mm")
        text_y += 44

    # Subtitle text
    if subtitle:
        sub_font = get_font(20)
        draw.text((width // 2, text_y + 15), subtitle, fill=(107, 107, 107), font=sub_font, anchor="mm")

    # Bottom minimal watermark
    foot_font = get_font(16)
    draw.text((width // 2, height - 60), "CURATED ESSENTIALS", fill=(130, 130, 130), font=foot_font, anchor="mm")

    img.save(target_path, 'JPEG', quality=95)


class Command(BaseCommand):
    help = 'Seeds categories and products idempotently with real ₹ pricing and local images'

    def handle(self, *args, **options):
        self.stdout.write("Seeding Cartza database...")

        seed_images_dir = os.path.join(settings.BASE_DIR, 'seed_images')
        media_products_dir = os.path.join(settings.MEDIA_ROOT, 'products')
        media_categories_dir = os.path.join(settings.MEDIA_ROOT, 'categories')
        media_hero_dir = os.path.join(settings.MEDIA_ROOT, 'hero')

        os.makedirs(media_products_dir, exist_ok=True)
        os.makedirs(media_categories_dir, exist_ok=True)
        os.makedirs(media_hero_dir, exist_ok=True)

        # Generate Hero Image
        hero_target = os.path.join(media_hero_dir, 'hero_curated.jpg')
        if not os.path.exists(hero_target):
            generate_pillow_image(
                hero_target,
                title="Curated Modern Living",
                subtitle="Autumn / Everyday Collection",
                category_name="Lifestyle",
                width=800,
                height=1000
            )

        data = [
            {
                'category': 'Fashion',
                'description': 'Elevated essentials and tailored garments designed for enduring comfort and timeless aesthetics.',
                'products': [
                    {
                        'name': 'Structured Linen Overshirt',
                        'price': Decimal('2899.00'),
                        'compare_at_price': Decimal('3499.00'),
                        'stock': 18,
                        'is_featured': True,
                        'is_bestseller': True,
                        'available_sizes': 'S, M, L, XL',
                        'available_colors': 'Natural Oat, Olive, Charcoal',
                        'description': 'Crafted from pure Belgian flax linen with twin utility chest pockets and horn buttons. Perfect for relaxed layering across seasons.',
                        'specifications': {
                            'Material': '100% Belgian Linen',
                            'Fit': 'Relaxed Overshirt Fit',
                            'Care': 'Machine wash cold on gentle cycle',
                            'Origin': 'Sustainably Crafted in India'
                        }
                    },
                    {
                        'name': 'Heavyweight Organic Cotton Tee',
                        'price': Decimal('1299.00'),
                        'compare_at_price': Decimal('1499.00'),
                        'stock': 42,
                        'is_featured': True,
                        'is_bestseller': True,
                        'available_sizes': 'XS, S, M, L, XL, XXL',
                        'available_colors': 'Off-White, Raw Umber, Black',
                        'description': 'A dense 260 GSM combed organic cotton t-shirt with reinforced ribbed collar and clean blind-stitched hems.',
                        'specifications': {
                            'Material': '100% GOTS Certified Organic Cotton',
                            'Weight': '260 GSM Heavyweight',
                            'Care': 'Pre-shrunk, wash at 30°C',
                            'Origin': 'Tiruppur, India'
                        }
                    },
                    {
                        'name': 'Pleated Relaxed Trousers',
                        'price': Decimal('3299.00'),
                        'compare_at_price': None,
                        'stock': 14,
                        'is_featured': False,
                        'is_bestseller': False,
                        'available_sizes': '30, 32, 34, 36',
                        'available_colors': 'Charcoal, Khaki Stone',
                        'description': 'Contemporary wide-tapered silhouette cut in a breathable wool-blend twill with front pleats and side adjusters.',
                        'specifications': {
                            'Material': '60% Recycled Wool, 40% Tencel',
                            'Rise': 'High Rise',
                            'Closure': 'Concealed zip fly and horn clasp',
                            'Origin': 'Crafted in India'
                        }
                    },
                    {
                        'name': 'Minimalist Merino Wool Knit',
                        'price': Decimal('4199.00'),
                        'compare_at_price': Decimal('4999.00'),
                        'stock': 8,
                        'is_featured': True,
                        'is_bestseller': False,
                        'available_sizes': 'S, M, L',
                        'available_colors': 'Espresso, Fog Grey',
                        'description': 'Extra-fine 19.5 micron Australian Merino wool crewneck knit with ribbed cuffs and subtle rolled neckline.',
                        'specifications': {
                            'Material': '100% Extra-fine Merino Wool',
                            'Gauge': '12 Gauge Fine Knit',
                            'Care': 'Dry clean or hand wash flat',
                            'Origin': 'Ludhiana, India'
                        }
                    },
                    {
                        'name': 'Tailored Trench Coat (Limited)',
                        'price': Decimal('7499.00'),
                        'compare_at_price': Decimal('8999.00'),
                        'stock': 0,  # Out of stock example
                        'is_featured': False,
                        'is_bestseller': False,
                        'available_sizes': 'M, L',
                        'available_colors': 'Sand Dune, Midnight',
                        'description': 'Double-breasted storm-flap trench coat cut from water-repellent gabardine with removable tonal waist belt.',
                        'specifications': {
                            'Material': '100% Weatherproof Cotton Gabardine',
                            'Lining': 'Viscose twill',
                            'Length': 'Mid-calf length',
                            'Status': 'Restock arriving next month'
                        }
                    }
                ]
            },
            {
                'category': 'Shoes',
                'description': 'Artisan footwear built with premium leathers, ergonomic footbeds, and timeless silhouettes.',
                'products': [
                    {
                        'name': 'Handcrafted Derby Leather Shoes',
                        'price': Decimal('5499.00'),
                        'compare_at_price': Decimal('6499.00'),
                        'stock': 12,
                        'is_featured': True,
                        'is_bestseller': True,
                        'available_sizes': 'UK 7, UK 8, UK 9, UK 10, UK 11',
                        'available_colors': 'Burnished Chestnut, Matte Black',
                        'description': 'Full-grain calfskin derby shoes constructed with Blake stitch welt, cork filler, and stacked leather heels.',
                        'specifications': {
                            'Upper': 'Full-Grain Calf Leather',
                            'Sole': 'Goodyear Welt Leather & Rubber Toplift',
                            'Lining': 'Full Calf Leather Interior',
                            'Origin': 'Agra, India'
                        }
                    },
                    {
                        'name': 'Court Classic Leather Sneakers',
                        'price': Decimal('3799.00'),
                        'compare_at_price': Decimal('4299.00'),
                        'stock': 25,
                        'is_featured': True,
                        'is_bestseller': True,
                        'available_sizes': 'UK 7, UK 8, UK 9, UK 10',
                        'available_colors': 'White / Alabaster, White / Forest',
                        'description': 'Low-top minimalist sneakers with buttery nappa leather upper, stitched cupsole, and antimicrobial Ortholite insole.',
                        'specifications': {
                            'Upper': 'Italian Nappa Leather',
                            'Sole': 'Natural Vulcanized Rubber',
                            'Laces': 'Waxed Organic Cotton',
                            'Origin': 'Crafted in India'
                        }
                    },
                    {
                        'name': 'Suede Chelsea Boots',
                        'price': Decimal('5999.00'),
                        'compare_at_price': None,
                        'stock': 10,
                        'is_featured': False,
                        'is_bestseller': False,
                        'available_sizes': 'UK 8, UK 9, UK 10',
                        'available_colors': 'Warm Taupe, Dark Snuff',
                        'description': 'Hand-treated water-resistant reverse suede with elasticated side gussets and heavy-duty herringbone pull tabs.',
                        'specifications': {
                            'Upper': 'Waterproofed Calf Suede',
                            'Sole': 'Dainite Rubber Lug Soles',
                            'Insole': 'Cushioned Vegetable-Tanned Insole',
                            'Origin': 'Crafted in India'
                        }
                    },
                    {
                        'name': 'Minimalist Leather Slide Sandals',
                        'price': Decimal('2199.00'),
                        'compare_at_price': Decimal('2699.00'),
                        'stock': 19,
                        'is_featured': False,
                        'is_bestseller': False,
                        'available_sizes': 'UK 7, UK 8, UK 9, UK 10',
                        'available_colors': 'Oiled Tan, Pitch Black',
                        'description': 'Wide cross-strap slide sandals with contoured memory foam footbed and non-slip textured rubber outsole.',
                        'specifications': {
                            'Material': 'Vegetable-Tanned Cowhide',
                            'Footbed': 'Ergonomic Arch Support',
                            'Weight': '320g per shoe',
                            'Origin': 'Crafted in India'
                        }
                    }
                ]
            },
            {
                'category': 'Accessories',
                'description': 'Functional daily carry goods, vegetable-tanned leather pieces, and refined accents.',
                'products': [
                    {
                        'name': 'Top-Grain Leather Commuter Tote',
                        'price': Decimal('4499.00'),
                        'compare_at_price': Decimal('5299.00'),
                        'stock': 16,
                        'is_featured': True,
                        'is_bestseller': True,
                        'available_sizes': 'One Size (16L)',
                        'available_colors': 'Cognac, Matte Black',
                        'description': 'Structured tote bag featuring padded 15-inch laptop sleeve, key leash, internal water bottle pocket, and YKK Excella zippers.',
                        'specifications': {
                            'Material': 'Full-Grain Oil Pull-up Leather',
                            'Capacity': '16 Litres',
                            'Laptop Sleeve': 'Up to 15.6 inch MacBook / Laptop',
                            'Hardware': 'Solid Brass with Antique Finish'
                        }
                    },
                    {
                        'name': 'Slim Bifold Card Wallet',
                        'price': Decimal('1199.00'),
                        'compare_at_price': Decimal('1499.00'),
                        'stock': 35,
                        'is_featured': False,
                        'is_bestseller': True,
                        'available_sizes': 'One Size',
                        'available_colors': 'Tobacco Tan, Forest Green',
                        'description': 'Ultra-slim wallet with 6 card slots, central cash compartment, and RFID shielding lining.',
                        'specifications': {
                            'Material': 'Vegetable Tanned Leather',
                            'Thickness': '0.7 cm empty',
                            'Protection': 'RFID Blocking Core',
                            'Warranty': '2 Year Craftsmanship Guarantee'
                        }
                    },
                    {
                        'name': 'Italian Acetate Square Sunglasses',
                        'price': Decimal('2999.00'),
                        'compare_at_price': Decimal('3499.00'),
                        'stock': 22,
                        'is_featured': True,
                        'is_bestseller': False,
                        'available_sizes': 'Standard (49-21-145)',
                        'available_colors': 'Tortoiseshell, Matte Black',
                        'description': 'Handmade plant-based Mazzucchelli acetate sunglasses with 100% UV400 category 3 scratch-resistant CR-39 lenses.',
                        'specifications': {
                            'Frame': 'Mazzucchelli 1849 Bio-Acetate',
                            'Lenses': 'Polarized UV400 CR-39',
                            'Hinges': '5-barrel German Engineered',
                            'Case': 'Includes Hard Leather Case & Microfibre Cloth'
                        }
                    },
                    {
                        'name': 'Merino Wool Woven Scarf',
                        'price': Decimal('1799.00'),
                        'compare_at_price': None,
                        'stock': 0,  # Out of stock example
                        'is_featured': False,
                        'is_bestseller': False,
                        'available_sizes': '180 x 35 cm',
                        'available_colors': 'Oatmeal Melange, Navy Glen',
                        'description': 'Featherlight pure merino wool scarf woven on traditional shuttle looms with eyelash fringed borders.',
                        'specifications': {
                            'Material': '100% Pure Merino Wool',
                            'Dimensions': '180 cm x 35 cm',
                            'Care': 'Gentle Hand Wash in Cold Water',
                            'Origin': 'Kashmir, India'
                        }
                    }
                ]
            },
            {
                'category': 'Electronics',
                'description': 'Modern desktop and acoustic essentials combining precision acoustics with minimalist industrial design.',
                'products': [
                    {
                        'name': 'Acoustic Walnut Desk Speakers',
                        'price': Decimal('8999.00'),
                        'compare_at_price': Decimal('10999.00'),
                        'stock': 9,
                        'is_featured': True,
                        'is_bestseller': True,
                        'available_sizes': 'Stereo Pair',
                        'available_colors': 'Solid Walnut / Matte Black',
                        'description': 'Active studio monitors with hand-finished solid walnut enclosures, Bluetooth 5.2 aptX HD, and 60W RMS balanced output.',
                        'specifications': {
                            'Drivers': '3-inch Kevlar Woofers, 0.75-inch Silk Tweeters',
                            'Output': '60W RMS (Peak 100W)',
                            'Inputs': 'Optical, RCA, AUX, Bluetooth aptX HD',
                            'Enclosure': 'Solid American Walnut'
                        }
                    },
                    {
                        'name': 'Over-Ear ANC Wireless Headphones',
                        'price': Decimal('7499.00'),
                        'compare_at_price': Decimal('8999.00'),
                        'stock': 15,
                        'is_featured': True,
                        'is_bestseller': True,
                        'available_sizes': 'Adjustable',
                        'available_colors': 'Silver Sand, Obsidian',
                        'description': 'Studio precision headphones featuring hybrid active noise cancellation, 40-hour battery runtime, and memory-foam leather cups.',
                        'specifications': {
                            'Drivers': '40mm Custom Bio-Cellulose',
                            'Battery': '40 Hours with ANC On (USB-C Fast Charge)',
                            'Connectivity': 'Bluetooth 5.3 Multipoint',
                            'Weight': '248g'
                        }
                    },
                    {
                        'name': 'Anodized Aluminium Laptop Stand',
                        'price': Decimal('1999.00'),
                        'compare_at_price': Decimal('2499.00'),
                        'stock': 28,
                        'is_featured': False,
                        'is_bestseller': False,
                        'available_sizes': 'Universal 11"-16"',
                        'available_colors': 'Space Grey, Silver',
                        'description': 'Precision CNC-machined aerospace aluminium stand designed to elevate your display to eye level and improve airflow.',
                        'specifications': {
                            'Material': 'Sandblasted Anodized 6061 Aluminium',
                            'Pads': 'Non-slip Silicone Surface Inlays',
                            'Elevation': 'Raises screen by 15 cm at 18° angle',
                            'Weight': '680g'
                        }
                    },
                    {
                        'name': 'Braided USB-C Fast Charging Cable Set',
                        'price': Decimal('899.00'),
                        'compare_at_price': Decimal('1099.00'),
                        'stock': 50,
                        'is_featured': False,
                        'is_bestseller': False,
                        'available_sizes': '1.2m + 2.0m Pack',
                        'available_colors': 'Slate Grey, Bone',
                        'description': 'Durable Kevlar-reinforced braided nylon cables rated up to 100W Power Delivery and 480Mbps data transfer speeds.',
                        'specifications': {
                            'Power Delivery': '100W (20V/5A) E-Marker Chip',
                            'Durability': 'Tested for 25,000+ bends',
                            'Included': 'Integrated Silicone Cable Organizers',
                            'Warranty': '3 Years Replacement'
                        }
                    }
                ]
            },
            {
                'category': 'Home & Living',
                'description': 'Ceramics, architectural lighting, and home objects crafted to bring calm and tactile warmth.',
                'products': [
                    {
                        'name': 'Hand-Thrown Ceramic Table Lamp',
                        'price': Decimal('3699.00'),
                        'compare_at_price': Decimal('4299.00'),
                        'stock': 11,
                        'is_featured': True,
                        'is_bestseller': False,
                        'available_sizes': 'H: 38cm, D: 22cm',
                        'available_colors': 'Textured Stone, Terracotta',
                        'description': 'Tactile stoneware base thrown on the wheel with a raw matte exterior, fitted with a natural linen drum shade and warm LED dimmer.',
                        'specifications': {
                            'Base Material': 'Stoneware Clay with Reactive Slip',
                            'Shade': '100% Unbleached Linen',
                            'Socket': 'Standard E27 with In-line Brass Dimmer',
                            'Bulb': 'Included 2700K Warm LED'
                        }
                    },
                    {
                        'name': 'Stoneware Pour-Over Carafe Set',
                        'price': Decimal('2299.00'),
                        'compare_at_price': Decimal('2799.00'),
                        'stock': 24,
                        'is_featured': False,
                        'is_bestseller': True,
                        'available_sizes': '600 ml',
                        'available_colors': 'Speckled Oatmeal, Slate',
                        'description': 'Ceramic slow-coffee dripper with matching 600ml pouring jug, engineered with spiral interior ridges for optimum extraction.',
                        'specifications': {
                            'Material': 'High-Fired Food-Safe Ceramic',
                            'Capacity': '600 ml (2-3 Cups)',
                            'Compatibility': 'Standard V60 02 filter papers',
                            'Dishwasher': 'Dishwasher and Microwave Safe'
                        }
                    },
                    {
                        'name': 'Waffle Weave Cotton Throw Blanket',
                        'price': Decimal('2499.00'),
                        'compare_at_price': None,
                        'stock': 18,
                        'is_featured': True,
                        'is_bestseller': False,
                        'available_sizes': '150 x 200 cm',
                        'available_colors': 'Earthy Sand, Olive Moss',
                        'description': 'Generously sized 450 GSM three-dimensional waffle weave blanket woven from long-staple Indian cotton with fringe ends.',
                        'specifications': {
                            'Material': '100% Combed Indian Cotton',
                            'Dimensions': '150 cm x 200 cm',
                            'Weight': '1.35 kg',
                            'Care': 'Machine wash cold, tumble dry low'
                        }
                    },
                    {
                        'name': 'Architectural Concrete Wall Clock',
                        'price': Decimal('2199.00'),
                        'compare_at_price': Decimal('2599.00'),
                        'stock': 14,
                        'is_featured': False,
                        'is_bestseller': False,
                        'available_sizes': 'Diameter: 30 cm',
                        'available_colors': 'Cast Grey Concrete',
                        'description': 'Cast ultra-dense architectural concrete dial with recessed hour markers, continuous-sweep silent Japanese quartz movement, and walnut hands.',
                        'specifications': {
                            'Dial': 'Glass-Fiber Reinforced Architectural Concrete',
                            'Hands': 'Solid Black Walnut',
                            'Movement': 'Silent Non-Ticking Quartz (1x AA)',
                            'Weight': '1.6 kg'
                        }
                    }
                ]
            },
            {
                'category': 'Lifestyle',
                'description': 'Everyday tools, botanicals, and conscious accessories for mindful living.',
                'products': [
                    {
                        'name': 'Double-Walled Insulated Flask',
                        'price': Decimal('1499.00'),
                        'compare_at_price': Decimal('1799.00'),
                        'stock': 32,
                        'is_featured': True,
                        'is_bestseller': True,
                        'available_sizes': '750 ml',
                        'available_colors': 'Desert Clay, Moss, Charcoal',
                        'description': 'Grade 304 stainless steel thermos with triple-layer vacuum insulation keeping beverages cold for 24 hours or piping hot for 12 hours.',
                        'specifications': {
                            'Material': 'Food-Grade 18/8 Stainless Steel',
                            'Cap': 'BPA-Free Silicone Sealed Lid with Carry Loop',
                            'Insulation': '24h Cold / 12h Hot Thermal Retention',
                            'Finish': 'Durable Matte Powder Coat'
                        }
                    },
                    {
                        'name': 'Soy Wax & Amber Botanical Candle',
                        'price': Decimal('899.00'),
                        'compare_at_price': Decimal('1099.00'),
                        'stock': 40,
                        'is_featured': False,
                        'is_bestseller': True,
                        'available_sizes': '280g (55h Burn Time)',
                        'available_colors': 'Amber Glass Vessel',
                        'description': 'Hand-poured 100% biodegradable golden soy wax scented with cedarwood, crushed cardamoms, and black amber, with crackling FSC wood wick.',
                        'specifications': {
                            'Wax': '100% Plant-Based Soy Wax',
                            'Wick': 'Natural FSC Certified Wooden Wick',
                            'Burn Time': '55 Hours',
                            'Vessel': 'Reusable Apothecary Amber Glass Jar'
                        }
                    },
                    {
                        'name': 'Japanese Canvas Field Journal',
                        'price': Decimal('999.00'),
                        'compare_at_price': None,
                        'stock': 26,
                        'is_featured': False,
                        'is_bestseller': False,
                        'available_sizes': 'A5 (148 x 210 mm)',
                        'available_colors': 'Olive Drab, Khaki Sand',
                        'description': 'Hardcover notebook wrapped in water-resistant paraffin duck canvas filled with 192 pages of fountain-pen-friendly 100 GSM acid-free paper.',
                        'specifications': {
                            'Cover': '10oz Waxed Cotton Canvas',
                            'Paper': '100 GSM Bleed-Proof Dot Grid Paper',
                            'Pages': '192 Numbered Pages with 2 Ribbon Bookmarks',
                            'Binding': 'Lay-Flat Thread Bound'
                        }
                    },
                    {
                        'name': 'Matte Ceramic Pourer & Mister Set',
                        'price': Decimal('1699.00'),
                        'compare_at_price': Decimal('1999.00'),
                        'stock': 15,
                        'is_featured': False,
                        'is_bestseller': False,
                        'available_sizes': 'Pourer: 1L, Mister: 300ml',
                        'available_colors': 'Bone White, Sage',
                        'description': 'Pair of indoor plant care tools comprising a long-spouted ceramic watering vessel and an ultra-fine brass mister pump.',
                        'specifications': {
                            'Materials': 'High-Density Ceramic & Solid Brass Pump',
                            'Finish': 'Satin Glazed Ceramic',
                            'Nozzle': 'Micro-Fine Mist Atomizer',
                            'Origin': 'Crafted in India'
                        }
                    }
                ]
            }
        ]

        total_cats = 0
        total_prods = 0

        for cat_data in data:
            cat_name = cat_data['category']
            cat_slug = slugify(cat_name)
            cat_desc = cat_data['description']

            category, _ = Category.objects.update_or_create(
                slug=cat_slug,
                defaults={
                    'name': cat_name,
                    'description': cat_desc,
                }
            )
            total_cats += 1

            # Category Image check: look in seed_images/ or generate with Pillow
            cat_img_rel = f"categories/{cat_slug}.jpg"
            cat_img_full = os.path.join(settings.MEDIA_ROOT, cat_img_rel)
            seed_cat_img = os.path.join(seed_images_dir, f"{cat_slug}.jpg")

            if os.path.exists(seed_cat_img):
                shutil.copy2(seed_cat_img, cat_img_full)
                category.image = cat_img_rel
                category.save()
            elif not category.image or not os.path.exists(cat_img_full):
                generate_pillow_image(
                    cat_img_full,
                    title=cat_name,
                    subtitle="Explore Collection",
                    category_name=cat_name,
                    width=800,
                    height=1000
                )
                category.image = cat_img_rel
                category.save()

            for p_info in cat_data['products']:
                prod_slug = slugify(p_info['name'])
                product, _ = Product.objects.update_or_create(
                    slug=prod_slug,
                    defaults={
                        'category': category,
                        'name': p_info['name'],
                        'price': p_info['price'],
                        'compare_at_price': p_info['compare_at_price'],
                        'stock': p_info['stock'],
                        'is_active': True,
                        'is_featured': p_info.get('is_featured', False),
                        'is_bestseller': p_info.get('is_bestseller', False),
                        'description': p_info['description'],
                        'specifications': p_info.get('specifications', {}),
                        'available_sizes': p_info.get('available_sizes', ''),
                        'available_colors': p_info.get('available_colors', ''),
                    }
                )
                total_prods += 1

                # Product Image check: look in seed_images/ or generate with Pillow
                prod_img_rel = f"products/{prod_slug}.jpg"
                prod_img_full = os.path.join(settings.MEDIA_ROOT, prod_img_rel)
                seed_prod_img = os.path.join(seed_images_dir, f"{prod_slug}.jpg")

                if os.path.exists(seed_prod_img):
                    shutil.copy2(seed_prod_img, prod_img_full)
                elif not os.path.exists(prod_img_full):
                    generate_pillow_image(
                        prod_img_full,
                        title=product.name,
                        subtitle=f"₹{product.price}",
                        category_name=cat_name,
                        width=800,
                        height=1000
                    )

                # Attach ProductImage if not already attached
                ProductImage.objects.update_or_create(
                    product=product,
                    is_primary=True,
                    defaults={
                        'image': prod_img_rel,
                        'alt_text': product.name,
                    }
                )

        self.stdout.write(self.style.SUCCESS(
            f"Successfully seeded {total_cats} categories and {total_prods} products idempotently!"
        ))
