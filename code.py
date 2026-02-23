import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import random

# --- Game Configuration ---
TOTAL_ROUNDS = 20
INITIAL_INVENTORY = 50
HOLDING_COST = 2.0    # Increased holding cost
BACKORDER_COST = 5.0  # Punishing backorder cost
LEAD_TIME = 3         # 3-week lead time makes forecasting very difficult

# Tough Demand Scenario: Noise, a sudden spike, a sudden drop, and another spike.
DEMAND_SCENARIO = [12, 15, 11, 14, 13,   # Weeks 1-5: Stable but noisy
                   38, 35, 32, 39, 34,   # Weeks 6-10: Massive unexpected spike
                   12, 10, 14, 11, 15,   # Weeks 11-15: Sudden drop back to normal
                   35, 32, 38, 31, 35]   # Weeks 16-20: Second spike

def initialize_game():
    """Initializes the session state variables for a new game."""
    st.session_state.round = 1
    st.session_state.inventory = INITIAL_INVENTORY
    st.session_state.backorders = 0
    st.session_state.total_cost = 0.0
    st.session_state.order_pipeline = [12, 12, 12] # Pipeline matched to lead time
    
    st.session_state.history = {
        'Week': [],
        'Demand': [],
        'Player_Orders': [],
        'Inventory': [],
        'Backorders': [],
        'Cost_This_Week': []
    }
    st.session_state.game_over = False

# --- App Layout & Logic ---
st.set_page_config(page_title="Tough Bullwhip Simulator", layout="wide")

st.title("🌪️ The Advanced Bullwhip Simulator")
st.markdown("""
**Role:** Wholesaler | **Objective:** Minimize total costs over 20 weeks.  
**Warning: This scenario is highly volatile.**
* **Lead Time:** Orders take **3 WEEKS** to arrive.
* **Holding Cost:** $2.00 per unit left in inventory.
* **Backorder Cost:** $5.00 per unit of missed demand (Ouch!).
""")

# Initialize state if it doesn't exist
if 'round' not in st.session_state:
    initialize_game()

# --- Reusable function to plot live history ---
def plot_live_history(df):
    fig, ax1 = plt.subplots(figsize=(12, 5))
    
    # Plotting lines
    if not df.empty:
        ax1.plot(df['Week'], df['Demand'], label='Retailer Demand', color='blue', marker='o', linewidth=2)
        ax1.plot(df['Week'], df['Player_Orders'], label='Your Orders to Mfg', color='red', marker='x', linestyle='--', linewidth=2)
        ax1.plot(df['Week'], df['Inventory'], label='Your Inventory', color='green', marker='s', alpha=0.5)
    
    ax1.set_xlabel('Week')
    ax1.set_ylabel('Units')
    ax1.set_title('Live Supply Chain Metrics')
    ax1.set_xlim(1, TOTAL_ROUNDS)
    # Give a bit of headroom on the y-axis
    max_y = max([50] + df['Demand'].tolist() + df['Player_Orders'].tolist() + df['Inventory'].tolist()) if not df.empty else 50
    ax1.set_ylim(0, max_y + 10)
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)
    return fig

# --- Game Over Screen ---
if st.session_state.game_over:
    st.header("🏁 Simulation Complete!")
    st.subheader(f"Your Final Score (Total Cost): **${st.session_state.total_cost:,.2f}**")
    
    df = pd.DataFrame(st.session_state.history)
    demand_var = df['Demand'].var()
    order_var = df['Player_Orders'].var()
    bwe_index = order_var / demand_var if demand_var > 0 else 1
    
    st.markdown("### Post-Mortem Analysis")
    if bwe_index > 1.2:
        st.error(f"**Severe Bullwhip Effect Detected!** Your order variance was {bwe_index:.2f}x higher than the actual demand variance. The 3-week delay and punishing stockout costs likely caused you to panic order.")
    else:
        st.success(f"**Master Planner!** You managed the turbulence brilliantly. Your order variance remained stable (Ratio: {bwe_index:.2f}).")

    st.pyplot(plot_live_history(df))
    
    with st.expander("View Raw Data"):
        st.dataframe(df.set_index('Week'))
    
    if st.button("Restart Simulation"):
        initialize_game()
        st.rerun()

# --- Main Game Dashboard ---
else:
    current_week = st.session_state.round
    current_demand = DEMAND_SCENARIO[current_week - 1]
    incoming_delivery = st.session_state.order_pipeline[0]
    
    # Render the Live Dashboard
    st.header(f"📅 Week {current_week} of {TOTAL_ROUNDS}")
    
    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📦 Current Inventory", st.session_state.inventory)
    col2.metric("⚠️ Backorders (Owed)", st.session_state.backorders)
    col3.metric("🚚 Arriving this week", incoming_delivery)
    col4.metric("💰 Total Cost So Far", f"${st.session_state.total_cost:,.2f}")
    
    st.divider()
    
    # Layout with Plot on the left, Controls on the right
    plot_col, control_col = st.columns([2, 1])
    
    with plot_col:
        st.markdown("### 📈 Performance History")
        df_history = pd.DataFrame(st.session_state.history)
        st.pyplot(plot_live_history(df_history))
        
    with control_col:
        st.markdown("### 📥 Action Required")
        st.info(f"**Retailer Demand this week: {current_demand} units**")
        
        st.markdown("**Order Pipeline Visibility:**")
        st.write(f"- Arriving Next Week: **{st.session_state.order_pipeline[1]}**")
        st.write(f"- Arriving in 2 Weeks: **{st.session_state.order_pipeline[2]}**")
        
        with st.form("order_form"):
            st.markdown("Analyze the chart and pipeline. How many units will you order?")
            order_amount = st.number_input("Order Quantity", min_value=0, max_value=1000, value=15, step=5)
            submitted = st.form_submit_button("Place Order & Advance Week ➡️")
            
            if submitted:
                # 1. Process incoming delivery
                received = st.session_state.order_pipeline.pop(0)
                
                # 2. Add new order to the end of the pipeline
                st.session_state.order_pipeline.append(order_amount)
                
                # 3. Calculate new inventory and backorders
                net_inventory = st.session_state.inventory - st.session_state.backorders + received
                new_net_inventory = net_inventory - current_demand
                
                if new_net_inventory > 0:
                    new_inventory = new_net_inventory
                    new_backorders = 0
                else:
                    new_inventory = 0
                    new_backorders = abs(new_net_inventory)
                    
                # 4. Calculate costs
                cost_this_week = (new_inventory * HOLDING_COST) + (new_backorders * BACKORDER_COST)
                
                # 5. Save History for the plot
                st.session_state.history['Week'].append(current_week)
                st.session_state.history['Demand'].append(current_demand)
                st.session_state.history['Player_Orders'].append(order_amount)
                st.session_state.history['Inventory'].append(st.session_state.inventory) # Record start-of-week inventory
                st.session_state.history['Backorders'].append(st.session_state.backorders)
                st.session_state.history['Cost_This_Week'].append(cost_this_week)
                
                # 6. Update State
                st.session_state.inventory = new_inventory
                st.session_state.backorders = new_backorders
                st.session_state.total_cost += cost_this_week
                
                if current_week >= TOTAL_ROUNDS:
                    st.session_state.game_over = True
                else:
                    st.session_state.round += 1
                    
                st.rerun()
