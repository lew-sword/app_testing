from typing import List
import streamlit as st
import bittensor as bt
import pandas as pd
import time
import altair as alt
import logging
import websockets

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

st.set_page_config(layout="wide", page_title="Macrocosmos dTao App", page_icon="logo_files/logo.png", initial_sidebar_state="collapsed")


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
        Macrocosmos Subnet Alpha Stake App
    </h1>
</div>
""",
unsafe_allow_html=True
)


class SubnetAnalyzer:
    def __init__(self, subnet: int, subtensor: bt.Subtensor, block: int = None):
        """
        Initialize the analyzer for a specific subnet.

        Args:
            subnet: The subnet ID to analyze.
            subtensor: The bittensor subtensor connection.
            block: The block at which to analyze the subnet (default: latest).
        """
        self.subnet = subnet
        self.subtensor = subtensor
        self.current_block = block if block else subtensor.get_current_block()

        # Fetch the metagraph for the given subnet and block
        self.metagraph = self.subtensor.metagraph(netuid=self.subnet, block=self.current_block)
        if self.metagraph is None:
            raise ValueError(f"Subnet {self.subnet} does not exist.")
    

    def get_macro_owner_key(self)->List[str]:
        if self.subnet == 1:
            return ["5HCFWvRqzSHWRPecN7q8J6c7aKQnrCZTMHstPv39xL1wgDHh"]
        elif self.subnet == 9:
            return ["5FsbubeciqtB5Nik3umL2iD4fG8FcC9GbT9nHJfXMj4mJJZ9"]
        elif self.subnet == 13:
            return ["5HBswBt1A9Ahx6U76abXXGd7VmabmCNBGhSK2vrP71GSxtgZ"]
        elif self.subnet == 25:
            return ["5F6aRdsBHajN2NhZHBTB6ibBFu7YuZZEWruWzB8x6B6GiZ4D"]
        elif self.subnet == 37:
            return ["5DXqqdrvu5FK3dASRVTCdGPZKx4Q9nkAZZSmibKG6PEEeW4j"]
        else:
            return ["non_macrocosmos_key"]


    def get_macro_vali_key(self)->List[str]:
        if self.subnet == 1:
            return ["5FRXwb2qsEhqDQQKcm5m2MF26xTWwW65MHTEtKFFydypuqjG"]
        elif self.subnet == 9:
            return ["5FRXwb2qsEhqDQQKcm5m2MF26xTWwW65MHTEtKFFydypuqjG", "5HBtpwxuGNL1gwzwomwR7sjwUt8WXYSuWcLYN6f9KpTZkP4k"]
        elif self.subnet == 13:
            return ["5FRXwb2qsEhqDQQKcm5m2MF26xTWwW65MHTEtKFFydypuqjG"]
        elif self.subnet == 25:
            return ["5FRXwb2qsEhqDQQKcm5m2MF26xTWwW65MHTEtKFFydypuqjG"]
        elif self.subnet == 37:
            return ["5HQWSRrS4sjxwgf9EQKG7arRHE2WqMTcMap2QZJWsvQFXfQK"]
        else:
            return ["non_macrocosmos_key"]

    def get_owner_uids(self):
        """Return active UIDs and their corresponding coldkeys."""
        active_uids = [i for i in range(len(self.metagraph.active)) if self.metagraph.coldkeys[i]== self.get_macro_owner_key()[0]]
        logging.info(f"Owner UIDs for subnet {self.subnet}: {active_uids}")
        return active_uids

    def get_active_uids(self):
        """Return active UIDs and their corresponding coldkeys."""
        active_uids = [i for i in range(len(self.metagraph.active)) if self.metagraph.active[i]]
        logging.info(f"Active UIDs for subnet {self.subnet}: {active_uids}")
        return active_uids

    def get_alpha_data_by_uid(self, uid: int):
        """Get the total staked alpha for a given active UID."""
        if uid >= len(self.metagraph.hotkeys):
            print(f"UID {uid} is out of range for subnet {self.metagraph.netuid}")
            return None

        staked_alpha = self.metagraph.alpha_stake[uid]
        stake = self.metagraph.stake[uid]
        return uid, staked_alpha, stake

    def get_stake_data(self):
        """Fetch stake data for all active UIDs in the subnet."""
        uid_stake_dict = {}
        macro_vali_keys = self.get_macro_vali_key()
        for uid in self.get_active_uids() + self.get_owner_uids():
            stake_data_for_uid = self.get_alpha_data_by_uid(uid)
            uid_stake_dict[uid] = {"alpha_stake": stake_data_for_uid[1], #gets staked alpha
                                   "stake": stake_data_for_uid[2], #gets total stake
                                   "coldkey": self.metagraph.coldkeys[uid],
                                   "v_permit": self.metagraph.validator_permit[uid], 
                                   "macro_vali": 1 if self.metagraph.coldkeys[uid] in macro_vali_keys else 0,
                                   "macro_owner": 1 if self.metagraph.coldkeys[uid] in self.get_macro_owner_key() else 0}
            
        return uid_stake_dict

    def to_dataframe(self):
        """Convert stake data to a Pandas DataFrame."""
        stake_data = self.get_stake_data()

        # Convert dictionary to DataFrame
        df = pd.DataFrame.from_dict(stake_data, orient="index")
        # Reset index to make UID a column
        df.reset_index(inplace=True)
        # Rename index column to 'UID'
        df.rename(columns={"index": "UID", "alpha_stake": "Alpha_Stake", "stake": "Stake" , "coldkey": "Coldkey", "v_permit": "V_Permit", "macro_vali": "Macro_Vali", "macro_owner": "Macro_Owner" }, inplace=True)
        # Create a new categorical column for coloring
        df["Macro_Group"] = df.apply(lambda row: 1 if row["Macro_Vali"] == 1 or row["Macro_Owner"] == 1 else 0, axis=1)
        # Sort by 'Stake' in descending order
        df = df.sort_values(by="Alpha_Stake", ascending=False)
        return df
    

    def display_stake_data(self):
        """Display stake data in Streamlit."""
        df = self.to_dataframe()
        st.write(f"### Alpha stake data for subnet `{self.subnet}` at block `{self.current_block}`")
        st.dataframe(df.set_index("UID"), use_container_width=True)


# Initialize subtensor connection\
REFRESH_PARAM = 30
NETWORK = "finney"
MAX_RETRIES = 5
INITIAL_WAIT = 2

def connect_to_subtensor(network, max_retries=MAX_RETRIES, initial_wait=INITIAL_WAIT):
    attempt = 0
    while attempt < max_retries:
        try:
            subtensor = bt.Subtensor(network=network)  # Attempt connection
            st.success(f"Connected successfully to {network} in attempt {attempt+1}/{max_retries} ✅")
            return subtensor
        except Exception as e:
            st.warning(f"Connection failed: {str(e)}. Retrying in {initial_wait} seconds...")
            time.sleep(initial_wait)
            initial_wait *= 2  # Exponential backoff
            attempt += 1

    return None  # Return None if all attempts fail

# Try connecting to Subtensor
subtensor = connect_to_subtensor(NETWORK)

if subtensor is None:
    st.error("Failed to connect to Subtensor.")
    if st.button("Retry Connection 🔄"):
        st.experimental_rerun()  # Restart the app when clicked

current_block = subtensor.get_current_block()

inst_sn1 = SubnetAnalyzer(subnet=1, subtensor=subtensor, block=current_block)
inst_sn9 = SubnetAnalyzer(subnet=9, subtensor=subtensor, block=current_block)
inst_sn13 = SubnetAnalyzer(subnet=13, subtensor=subtensor, block=current_block)
inst_sn25 = SubnetAnalyzer(subnet=25, subtensor=subtensor, block=current_block)
inst_sn37 = SubnetAnalyzer(subnet=37, subtensor=subtensor, block=current_block)

# Define a function to create the pie chart
def make_chart(df, color_mode):
    """Create a pie chart with colors based on selected mode."""
    theta_param = "Alpha_Stake"
    
    if color_mode == "Validator Permit":
        color_scheme = alt.Scale(domain=[True, False], range=["#4CAF50", "#FF5733"])
        color_encoding = alt.Color("V_Permit:N", scale=color_scheme, title="Validator Permit")

    elif color_mode == "Macro Validator (Alpha Stake)":
        color_scheme = alt.Scale(domain=[1, 0], range=["#FFD700", "#4682B4"])
        color_encoding = alt.Color("Macro_Vali:O", scale=color_scheme, title="Macro Validator")

    elif color_mode == "Macro Validator (Stake)":
        theta_param = "Stake"
        color_scheme = alt.Scale(domain=[1, 0], range=["#FFD700", "#4682B4"])
        color_encoding = alt.Color("Macro_Vali:O", scale=color_scheme, title="Macro Validator")

    elif color_mode == "Macro Group (Alpha Stake)":
        color_scheme = alt.Scale(domain=[1,0], range=["#FFD700", "#4682B4"])
        color_encoding = alt.Color("Macro_Group:O", scale=color_scheme, title="Macro Group")

    elif color_mode == "Macro Group (Stake)":
        theta_param = "Stake"
        color_scheme = alt.Scale(domain=[1,0], range=["#FFD700", "#4682B4"])
        color_encoding = alt.Color("Macro_Group:O", scale=color_scheme, title="Macro Group")

    else:  # Default color scheme (UID)
        color_scheme = alt.Scale(scheme="dark2")
        color_encoding = alt.Color("UID:N", scale=color_scheme, title="UID")

    # Create pie chart
    return alt.Chart(df).mark_arc().encode(
        theta=f"{theta_param}:Q",
        color=color_encoding,
        tooltip=["UID", "Stake", "Alpha_Stake", "V_Permit", "Coldkey", "Macro_Group"]
    ).properties(
        title="UID Staked Alphas Distribution",
        width=500,
        height=500
    )

color_mode = st.radio(
    "Select display mode:",
    ["UID", "Validator Permit", "Macro Validator (Alpha Stake)", "Macro Validator (Stake)", "Macro Group (Alpha Stake)", "Macro Group (Stake)"],
    index=0  # Default to UID
)

# Create separate rows for each subnet
for inst in [inst_sn1, inst_sn9, inst_sn13, inst_sn25, inst_sn37]:
    col1, col2 = st.columns([1, 1])  # Equal width columns

    with col1:
        inst.display_stake_data()  # Show the dataframe

    with col2:
        st.altair_chart(make_chart(inst.to_dataframe(), color_mode), use_container_width=True)  # Show the chart


# Sleep and rerun settings
wait_message = st.empty()

for i in range(REFRESH_PARAM):  
    wait_message.write(f"Refreshing in {REFRESH_PARAM - i} seconds")  
    time.sleep(1)  # Wait for 1 second

st.experimental_rerun()  # Forces Streamlit to update

