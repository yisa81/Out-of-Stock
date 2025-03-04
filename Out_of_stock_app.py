
import streamlit as st
import pandas as pd
import datetime as dt
import io

# ====================== APP CONFIGURATION ======================
st.set_page_config(page_title="Out of Stock Calculations", page_icon="📉")

st.title("📉 Out of Stock Calculations Report")
st.write("Upload your **Sales Report** and enter the **Magento Stock Details** manually to generate the report.")

# ====================== SECURITY DISCLAIMER ======================
st.info(
    "🔒 **Security Disclaimer:**\n"
    "Your uploaded files are processed only in memory and are **NOT** stored on any server. "
    "Once you leave or refresh the page, your uploaded files are **immediately deleted**. "
    "No other users can view your uploaded files."
)

# ====================== FILE UPLOAD SECTION ======================
sales_file = st.file_uploader("Upload Sales Report File (Excel)", type=["xlsx"])
magento_screenshot = st.file_uploader("Upload Magento Stock Screenshot (Optional)", type=["png", "jpg", "jpeg"])

# ====================== MANUAL SKU INPUT SECTION ======================
st.write("### 📝 Enter Magento Stock Details")
sku_list = []
num_skus = st.number_input("How many SKUs do you want to enter?", min_value=1, max_value=20, value=3, step=1)

for i in range(num_skus):
    sku = st.text_input(f"SKU {i+1}", placeholder="e.g., parker_049")
    tot_salable = st.number_input(f"Tot Salable for SKU {i+1}", min_value=0, value=0, step=1)
    if sku:
        sku_list.append({"SKU": sku, "Tot Salable": tot_salable})

# ====================== REPORT GENERATION FUNCTION ======================
def generate_report(sales_file, sku_list):
    try:
        # Load Sales Report
        xls = pd.ExcelFile(sales_file)
        data_df = pd.read_excel(xls, sheet_name="Data")
        oos_df = pd.read_excel(xls, sheet_name="OOS")

        # Convert SKU list to DataFrame
        magento_df = pd.DataFrame(sku_list)

        # Extract Mthly Max Avg Sales
        data_df = data_df[['SKU', 'Mthly Max Avg Sales (A,B & C)', 'Conant SOH', 'Ocean SOH']]
        result_df = pd.merge(magento_df, data_df, on='SKU', how='left')

        # Calculate Estimated OOS Date: (Saleable Qty / Max Avg Sales) / 12 * 365 + Today()
        today = dt.datetime.now().date()
        result_df['Estimated OOS Date'] = result_df.apply(
            lambda row: today + pd.DateOffset(days=(row['Tot Salable'] / row['Mthly Max Avg Sales (A,B & C)']) / 12 * 365)
            if row['Mthly Max Avg Sales (A,B & C)'] > 0 else None, axis=1
        )

        # Keep All Orders Separately (Not Summed Up)
        oos_df = oos_df[['Simple SKU', 'Actual Outstanding Balance', 'Estimated Delivery Date']]
        oos_df = oos_df.rename(columns={'Simple SKU': 'SKU'})

        # Merge result_df with each row of OOS separately
        final_df = pd.merge(result_df, oos_df, on='SKU', how='left')

        # Select final columns
        final_df = final_df[['SKU', 'Tot Salable', 'Mthly Max Avg Sales (A,B & C)', 
                             'Estimated OOS Date', 'Actual Outstanding Balance', 'Estimated Delivery Date', 'Conant SOH', 'Ocean SOH']]

        # Save to Excel in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            final_df.to_excel(writer, index=False, sheet_name="Out of Stock Report")
        output.seek(0)

        return output, final_df
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None, None

# ====================== MAIN APP LOGIC ======================
if sales_file and sku_list:
    if st.button("📥 Generate Report"):
        with st.spinner("Processing... Please wait."):
            output, result_df = generate_report(sales_file, sku_list)
            if output:
                st.success("✅ Report generated successfully!")
                st.download_button(label="💾 Download Report", data=output, file_name="Out_of_Stock_Calculations_Report.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                st.dataframe(result_df)  # Display report preview

# ====================== SHOW UPLOADED SCREENSHOT ======================
if magento_screenshot:
    st.image(magento_screenshot, caption="Magento Stock Screenshot", use_column_width=True)
