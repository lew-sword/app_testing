import streamlit as st
import bittensor as bt
import pandas as pd
import time
import altair as alt
import logging
import websockets

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

st.set_page_config(layout="wide", page_title="Macrocosmos dTao App", page_icon="logo_files/logo.png", initial_sidebar_state="collapsed")


# Centered title with flexbox for vertical alignment
st.markdown(
"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap');

    .orbitron-title {
        font-family: "Orbitron", sans-serif !important;
        font-weight: 700;
        text-transform: uppercase;
        text-align: center;
        margin: 0;
        letter-spacing: 2px;
        color: #4CAF50;
    }
</style>

<div style="display: flex; justify-content: center; align-items: center; height: 100%;">
    <h1 class="orbitron-title">
        Macrocosmos dTao App
    </h1>
</div>
""",
unsafe_allow_html=True
)


# Choose number of blocks and feature to display (e.g., emission, alpha_out, etc.). Must be from DynamicInfo and Balance object
NUM_OF_BLOCKS = 6   
FEATURE_NAME = "price"
REFRESH_PARAM = 12
NETWORK = "finney"
# Define subnets of interest for data 
subnets_of_interest = [1, 9, 13, 25, 37]

# Initialize the subtensor connection
sub = bt.Subtensor(network=NETWORK)
# logging.info(sub.determine_chain_endpoint_and_network(network=NETWORK))  # May indicate delays per query
current_block = sub.get_current_block()

def all_subnet_data_func(block):
    data_list = []
    all_subnet_data = sub.all_subnets(block=block)
    for i in all_subnet_data:
        if i.netuid in {0,1,9,13,25,37}:
            data_list.append(i)
    return data_list

data_list = all_subnet_data_func(current_block)
# Create a list of dictionaries for structured data
data = [{"Netuid": i.netuid, "Subnet Alpha Name": i.subnet_name, "Symbol": i.symbol, f"{FEATURE_NAME}": getattr(i, FEATURE_NAME).tao} for i in data_list]
print(data)
# Convert to a DataFrame
df = pd.DataFrame(data)
st.write(f"### Subnets, symbols, current `{FEATURE_NAME}` values at block `{current_block}`")
st.dataframe(df.set_index("Netuid").sort_values(by="Netuid").transpose())

# Initialize session state for storing block data
if "block_data" not in st.session_state:
    st.session_state.block_data = {netuid: [] for netuid in subnets_of_interest}


MAX_RETRIES = 8  # Maximum number of retry attempts
INITIAL_DELAY = 1  # Initial delay in seconds

def fetch_block_data(current_block=current_block):
    """Fetch latest block data and update session state with a rolling window using batch fetching."""
    
    retries = 0
    delay = INITIAL_DELAY
    logging.info(f"Fetching block data at {current_block}...")
    while retries < MAX_RETRIES:
        try:
            # Ensure session state is initialized for all subnets
            for netuid in subnets_of_interest:
                st.session_state.block_data.setdefault(netuid, [])

            # Get the last recorded block for any subnet
            stored_blocks = {
                netuid: {entry["BLOCK"] for entry in st.session_state.block_data[netuid]}
                for netuid in subnets_of_interest
            }

            # Find the earliest block that needs fetching
            last_recorded_blocks = {
                netuid: max(stored_blocks[netuid]) if stored_blocks[netuid] else (current_block - NUM_OF_BLOCKS)
                for netuid in subnets_of_interest
            }

            # Define the block range to fetch
            block_range = list(range(min(last_recorded_blocks.values()) + 1, current_block + 1))

            if not block_range:
                return  # No new blocks to fetch

            # Fetch all subnet data in a single batch call per block
            all_data_per_block = {block: all_subnet_data_func(block) for block in block_range}

            # Create a lookup dict for fast access
            block_netuid_map = {
                (block, subnet.netuid): subnet
                for block, subnet_list in all_data_per_block.items()
                for subnet in subnet_list if subnet.netuid in subnets_of_interest
            }

            # Process data per subnet
            for netuid in subnets_of_interest:
                new_entries = [
                    {
                        "SYMBOL": block_netuid_map[(block, netuid)].symbol,
                        "BLOCK": block,
                        "VALUE": getattr(block_netuid_map[(block, netuid)], FEATURE_NAME).tao
                    }
                    for block in block_range
                    if (block, netuid) in block_netuid_map and block not in stored_blocks[netuid]
                ]

                if new_entries:
                    st.session_state.block_data[netuid].extend(new_entries)

                    # Keep only the last NUM_OF_BLOCKS entries (rolling window)
                    st.session_state.block_data[netuid] = st.session_state.block_data[netuid][-NUM_OF_BLOCKS:]

                    logging.info(f"✅ Added {len(new_entries)} new blocks for subnet {netuid}")

            return  # Success, exit loop

        except websockets.exceptions.WebSocketException as e:
            retries += 1
            logging.error(f"WebSocket error: {e} - Retrying in {delay}s ({retries}/{MAX_RETRIES})")
            time.sleep(delay)
            delay *= 2  # Exponential backoff

        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            st.error(f"⚠️ Unexpected error: {e}")
            return  # Exit immediately for non-WebSocket errors

    st.error("🚨 Failed to fetch block data after multiple attempts.")
    logging.error("Maximum retries reached. Aborting fetch_block_data.")


# Fetch latest data
fetch_block_data()

# Convert stored data to DataFrame
df_list = []
for netuid, records in st.session_state.block_data.items():
    temp_df = pd.DataFrame(records)
    temp_df["SUBNET"] = netuid
    temp_df["CHANGE"] = temp_df["VALUE"].pct_change().fillna(0) * 100  # Convert to %
    temp_df = temp_df.iloc[1:]
    df_list.append(temp_df)

df = pd.concat(df_list) if df_list else pd.DataFrame(columns=["SYMBOL","SUBNET", "BLOCK", "VALUE", "CHANGE"])

# Display the data in expander objects
st.write(f"### Previous `{FEATURE_NAME}` values for selected subnets")

for netuid in df["SUBNET"].unique():
    with st.expander(f"Subnet {netuid} Data"):
        subnet_df = df[df["SUBNET"] == netuid].sort_values("BLOCK", ascending=False)
        st.dataframe(subnet_df.drop(columns="SUBNET"), use_container_width=True)

# Plotting dataframe results as line charts
if not df.empty:
    # Enable zooming & panning
    zoom = alt.selection_interval(bind="scales")  

    # Enable hover interaction
    hover = alt.selection_single(
        nearest=True, on="mouseover", fields=["BLOCK"], empty="none"
    )

    # Dynamically compute Y-axis range for autozoom
    y_min, y_max = df["CHANGE"].min(), df["CHANGE"].max()
    y_margin = (y_max - y_min) * 0.1  # Add 10% margin
    y_scale = alt.Scale(domain=[y_min - y_margin, y_max + y_margin])  

    # Line chart explicitly encoding `SUBNET` for multiple lines
    line = alt.Chart(df).mark_line().encode(
        x=alt.X("BLOCK:O", title="Block", sort="descending"),
        y=alt.Y("CHANGE:Q", title="Percentage Change (%)", scale=y_scale),
        color=alt.Color("SUBNET:N", title="Subnet", scale=alt.Scale(scheme="category10")),
        tooltip=["BLOCK", "CHANGE", "SUBNET","VALUE"]
    ).properties(
        width=900, height=500
    ).add_selection(zoom) 

    # Add hover effect - Circles on hovered points
    points = alt.Chart(df).mark_circle(size=80).encode(
        x="BLOCK:O",
        y="CHANGE:Q",
        color="SUBNET:N",
        tooltip=["BLOCK", "CHANGE", "SUBNET", "SYMBOL"]
    ).transform_filter(hover)

    # Transparent selectors to improve interaction
    selectors = alt.Chart(df).mark_rule().encode(
        x="BLOCK:O",
        opacity=alt.condition(hover, alt.value(0.3), alt.value(0))
    ).add_selection(hover)

    # Combine all elements 
    chart = alt.layer(line, selectors, points).add_selection(zoom)

    st.altair_chart(chart, use_container_width=True)

# Sleep and rerun settings
wait_message = st.empty()

for i in range(REFRESH_PARAM):  
    wait_message.write(f"Refreshing in {REFRESH_PARAM - i} seconds")  
    time.sleep(1)  # Wait for 1 second

st.experimental_rerun()  # Forces Streamlit to update

