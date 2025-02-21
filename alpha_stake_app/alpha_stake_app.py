import streamlit as st
import bittensor as bt
import pandas as pd
import time
import altair as alt
import logging
import websockets

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

st.set_page_config(layout="wide", page_title="Macrocosmos dTao App", page_icon="logo_files/logo.png", initial_sidebar_state="collapsed")

#Logos and title
col1, col2, col3 = st.columns([1, 3, 1])  # Adjust width proportions

with col1:
    st.markdown(
        """
        <div style="display: flex; justify-content: center; align-items: center; height: 100%;">
            <iframe src="https://lunar.macrocosmos.ai/iframe.html?globals=backgrounds.value%3A!hex(333)%3Bbackgrounds.grid%3A!false%3Btheme%3Adark&args=&id=logospinner--dark-large&viewMode=story"
                    width="300" height="150" style="border: none;"></iframe>
        </div>
        """,
        unsafe_allow_html=True
    )

with col2:
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
            Subnet Alpha Stake App
        </h1>
    </div>
    """,
    unsafe_allow_html=True
)

with col3:
    st.markdown(
        """
        <div style="display: flex; justify-content: center; align-items: center; height: 100%;">
            <iframe src="https://lunar.macrocosmos.ai/iframe.html?globals=backgrounds.value%3A!hex(333)%3Bbackgrounds.grid%3A!false%3Btheme%3Adark&args=&id=logospinner--dark-large&viewMode=story"
                    width="300" height="150" style="border: none;"></iframe>
        </div>
        """,
        unsafe_allow_html=True
    )


# Choose number of blocks and feature to display (e.g., emission, alpha_out, etc.). Must be from DynamicInfo and Balance object
REFRESH_PARAM = 30
NETWORK = "finney"

subnets_of_interest = [9]

# Initialize the subtensor connection
subtensor = bt.Subtensor(network=NETWORK)
# logging.info(sub.determine_chain_endpoint_and_network(network=NETWORK))  # May indicate delays per query
current_block = subtensor.get_current_block()

metagraph_instance = subtensor.metagraph(netuid=subnets_of_interest[0], block = current_block)


def get_active_uids(metagraph_instance):
    if metagraph_instance is None:
        print("Subnet does not exist")
        return None

    active_uids = [i for i in range(len(metagraph_instance.active)) if metagraph_instance.active[i]]
    active_coldkeys = {metagraph_instance.coldkeys[i] for i in active_uids}  # Use set for fast lookup

    return active_uids, active_coldkeys

def get_total_alpha_by_uid(metagraph_instance, uid):
    # Get metagraph info synchronously
    if metagraph_instance is None:
        print("Subnet does not exist")
        return None

    # Validate UID
    if uid >= len(metagraph_instance.hotkeys):
        print(f"UID {uid} is out of range for subnet {metagraph_instance.netuid}")
        return None

    # Get staked alpha from metagraph
    staked_alpha = metagraph_instance.alpha_stake[uid]

    print(f"Staked Alpha for UID {uid}: {staked_alpha}")
    
    return uid, staked_alpha

uid_stake_dict = {}
for i in get_active_uids(metagraph_instance)[0]:
    uid_stake_dict[i] = get_total_alpha_by_uid(metagraph_instance, i)[1]
    # list_of_uids_stake.append(get_total_alpha_by_uid(metagraph_instance, i))

st.write(f"### Stake app for subnet(s) {subnets_of_interest} values at block `{current_block}`")

# Convert to DataFrame
df = pd.DataFrame(list(uid_stake_dict.items()), columns=["UID", "Stake"])

color_scheme = alt.Scale(scheme="dark2")  # Alternatives: "category10", "set1", "tableau10"

# Create pie chart
chart = alt.Chart(df).mark_arc().encode(
    theta="Stake",
    color=alt.Color("UID:N", scale=color_scheme),
    tooltip=["UID", "Stake"]
).properties(title="UID Staked Alphas Distribution",
            width=700,   # Adjust width
            height=700   # Adjust height
)



# Part of page
col1, col2 = st.columns([1, 1])  # Adjust width proportions
with col1:
    st.dataframe(df)
with col2:
    # Display in Streamlit
    st.altair_chart(chart, use_container_width=True)    
# Sleep and rerun settings
wait_message = st.empty()

for i in range(REFRESH_PARAM):  
    wait_message.write(f"Refreshing in {REFRESH_PARAM - i} seconds")  
    time.sleep(1)  # Wait for 1 second

st.experimental_rerun()  # Forces Streamlit to update

