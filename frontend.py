import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# API Base URL
API_BASE_URL = "http://127.0.0.1:8000"

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #D40511;
        font-weight: bold;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #333333;
        font-weight: bold;
    }
    .card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        background-color: #f8f9fa;
        box-shadow: 0 0.25rem 0.75rem rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #D40511;
    }
    .metric-label {
        font-size: 1rem;
        color: #6c757d;
    }
    .dhl-red {
        color: #D40511;
    }
    .dhl-yellow {
        color: #FFCC00;
    }
</style>
""", unsafe_allow_html=True)

# Helper functions
def fetch_api_data(endpoint):
    """Fetch data from the API"""
    try:
        response = requests.get(f"{API_BASE_URL}{endpoint}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data from API: {e}")
        return None

# Sidebar navigation
st.sidebar.markdown("<div class='main-header'>DHL Logistics</div>", unsafe_allow_html=True)
st.sidebar.image("https://logistics.dhl/content/dam/dhl/global/core/images/logos/dhl-logo.svg", width=100)

page = st.sidebar.radio(
    "Navigation",
    ["Customers", "Parcels", "Shipments"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Filters")

# Customers Page
if page == "Customers":
    st.markdown("<div class='main-header'>Customer Management</div>", unsafe_allow_html=True)
    
    customers = fetch_api_data("/customers")
    
    if customers:
        df_customers = pd.DataFrame(customers)
        
        search_term = st.text_input("Search by Customer Name or Email")
        
        if search_term:
            df_customers = df_customers[
                df_customers['Name'].str.contains(search_term, case=False) | 
                df_customers['Email'].str.contains(search_term, case=False)
            ]
        
        st.dataframe(df_customers, use_container_width=True)
        
        # Customer details section
        st.markdown("<div class='sub-header'>Customer Details</div>", unsafe_allow_html=True)
        
        selected_customer_id = st.selectbox(
            "Select Customer to View Details",
            options=df_customers['CustomerID'].tolist(),
            format_func=lambda x: df_customers.loc[df_customers['CustomerID'] == x, 'Name'].iloc[0]
        )
        
        customer_detail = fetch_api_data(f"/customers/{selected_customer_id}")
        
        if customer_detail:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.write(f"**Name:** {customer_detail['Name']}")
            st.write(f"**Email:** {customer_detail['Email']}")
            st.write(f"**Phone:** {customer_detail['Phone']}")
            st.write(f"**Address:** {customer_detail['Address']}")
            st.write(f"**Customer Type:** {customer_detail['Type']}")
            st.markdown("</div>", unsafe_allow_html=True)

# Parcels Page
elif page == "Parcels":
    st.markdown("<div class='main-header'>Parcel Management</div>", unsafe_allow_html=True)
    
    parcels = fetch_api_data("/parcels")
    
    if parcels:
        df_parcels = pd.DataFrame(parcels)
        
        col1, col2 = st.columns(2)
        
        with col1:
            search_term = st.text_input("Search by Parcel Name")
        
        with col2:
            type_filter = st.selectbox(
                "Filter by Type",
                ["All"] + list(df_parcels['Type'].unique())
            )
        
        # Apply filters
        filtered_df = df_parcels
        
        if search_term:
            filtered_df = filtered_df[filtered_df['ParcelName'].str.contains(search_term, case=False)]
        
        if type_filter != "All":
            filtered_df = filtered_df[filtered_df['Type'] == type_filter]
        
        st.dataframe(filtered_df, use_container_width=True)
        
        # Weight distribution chart
        st.markdown("<div class='sub-header'>Parcel Weight Distribution</div>", unsafe_allow_html=True)
        
        fig = px.histogram(
            df_parcels,
            x="Weight",
            color="Type",
            marginal="box",
            opacity=0.7
        )
        
        st.plotly_chart(fig, use_container_width=True)

# Shipments Page
elif page == "Shipments":
    st.markdown("<div class='main-header'>Shipment Management</div>", unsafe_allow_html=True)
    
    # Create tabs for viewing and updating shipments
    tab1, tab2 = st.tabs(["View Shipments", "Update Shipment"])
    
    with tab1:
        shipments = fetch_api_data("/shipments")
        
        if shipments:
            df_shipments = pd.DataFrame(shipments)
            
            st.dataframe(df_shipments, use_container_width=True)
    
    with tab2:
        shipments = fetch_api_data("/shipments")
        
        if shipments:
            shipment_options = {f"{s['ShipmentID']} - {s['ShipmentName']}": s['ShipmentID'] for s in shipments}
            
            selected_shipment = st.selectbox(
                "Select Shipment to Update",
                options=list(shipment_options.keys())
            )
            
            shipment_id = shipment_options[selected_shipment]
            
            # Find the selected shipment
            current_shipment = next((s for s in shipments if s['ShipmentID'] == shipment_id), None)
            
            if current_shipment:
                st.write(f"Current Status: **{current_shipment['Status']}**")
                st.write(f"Current Location: **{current_shipment['CurrentLocation']}**")
                
                new_status = st.selectbox(
                    "New Status",
                    ["In Transit", "Delivered", "Delayed", "Processing"]
                )
                
                new_location = st.text_input(
                    "New Location",
                    value=current_shipment['CurrentLocation']
                )
                
                if st.button("Update Shipment"):
                    try:
                        response = requests.put(
                            f"{API_BASE_URL}/shipments/{shipment_id}/status",
                            json={"status": new_status}
                        )
                        response.raise_for_status()
                        st.success("Shipment updated successfully!")
                    except requests.exceptions.RequestException as e:
                        st.error(f"Error updating shipment: {e}")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #6c757d; font-size: 0.8rem;">
        © 2025 DHL Logistics Dashboard | Created with Streamlit
    </div>
    """, 
    unsafe_allow_html=True
)

# command to run the app: streamlit run frontend.py