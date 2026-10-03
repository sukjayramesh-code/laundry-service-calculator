from datetime import datetime, timedelta


SERVICE_RATES = {
    "Wash & Fold": 4.00,
    "Wash & Iron": 6.00,
    "Dry Clean": 12.00,
    "Iron Only": 3.00,
}
DELIVERY_FEES = {
    "Self Pickup": 0.00,
    "Home Delivery": 5.00,
}
SST_RATE = 0.06
MAX_WEIGHT = 50.0


class InvalidInputError(Exception):
    pass


def validate_inputs(name, phone, weight_text):
    if not name.strip() or not phone.strip() or not weight_text.strip():
        raise InvalidInputError("All required fields must be filled in.")

    if not any(ch.isalpha() for ch in name):
        raise InvalidInputError("Customer name must contain letters.")

    digits = phone.replace("-", "").replace(" ", "")
    if not digits.isdigit() or not 9 <= len(digits) <= 11:
        raise InvalidInputError("Phone number must contain 9 to 11 digits (e.g. 012-3456789).")

    try:
        weight = float(weight_text)
    except ValueError:
        raise InvalidInputError("Weight must be a number (e.g. 5 or 7.5).")

    if weight <= 0:
        raise InvalidInputError("Weight must be greater than 0 kg.")
    if weight > MAX_WEIGHT:
        raise InvalidInputError(f"Weight cannot exceed {MAX_WEIGHT:.0f} kg per order.")
    return weight


def calculate_total(subtotal, delivery_fee, discount_rate=0.0, tax_rate=SST_RATE):
    discount = round(subtotal * discount_rate, 2)
    taxable = subtotal - discount + delivery_fee
    tax = round(taxable * tax_rate, 2)
    total = round(taxable + tax, 2)
    return {
        "subtotal": round(subtotal, 2),
        "discount": discount,
        "delivery": round(delivery_fee, 2),
        "tax": tax,
        "total": total,
    }


def get_discount_rate(weight_kg):
    if weight_kg >= 10:
        return 0.10
    elif weight_kg >= 5:
        return 0.05
    return 0.0


def generate_receipt(order, breakdown, discount_rate):
    lines = [
        "=" * 36,
        "        LAUNDRY SERVICE RECEIPT",
        "=" * 36,
        f"Order ID   : {order.order_id}",
        f"Customer   : {order.customer_name}",
        f"Phone      : {order.phone}",
        f"Order Type : {order.get_order_type()}",
        f"Service    : {order.service_type}",
        f"Weight     : {order.weight_kg:.1f} kg",
        f"Delivery   : {order.delivery_option}",
        f"Ready By   : {order.get_ready_date()}",
        "-" * 36,
        f"Subtotal         : RM {breakdown['subtotal']:>8.2f}",
        f"Discount ({discount_rate * 100:.0f}%)   : RM {breakdown['discount']:>8.2f}",
        f"Delivery Fee     : RM {breakdown['delivery']:>8.2f}",
        f"SST (6%)         : RM {breakdown['tax']:>8.2f}",
        "-" * 36,
        f"TOTAL            : RM {breakdown['total']:>8.2f}",
        "=" * 36,
    ]
    return "\n".join(lines)


class Order:

    def __init__(self, customer_name, phone, weight_kg, service_type, delivery_option):
        self.order_id = "LD" + datetime.now().strftime("%y%m%d%H%M%S")
        self.customer_name = customer_name
        self.phone = phone
        self.weight_kg = weight_kg
        self.service_type = service_type
        self.delivery_option = delivery_option
        self.turnaround_days = 2

    def get_rate(self):
        return SERVICE_RATES[self.service_type]

    def calculate_subtotal(self):
        return round(self.weight_kg * self.get_rate(), 2)

    def get_delivery_fee(self):
        return DELIVERY_FEES[self.delivery_option]

    def get_order_type(self):
        return "Regular"

    def get_ready_date(self):
        ready = datetime.now() + timedelta(days=self.turnaround_days)
        return ready.strftime("%d %b %Y")

    def to_record(self, breakdown):
        return {
            "Order ID": self.order_id,
            "Customer": self.customer_name,
            "Type": self.get_order_type(),
            "Service": self.service_type,
            "Weight (kg)": self.weight_kg,
            "Delivery": self.delivery_option,
            "Total (RM)": breakdown["total"],
        }


class ExpressOrder(Order):

    SURCHARGE_RATE = 0.50

    def __init__(self, customer_name, phone, weight_kg, service_type, delivery_option):
        super().__init__(customer_name, phone, weight_kg, service_type, delivery_option)
        self.turnaround_days = 1

    def get_surcharge(self):
        return round(super().calculate_subtotal() * self.SURCHARGE_RATE, 2)

    def calculate_subtotal(self):
        return round(super().calculate_subtotal() + self.get_surcharge(), 2)

    def get_order_type(self):
        return "Express"