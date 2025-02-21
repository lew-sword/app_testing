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
        
    def get_macro_vali_key(self):
        if self.subnet == 1:
            return "5FRXwb2qsEhqDQQKcm5m2MF26xTWwW65MHTEtKFFydypuqjG"
        elif self.subnet == 9:
            return "5FRXwb2qsEhqDQQKcm5m2MF26xTWwW65MHTEtKFFydypuqjG" #"5HBtpwxuGNL1gwzwomwR7sjwUt8WXYSuWcLYN6f9KpTZkP4k"
        elif self.subnet == 13:
            return "5FRXwb2qsEhqDQQKcm5m2MF26xTWwW65MHTEtKFFydypuqjG"
        elif self.subnet == 25:
            return "5FRXwb2qsEhqDQQKcm5m2MF26xTWwW65MHTEtKFFydypuqjG"
        elif self.subnet == 37:
            return "5HQWSRrS4sjxwgf9EQKG7arRHE2WqMTcMap2QZJWsvQFXfQK"
        else:
            return"non_macrocosmos_key"

    def get_active_uids(self):
        """Return active UIDs and their corresponding coldkeys."""
        active_uids = [i for i in range(len(self.metagraph.active)) if self.metagraph.active[i]]
        return active_uids

    def get_total_alpha_by_uid(self, uid: int):
        """Get the total staked alpha for a given active UID."""
        if uid >= len(self.metagraph.hotkeys):
            print(f"UID {uid} is out of range for subnet {self.metagraph.netuid}")
            return None

        staked_alpha = self.metagraph.alpha_stake[uid]
        return uid, staked_alpha

    def get_stake_data(self):
        """Fetch stake data for all active UIDs in the subnet."""
        uid_stake_dict = {}
        for uid in self.get_active_uids():
            uid_stake_dict[uid] = {"stake": self.get_total_alpha_by_uid(uid)[1], "coldkey": self.metagraph.coldkeys[uid], "v_permit": self.metagraph.validator_permit[uid], "macro_vali": 1 if self.metagraph.coldkeys[uid]==self.get_macro_vali_key() else 0}
        return uid_stake_dict

    def to_dataframe(self):
        """Convert stake data to a Pandas DataFrame."""
        stake_data = self.get_stake_data()

        # Convert dictionary to DataFrame
        df = pd.DataFrame.from_dict(stake_data, orient="index")
        # Reset index to make UID a column
        df.reset_index(inplace=True)
        # Rename index column to 'UID'
        df.rename(columns={"index": "UID", "stake": "Stake", "coldkey": "Coldkey", "v_permit": "V_Permit", "macro_vali": "Macro Vali" }, inplace=True)
        
        # Sort by 'Stake' in descending order
        df = df.sort_values(by="Stake", ascending=False)
        return df
    

    def display_stake_data(self):
        """Display stake data in Streamlit."""
        df = self.to_dataframe()
        st.write(f"### Stake data for subnet {self.subnet} at block `{self.current_block}`")
        st.dataframe(df.set_index("UID"), use_container_width=True)


# Initialize subtensor connection\
REFRESH_PARAM = 30
NETWORK = "finney"
subtensor = bt.Subtensor(network=NETWORK)
current_block = subtensor.get_current_block()     
inst_sn1 = SubnetAnalyzer(subnet=1, subtensor=subtensor, block=current_block)
inst_sn9 = SubnetAnalyzer(subnet=9, subtensor=subtensor, block=current_block)
inst_sn13 = SubnetAnalyzer(subnet=13, subtensor=subtensor, block=current_block)
inst_sn25 = SubnetAnalyzer(subnet=25, subtensor=subtensor, block=current_block)
inst_sn37 = SubnetAnalyzer(subnet=37, subtensor=subtensor, block=current_block)


def make_chart(df, color_by_v_permit=False, color_by_macro_vali=False):
    """Create a pie chart with colors based on either UID or V_Permit."""
    
    if color_by_v_permit:
        color_scheme = alt.Scale(domain=[True, False], range=["#4CAF50", "#FF5733"])
        color_encoding = alt.Color("V_Permit:N", scale=color_scheme, title="Validator Permit")
    elif color_by_macro_vali:
        # Gold for Macro Validator, Blue for Others
        color_scheme = alt.Scale(domain=[1, 0], range=["#FFD700", "#4682B4"])
        color_encoding = alt.Color("Macro Vali:O", scale=color_scheme, title="Macro Validator")
        
    else:
        color_scheme = alt.Scale(scheme="dark2")  # Alternative color scheme for UID
        color_encoding = alt.Color("UID:N", scale=color_scheme, title="UID")
    
    # Create pie chart
    return alt.Chart(df).mark_arc().encode(
        theta="Stake",
        color=color_encoding,
        tooltip=["UID", "Stake", "V_Permit", "Coldkey"]
    ).properties(
        title="UID Staked Alphas Distribution",
        width=500,
        height=500
    )


# Display in Streamlit
color_by_v_permit = st.checkbox("Colour by Validator Permit?", value=False)
color_by_macro_vali = st.checkbox("Colour by Macro Validator Vs. Others?", value=False)
# Create separate rows for each subnet
for inst in [inst_sn1, inst_sn9, inst_sn13, inst_sn25, inst_sn37]:
    col1, col2 = st.columns([1, 1])  # Equal width columns

    with col1:
        inst.display_stake_data()  # Show the dataframe

    with col2:
        st.altair_chart(make_chart(inst.to_dataframe(), color_by_v_permit, color_by_macro_vali), use_container_width=True)  # Show the chart

# Sleep and rerun settings
wait_message = st.empty()

for i in range(REFRESH_PARAM):  
    wait_message.write(f"Refreshing in {REFRESH_PARAM - i} seconds")  
    time.sleep(1)  # Wait for 1 second

st.experimental_rerun()  # Forces Streamlit to update

