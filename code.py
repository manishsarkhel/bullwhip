import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import random

# --- Game Configuration ---
TOTAL_ROUNDS = 20
INITIAL_INVENTORY = 40
HOLDING_COST = 2.0    # Punishing holding cost
BACKORDER_COST = 5.0  # Punishing backorder cost
LEAD_TIME = 3         # 3-week lead time makes forecasting very difficult

def generate_phased_demand(total_weeks):
    """
    Generates demand that shifts through distinct market phases, 
    making a static ordering strategy mathematically terrible.
    """
    demand = []
    for week in range(1, total_weeks + 1):
        if week <= 5:
            # Phase 1: Stable, quiet market
            val = int(random.gauss(12, 2))
        elif week <= 12:
            # Phase 2: Sudden viral growth / sustained high demand
            val = int(random.gauss(32, 5))
        else:
            # Phase 3: Sudden market drop-off / competitor enters
            val = int(random.gauss(8, 2))
            
        demand.append(max(0, val)) # Ensure no negative demand
    return demand

# Generate the demand scenario for this session
if 'demand_scenario' not in st.session_state:
    st.session_state.demand_scenario = generate_phased_demand(TOTAL_ROUNDS)

def initialize_game():
    """Initializes the session state variables for a new game."""
    st.session_state.round = 1
    st.session_state.inventory = INITIAL_INVENTORY
    st.session_state.backorders = 0
    st.session_state.total_cost = 0.0
    st.session_state.order_pipeline = [12, 12, 12] # Pipeline matched to initial phase
    st.session_state.demand_scenario = generate_phased_demand(TOTAL_ROUNDS) 
    st.session_state.last_order = 12 # Track last order for UI default
    
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
st.set_page_config(page_title="Advanced Bullwhip Simulator", layout="wide")

st.title("🌪️ The Advanced Bullwhip Simulator (Shifting Markets)")
st.markdown("""
**Role:** Wholesaler | **Objective:** Minimize total costs over 20 weeks.  
**Warning: Market conditions will shift. A static strategy will fail.**
* **Lead Time:** Orders take **3 WEEKS** to arrive.
* **Holding Cost:** $2.00 per unit left in inventory.
* **Backorder Cost:** $5.00 per unit of missed demand.
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
    max_y = max([60] + df['Demand'].tolist() + df['Player_Orders'].tolist() + df['Inventory'].tolist()) if not df.empty else 60
    ax1.set_ylim(0, max_y + 10)
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)
    
    # Highlight phase changes if they have occurred
    if len(df) >= 6:
        ax1.axvline(x=5.5, color='gray', linestyle=':', alpha=0.7)
        ax1.text(5.6, max_y, 'Growth Phase', rotation=90, verticalalignment='top', color='gray')
    if len(df) >= 13:
        ax1.axvline(x=12.5, color='gray', linestyle=':', alpha=0.7)
        ax1.text(12.6, max_y, 'Decline Phase', rotation=90, verticalalignment='top', color='gray')
        
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
        st.error(f"**Severe Bullwhip Effect Detected!** Your order variance was {bwe_index:.2f}x higher than the actual demand variance. The 3-week delay caused you to over-correct wildly when the market shifted.")
    else:
        st.success(f"**Master Planner!** You managed the market regime changes brilliantly. Your order variance remained stable relative to demand (Ratio: {bwe_index:.2f}).")

    st.pyplot(plot_live_history(df))
    
    with st.expander("View Raw Data"):
        st.dataframe(df.set_index('Week'))
    
    if st.button("Restart Simulation (New Market Scenario)"):
        initialize_game()
        st.rerun()

# --- Main Game Dashboard ---
else:
    current_week = st.session_state.round
    current_demand = st.session_state.demand_scenario[current_week - 1]
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
            
            # Default value is now whatever they ordered LAST week. 
            # If they keep clicking without looking, they will fail when the phase changes.
            order_amount = st.number_input("Order Quantity", min_value=0, max_value=1000, value=st.session_state.last_order, step=5)
            submitted = st.form_submit_button("Place Order & Advance Week ➡️")
            
            if submitted:
                # Process game logic
                received = st.session_state.order_pipeline.pop(0)
                st.session_state.order_pipeline.append(order_amount)
                
                net_inventory = st.session_state.inventory - st.session_state.backorders + received
                new_net_inventory = net_inventory - current_demand
                
                if new_net_inventory > 0:
                    new_inventory = new_net_inventory
                    new_backorders = 0
                else:
                    new_inventory = 0
                    new_backorders = abs(new_net_inventory)
                    
                cost_this_week = (new_inventory * HOLDING_COST) + (new_backorders * BACKORDER_COST)
                
                # Save Data
                st.session_state.history['Week'].append(current_week)
                st.session_state.history['Demand'].append(current_demand)
                st.session_state.history['Player_Orders'].append(order_amount)
                st.session_state.history['Inventory'].append(st.session_state.inventory)
                st.session_state.history['Backorders'].append(st.session_state.backorders)
                st.session_state.history['Cost_This_Week'].append(cost_this_week)
                
                # Update State
                st.session_state.inventory = new_inventory
                st.session_state.backorders = new_backorders
                st.session_state.total_cost += cost_this_week
                st.session_state.last_order = order_amount # Remember order for next turn's default
                
                if current_week >= TOTAL_ROUNDS:
                    st.session_state.game_over = True
                else:
                    st.session_state.round += 1
                    
                st.rerun()
