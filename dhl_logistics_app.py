import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Set page configuration
st.set_page_config(
    page_title="DHL Logistics Dashboard",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

def update_shipment_status(shipment_id, status, location):
    """Update shipment status via API"""
    try:
        response = requests.put(
            f"{API_BASE_URL}/shipments/{shipment_id}",
            json={"Status": status, "CurrentLocation": location}
        )
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"Error updating shipment: {e}")
        return False

# Sidebar navigation
st.sidebar.markdown("<div class='main-header'>DHL Logistics</div>", unsafe_allow_html=True)
st.sidebar.image("https://logistics.dhl/content/dam/dhl/global/core/images/logos/dhl-logo.svg", width=100)

page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Shipments", "Customers", "Parcels", "Analytics", "Route Visualization"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Filters")

# Common filters in sidebar
status_filter = st.sidebar.selectbox(
    "Shipment Status",
    ["All", "In Transit", "Delivered", "Delayed", "Processing"]
)

# Dashboard Page
if page == "Dashboard":
    st.markdown("<div class='main-header'>DHL Logistics Dashboard</div>", unsafe_allow_html=True)
    
    # Fetch summary data
    summary = fetch_api_data("/dashboard/summary")
    
    if summary:
        # Create metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown(f"<div class='metric-value'>{summary['total_shipments']}</div>", unsafe_allow_html=True)
            st.markdown("<div class='metric-label'>Total Shipments</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
        with col2:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown(f"<div class='metric-value'>{summary['active_shipments']}</div>", unsafe_allow_html=True)
            st.markdown("<div class='metric-label'>Active Shipments</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
        with col3:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown(f"<div class='metric-value'>{summary['delayed_shipments']}</div>", unsafe_allow_html=True)
            st.markdown("<div class='metric-label'>Delayed Shipments</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
        with col4:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown(f"<div class='metric-value'>{summary['completed_shipments']}</div>", unsafe_allow_html=True)
            st.markdown("<div class='metric-label'>Completed Shipments</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Second row - charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("<div class='sub-header'>Shipment Status</div>", unsafe_allow_html=True)
            
            # Fetch status counts
            status_counts = fetch_api_data("/analytics/shipment-status-count")
            
            if status_counts:
                df_status = pd.DataFrame(status_counts)
                fig = px.pie(
                    df_status,
                    values='count',
                    names='status',
                    color_discrete_sequence=px.colors.sequential.RdBu,
                    hole=0.4
                )
                fig.update_layout(margin=dict(t=30, b=0, l=0, r=0))
                st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            st.markdown("<div class='sub-header'>Efficiency by Parcel Type</div>", unsafe_allow_html=True)
            
            # Fetch efficiency data
            efficiency_data = fetch_api_data("/analytics/efficiency-by-parcel-type")
            
            if efficiency_data:
                df_efficiency = pd.DataFrame(efficiency_data)
                fig = px.bar(
                    df_efficiency,
                    x='parcelType',
                    y=['averageEfficiency', 'averageRating'],
                    barmode='group',
                    color_discrete_sequence=['#D40511', '#FFCC00']
                )
                fig.update_layout(margin=dict(t=30, b=0, l=0, r=0))
                st.plotly_chart(fig, use_container_width=True)
        
        # Third row - Recent shipments
        st.markdown("<div class='sub-header'>Recent Shipments</div>", unsafe_allow_html=True)
        
        shipments = fetch_api_data("/shipments?limit=5")
        
        if shipments:
            df_shipments = pd.DataFrame(shipments)
            st.dataframe(
                df_shipments[['ShipmentID', 'ShipmentName', 'ParcelName', 'CustomerName', 'Status', 'CurrentLocation']],
                use_container_width=True
            )
    
# Shipments Page
elif page == "Shipments":
    st.markdown("<div class='main-header'>Shipment Management</div>", unsafe_allow_html=True)
    
    # Create tabs for viewing and updating shipments
    tab1, tab2 = st.tabs(["View Shipments", "Update Shipment"])
    
    with tab1:
        status_param = "" if status_filter == "All" else f"?status={status_filter}"
        shipments = fetch_api_data(f"/shipments{status_param}")
        
        if shipments:
            df_shipments = pd.DataFrame(shipments)
            
            # Advanced search
            search_col1, search_col2 = st.columns(2)
            with search_col1:
                search_term = st.text_input("Search by Shipment Name or Customer")
            
            if search_term:
                df_shipments = df_shipments[
                    df_shipments['ShipmentName'].str.contains(search_term, case=False) | 
                    df_shipments['CustomerName'].str.contains(search_term, case=False)
                ]
            
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
                    if update_shipment_status(shipment_id, new_status, new_location):
                        st.success("Shipment updated successfully!")
                        st.rerun()

# Customers Page
elif page == "Customers":
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
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.write(f"**Name:** {customer_detail['Name']}")
                st.write(f"**Email:** {customer_detail['Email']}")
                st.write(f"**Phone:** {customer_detail['Phone']}")
                st.write(f"**Address:** {customer_detail['Address']}")
                st.write(f"**Customer Type:** {customer_detail['Type']}")
                st.markdown("</div>", unsafe_allow_html=True)
            
            # In a real app, you might fetch associated shipments here
            with col2:
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.write("**Customer Activity**")
                
                # Placeholder for customer activity stats
                st.write("Active Shipments: 3")
                st.write("Completed Shipments: 12")
                st.write("Average Rating: 4.5/5")
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

# Analytics Page
elif page == "Analytics":
    st.markdown("<div class='main-header'>Logistics Analytics</div>", unsafe_allow_html=True)
    
    # Efficiency & customer ratings
    st.markdown("<div class='sub-header'>Shipment Performance Metrics</div>", unsafe_allow_html=True)
    
    analytics = fetch_api_data("/analytics/shipments")
    
    if analytics:
        df_analytics = pd.DataFrame(analytics)
        
        # Create metrics dashboard
        col1, col2, col3 = st.columns(3)
        
        with col1:
            avg_efficiency = df_analytics['Efficiency'].mean()
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown(f"<div class='metric-value'>{avg_efficiency:.1f}%</div>", unsafe_allow_html=True)
            st.markdown("<div class='metric-label'>Average Efficiency</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            avg_rating = df_analytics['CustomerRating'].mean()
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown(f"<div class='metric-value'>{avg_rating:.1f}/5</div>", unsafe_allow_html=True)
            st.markdown("<div class='metric-label'>Average Customer Rating</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col3:
            total_delays = df_analytics['Delays'].sum()
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown(f"<div class='metric-value'>{total_delays}</div>", unsafe_allow_html=True)
            st.markdown("<div class='metric-label'>Total Delays</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Scatter plot of efficiency vs customer rating
        fig = px.scatter(
            df_analytics,
            x="Efficiency",
            y="CustomerRating",
            size="Delays",
            hover_name="ShipmentID",
            color="Efficiency",
            color_continuous_scale="RdYlGn",
            title="Efficiency vs. Customer Rating"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Efficiency by parcel type
        efficiency_data = fetch_api_data("/analytics/efficiency-by-parcel-type")
        
        if efficiency_data:
            st.markdown("<div class='sub-header'>Performance by Parcel Type</div>", unsafe_allow_html=True)
            
            df_efficiency = pd.DataFrame(efficiency_data)
            
            # Create a radar chart
            fig = go.Figure()
            
            for i, row in df_efficiency.iterrows():
                fig.add_trace(go.Scatterpolar(
                    r=[row['averageEfficiency'], row['averageRating'] * 20, 100 - row['averageEfficiency']],
                    theta=['Efficiency', 'Customer Rating', 'Improvement Potential'],
                    fill='toself',
                    name=row['parcelType']
                ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100]
                    )),
                showlegend=True
            )
            
            st.plotly_chart(fig, use_container_width=True)

# Route Visualization Page
elif page == "Route Visualization":
    st.markdown("<div class='main-header'>Route Visualization</div>", unsafe_allow_html=True)
    
    active_routes = fetch_api_data("/route/active-shipments")
    locations = fetch_api_data("/route/locations")
    
    if active_routes and locations:
        # Create a map
        st.markdown("<div class='sub-header'>Active Shipment Routes</div>", unsafe_allow_html=True)
        
        # In a real app, you would use actual geocoded data
        # This is a placeholder visualization
        
        # Create a simple network diagram
        nodes = pd.DataFrame(
            {"name": locations}
        )
        
        # Create edges from route data
        edges = []
        for route in active_routes:
            for i in range(len(route['routePoints']) - 1):
                edges.append({
                    "source": i,
                    "target": i + 1, 
                    "weight": route['weight'],
                    "shipment": route['shipmentName']
                })
        
        edges_df = pd.DataFrame(edges)
        
        # Create a simple network diagram
        fig = go.Figure()
        
        # Add nodes
        for i, location in enumerate(locations):
            fig.add_trace(go.Scatter(
                x=[i * 100],
                y=[i % 3 * 100],
                mode='markers+text',
                marker=dict(size=20, color='#D40511'),
                text=[location],
                textposition="bottom center",
                name=location
            ))
        
        # Add routes
        for route in active_routes:
            x_values = [point['x'] for point in route['routePoints']]
            y_values = [point['y'] for point in route['routePoints']]
            
            fig.add_trace(go.Scatter(
                x=x_values,
                y=y_values,
                mode='lines',
                line=dict(width=2, color='#FFCC00'),
                name=f"Route {route['shipmentId']} - {route['shipmentName']}"
            ))
        
        fig.update_layout(
            title="Active Shipment Routes",
            showlegend=True,
            height=600
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Show active shipments table
        st.markdown("<div class='sub-header'>Active Shipments</div>", unsafe_allow_html=True)
        
        active_df = pd.DataFrame([
            {
                "Shipment ID": route['shipmentId'],
                "Name": route['shipmentName'],
                "Location": route['currentLocation'],
                "Type": route['parcelType'],
                "Weight (kg)": route['weight']
            }
            for route in active_routes
        ])
        
        st.dataframe(active_df, use_container_width=True)

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