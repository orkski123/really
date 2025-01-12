import streamlit as st
import pandas as pd
import json
import utility as ut
import database as db

from datetime import datetime

# Page configuration
st.set_page_config(page_title="ระบบจัดการร้านอาหาร",page_icon="🍜",layout="wide")
st.markdown('<style>div.block-container{padding-top:1.85rem;}</style>', unsafe_allow_html=True)

from streamlit_extras.image_in_tables import table_with_images

# Initialize session state
if 'client' not in st.session_state:
    st.session_state.client = db.init_google_sheets()

if 'current_page' not in st.session_state:
    st.session_state.current_page = 'orders'

@st.dialog("เพิ่มข้อมูลสินค้า")
def show_dialogAddProd():
    cols = st.columns([2,3,2,1],vertical_alignment="top")
    id = cols[0].text_input("รหัสสินค้า")
    name = cols[1].text_input("ชื่อสินค้า")
    price = cols[2].number_input("ราคา", min_value=0.0, step=0.5)
    qty = cols[3].number_input("จำนวน", min_value=0, step=1)
    category = st.selectbox("แบรนด์", ["Rinnai", "Electrolux", "Lucky Flame", "Seagull", "MEX","Teka"])
   
    # Image upload
    uploaded_file = st.file_uploader("อัปโหลดรูปภาพสินค้า", type=['png', 'jpg', 'jpeg'])
    image_url = None
   
    if uploaded_file:
        image_url = ut.upload_image_to_cloudinary(uploaded_file)
        if image_url:
            st.image(uploaded_file, caption="รูปภาพที่อัปโหลด", width=200)
   
    if st.button("เพิ่มสินค้า",type="primary",key="add_product"):
        if name and price > 0 and image_url:
            db.save_product(id,name, price, category, image_url,qty)
            st.rerun()
        else:
            st.warning("กรุณากรอกข้อมูลให้ครบถ้วน")

@st.dialog("แก้ไขข้อมูลสินค้า")
def show_dialogEditProd(row_idx,product):
    # products = db.load_products()
    # Edit Form (Key change is here)
    if product:
        with st.form(key=f"edit_form_{product['id']}"):
            cols = st.columns([2,3,2,1],vertical_alignment="top")
            edit_id = cols[0].text_input("รหัสสินค้า", value=product['id'])
            edit_name = cols[1].text_input("ชื่อสินค้า", value=product['name'])
            edit_price = cols[2].number_input("ราคา", min_value=0.0, step=1.0, value=float(product['price']))
            edit_qty = cols[3].number_input("จำนวน", min_value=0, step=1 , value = int(product['qty']))
            edit_category = st.selectbox("หมวดหมู่", ["Rinnai", "Electrolux", "Lucky Flame", "Seagull", "MEX","Teka"], index=["Rinnai", "Electrolux", "Lucky Flame", "Seagull", "MEX","Teka"].index(product["category"]))
            edit_status = st.selectbox("สถานะ", ["active", "inactive"], index=0 if product['status'] == 'active' else 1)
            edit_image_file = st.file_uploader("เปลี่ยนรูปภาพสินค้า", type=['png', 'jpg', 'jpeg'])

            if edit_image_file:
                edit_image_url = ut.upload_image_to_cloudinary(edit_image_file)
            else:
                edit_image_url = product['image_url']
           
            if st.form_submit_button("บันทึก"):
                db.update_product(row_idx,edit_id, edit_name, edit_price, edit_category, edit_status, edit_image_url,edit_qty)
                st.success('อัพเดตข้อมูลสินค้าเรียบร้อยแล้ว')
                st.rerun()
                       
def product_management_page():
    col1,col2 = st.columns([5,1],vertical_alignment="bottom")
    col1.title("🍜 จัดการสินค้า")
    with col2:
        if (st.button('เพิ่มสินค้า',type="primary")):
            show_dialogAddProd()
               
    st.subheader("รายการสินค้าทั้งหมด")
    products = db.load_products()
    # st.write(products)
    products_df = pd.DataFrame.from_dict(pd.json_normalize(products))
    # แสดงรายการสินค้ารูปแบบตาราง
    # df_html = table_with_images(products_df, url_columns=('image_url',))
    # st.markdown(df_html, unsafe_allow_html=True)
   
    if products:
        # แสดงข้อมูลเป็นกริด 4 คอลัมบ์
        cols = st.columns(4,vertical_alignment='top',gap='medium')
        for idx, product in enumerate(products): # Iterate over a copy
            with cols[idx % 4]:
                st.image(product['image_url'],caption=f"{product['id']} - {product['name']}",width=200)
                st.markdown(f"##### ราคา: ฿{product['price']:.2f}")
                st.markdown(f"##### จำนวน: {product['qty']:}")
                st.write(f"หมวดหมู่: {product['category']}")
                colb1,colb2 = st.columns([3,2])
                with colb1:
                    if st.button("แก้ไข",key=f"edit_{idx}",type="primary"):
                        show_dialogEditProd(idx,product)
                with colb2:
                    if st.button("ลบ", key=f"delete_{idx}",type="primary"):
                        products = db.delete_product(idx, products)
                        st.success('ลบสินค้าสำเร็จ')
                        st.rerun()

    else:
        st.info("ยังไม่มีสินค้า")

# UI Components
def sidebar_menu():
    st.sidebar.image("imi-logo.png",width=180)
    st.sidebar.title("เมนูหลัก")
    pages = {
        'orders': '📝 รายการสั่งซื้อ',
        'products': '🍜 จัดการสินค้า',
        'order_management': '📊 จัดการออเดอร์'
    }
   
    for page_id, page_name in pages.items():
        if st.sidebar.button(page_name):
            st.session_state.current_page = page_id
            st.rerun()

def order_page():
    st.title("📝 สั่งซื้อสินค้า")
    products = db.load_products()
    active_products = [p for p in products if p['status'] == 'active'] #กรองสินค้าที่พร้อมขาย
   
    if not active_products:
        st.warning("ไม่มีสินค้าที่พร้อมขาย กรุณาเพิ่มสินค้าก่อน")
        return
    col1,col2 = st.columns([4,2],vertical_alignment="top")
    with col1:
        # Display products in a grid
        st.subheader("รายการสินค้า")
        cols = st.columns(3,vertical_alignment="top",gap='small')
        if 'order_items' not in st.session_state:
            st.session_state.order_items = {} # Initialize outside the loop
        for idx, product in enumerate(active_products):
            with cols[idx % 3]:
                st.image(product['image_url'],caption=f"{product['id']} - {product['name']} ราคา: ฿{product['price']:.2f} จำนวน: {product['qty']}",use_container_width=True)
                # st.markdown('<h6 style="text-align: center;">' + f"{product['price']:.2f}" + '</h6>', unsafe_allow_html=True)
                quantity = st.number_input(
                    "สั่งซื้อ",
                    min_value=0,
                    value=0,
                    key=f"qty_{idx}"
                )
                if quantity > 0:
                    if 'order_items' not in st.session_state:
                        st.session_state.order_items = {}  # Initialize as a dictionary
                    # Update or add item to the dictionary
                    st.session_state.order_items[product['name']] = {
                        'name': product['name'],
                        'price': product['price'],
                        'quantity': quantity,
                        'subtotal': product['price'] * quantity,
                        'image_url': product['image_url']
                    }
                elif product['name'] in st.session_state.order_items and quantity == 0:
                    # Remove item if quantity is set to 0
                    del st.session_state.order_items[product['name']]
    with col2:
        # Order summary
        st.subheader("สรุปรายการสั่งซื้อ")
        if hasattr(st.session_state, 'order_items') and st.session_state.order_items:
            order_items_list = list(st.session_state.order_items.values())  # Convert to list
           
            order_items_list = list(st.session_state.order_items.values())
            for item in order_items_list:
                cols = st.columns([1.5, 1, 2])
                with cols[0]:
                    st.image(item['image_url'],caption=f"{item['name']}",use_container_width=True)
                with cols[1]:
                    st.write(f"{item['quantity']} ชิ้น")
                with cols[2]:
                    st.write(f"เป็นเงิน: ฿{item['subtotal']:.2f}")

            total = sum(item['subtotal'] for item in st.session_state.order_items.values())
            cols = st.columns(2)
           
            cols[0].markdown('<h5 style="text-align: right;">ยอดรวม</h5>', unsafe_allow_html=True)
            cols[1].markdown(f'<h5 style="text-align: right;">฿{total:.2f}</h5>', unsafe_allow_html=True)
           
            customer_name = st.text_input("ชื่อลูกค้า")
            special_instructions = st.text_area("บันทึกเพิ่มเติม")
           
           
            if st.button("ยืนยันการสั่งซื้อ"):
                if customer_name:
                    db.save_order(customer_name, order_items_list, total, special_instructions)  # Pass the list
                    st.session_state.order_items = {}  # Reset order items after order
                    st.rerun()
                else:
                    st.warning("กรุณากรอกชื่อลูกค้า")

def order_management_page():
    st.title("📊 จัดการออเดอร์")
   
    orders = db.load_orders()
    # st.write(orders)
    orders_df = pd.DataFrame(orders)
    # st.table(orders_df)
   
    # แปลงคอลัมน์ timestamp เป็น datetime
    orders_df['timestamp'] = pd.to_datetime(orders_df['timestamp'])
   
    # เลือกวันที่
    cols = st.columns(2)
    start_date = cols[0].date_input("เริ่มต้นวันที่", value=orders_df['timestamp'].min().date())
    end_date = cols[1].date_input("สิ้นสุดวันที่", value=orders_df['timestamp'].max().date())
   
    if start_date > end_date:
        st.error("วันที่เริ่มต้นต้องไม่มากกว่าวันที่สิ้นสุด")
        return
   
    # กรองข้อมูลตามวันที่
    filtered_orders_df = orders_df[
        (orders_df['timestamp'].dt.date >= start_date) &
        (orders_df['timestamp'].dt.date <= end_date)
    ]
   
    if filtered_orders_df.empty:
        st.info("ไม่มีออเดอร์ในช่วงวันที่ที่เลือก")
        return
   
    if orders:
        for idx, order in filtered_orders_df.iterrows():
            # แปลงวันที่เป็นรูปแบบ d/m/y
            order_date = order['timestamp'].strftime("%d/%m/%Y")
            with st.expander(f"ออเดอร์ {idx+1} - ลูกค้า:{order['customer_name']}:ยอดรวม: ฿{order['total']:.2f} ({order_date})"):
                items = json.loads(order['items'])
                # st.table(items)
                cols = st.columns([2,1],vertical_alignment="top",gap="medium")
                with cols[0]:
                    # แสดงรายการสินค้ารูปแบบตาราง
                    df_html = table_with_images(pd.DataFrame(items), url_columns=('image_url',))
                    st.markdown(df_html, unsafe_allow_html=True)
               
                # cols = st.columns(len(items))
                # for item_idx, item in enumerate(items):
                #     with cols[item_idx]:
                #         ut.display_image(item['image_url'])
                #         st.write(f"**{item['name']}**")
                #         st.write(f"จำนวน: {item['quantity']} ชิ้น")
                #         st.write(f"ราคา: ฿{item['subtotal']:.2f}")
                with cols[1]:
                    st.write(f"**ยอดรวม: ฿{order['total']:.2f}**")
                    st.write(f"หมายเหตุ: {order['special_instructions']}")
               
                    new_status = st.selectbox(
                        "สถานะ",
                        options=['pending', 'preparing', 'ready', 'completed', 'cancelled'],
                        key=f"status_{idx}",
                        index=['pending', 'preparing', 'ready', 'completed', 'cancelled'].index(order['status'])
                    )
                   
                    if new_status != order['status']:
                        st.write(new_status)
                        st.write(idx)
                        db.update_order(idx, new_status)
                        st.rerun()
    else:
        st.info("ยังไม่มีออเดอร์")

# Main App
def main():
    sidebar_menu()
    if not st.session_state.client:
        st.error("กรุณาตั้งค่า Google Sheets API ก่อนใช้งาน")
        return
   
    if st.session_state.current_page == 'products':
        product_management_page()
    elif st.session_state.current_page == 'orders':
        order_page()
    elif st.session_state.current_page == 'order_management':
        order_management_page()

# ========================================================================
if __name__ == "__main__":
    main()