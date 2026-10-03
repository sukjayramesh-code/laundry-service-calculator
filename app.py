import pandas as pd
import streamlit as st

from logic import (
    SERVICE_RATES, DELIVERY_FEES, InvalidInputError, Order, ExpressOrder,
    validate_inputs, calculate_total, get_discount_rate, generate_receipt,
)

st.set_page_config(page_title="Laundry Service Calculator", layout="centered")


if "orders" not in st.session_state:
    st.session_state.orders = []
if "event_msg" not in st.session_state:
    st.session_state.event_msg = ""


def on_service_change():
    service = st.session_state.service
    st.session_state.event_msg = f"{service}: RM {SERVICE_RATES[service]:.2f} per kg"


def on_delivery_change():
    option = st.session_state.delivery
    st.session_state.event_msg = f"{option}: delivery fee RM {DELIVERY_FEES[option]:.2f}"


def on_express_change():
    if st.session_state.express:
        st.session_state.event_msg = "Express selected: +50% surcharge, ready in 1 day"
    else:
        st.session_state.event_msg = "Regular order: ready in 2 days"


def clear_history():
    st.session_state.orders = []


st.title("Laundry Service Calculator")
st.caption("Calculate your laundry price instantly - Regular or Express service.")

with st.sidebar:
    st.header("Price List")
    st.table(pd.DataFrame(
        {"RM / kg": [f"{v:.2f}" for v in SERVICE_RATES.values()]},
        index=list(SERVICE_RATES.keys()),
    ))
    st.write("**Discounts:** 5% for 5 kg and above, 10% for 10 kg and above.")
    st.write("**Express:** +50% surcharge, ready in 1 day.")
    st.write("**SST:** 6% on all orders.")


col1, col2 = st.columns(2)
with col1:
    name = st.text_input("Customer Name *")
with col2:
    phone = st.text_input("Phone Number *", placeholder="012-3456789")

weight_text = st.text_input("Laundry Weight (kg) *", placeholder="e.g. 5.5")

service = st.selectbox("Service Type", list(SERVICE_RATES.keys()),
                       key="service", on_change=on_service_change)
delivery = st.radio("Delivery Option", list(DELIVERY_FEES.keys()),
                    key="delivery", on_change=on_delivery_change, horizontal=True)
express = st.checkbox("Express Service (+50%, ready in 1 day)",
                      key="express", on_change=on_express_change)

if st.session_state.event_msg:
    st.info(st.session_state.event_msg)


if st.button("Calculate Total", type="primary"):
    try:
        weight = validate_inputs(name, phone, weight_text)

        order_class = ExpressOrder if express else Order
        order = order_class(name.strip(), phone.strip(), weight, service, delivery)

        discount_rate = get_discount_rate(weight)
        breakdown = calculate_total(order.calculate_subtotal(),
                                    order.get_delivery_fee(), discount_rate)
        receipt = generate_receipt(order, breakdown, discount_rate)

        st.session_state.orders.append(order.to_record(breakdown))
        st.session_state.last_receipt = receipt

        st.success(f"{order.get_order_type()} order created for {order.customer_name}!")
        m1, m2, m3 = st.columns(3)
        m1.metric("Subtotal", f"RM {breakdown['subtotal']:.2f}")
        m2.metric("Total", f"RM {breakdown['total']:.2f}")
        m3.metric("Ready By", order.get_ready_date())
        st.code(receipt, language=None)

    except InvalidInputError as err:
        st.error(f"Input error: {err}")
    except Exception as err:
        st.error(f"Unexpected error: {err}")

if "last_receipt" in st.session_state and st.session_state.orders:
    st.download_button("Download Receipt", st.session_state.last_receipt,
                       file_name="receipt.txt")


if st.session_state.orders:
    st.subheader("Order History")
    df = pd.DataFrame(st.session_state.orders)
    st.dataframe(df, width="stretch", hide_index=True)
    st.write(f"**Orders:** {len(df)}   |   **Total sales:** RM {df['Total (RM)'].sum():.2f}")
    st.button("Clear History", on_click=clear_history)