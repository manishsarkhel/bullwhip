import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# --- Game Configuration ---
TOTAL_ROUNDS = 20
INITIAL_INVENTORY = 40
HOLDING_COST = 1.0    # Cost per unit of inventory per week
BACKORDER_COST = 2.0  # Cost per unit of unmet demand per week
LEAD_TIME = 2         # Weeks it takes for an order to arrive

# Pre-programmed demand (Hidden from the player)
# Steady at 10, jumps to 20 at week 5 to trigger the bullwhip effect
DEMAND_SCENARIO = [10, 10, 10, 10, 20, 20, 20, 20, 20, 20, 
                   20, 20, 20, 20, 20, 20, 20, 20, 20, 20]

def initialize_game():
    """Initializes the session state variables for a new game."""
    st.session_state.round = 1
    st.session_state.inventory = INITIAL_INVENTORY
    st.session_state.backorders = 0
    st.session_state.total_cost = 0.0
    st.session_state.order_pipeline = [10] * LEAD_TIME # Initial pipeline deliveries
    
    # History tracking for the final analysis
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
st.set_page_config(page_title="Bullwhip Effect Simulator", layout="wide")

st.title("🏭 The Bullwhip Effect Simulator")
st.markdown("""
**Role:** Wholesaler  
**Objective:** Minimize your total costs over 20 weeks.  
**Rules:**
* You receive weekly demand from retailers.
* You must place orders to the Manufacturer to replenish your stock.
* **Lead Time:** Orders take **2 weeks** to arrive.
* **Holding Cost:** $1.00 per unit left in inventory at the end of the week.
* **Backorder Cost:** $2.00 per unit of demand you fail to meet (stockouts carry over).
""")

# Initialize state if it doesn't exist
if 'round' not in st.session_state:
    initialize_game()

# --- Game Over Screen ---
if st.session_state.game_over:
    st.header("🏁 Game Over!")
    st.subheader(f"Your Final Score (Total Cost): **${st.session_state.total_cost:,.2f}**")
    st.markdown("*(Lower is better. A perfect score with perfect foresight is around $400)*")
    
    # Calculate variances to prove the Bullwhip Effect
    df = pd.DataFrame(st.session_state.history)
    demand_var = df['Demand'].var()
    order_var = df['Player_Orders'].var()
    bwe_index = order_var / demand_var if demand_var > 0 else 1
    
    st.markdown("### The Bullwhip Analysis")
    if bwe_index > 1:
        st.error(f"**Bullwhip Effect Detected!** Your order variance was {bwe_index:.2f}x higher than the actual demand variance. This causes chaos upstream in the supply chain.")
    else:
        st.success(f"**Great Job!** You avoided the Bullwhip Effect. Your order variance was stable compared to demand (Ratio: {bwe_index:.2f}).")

    # Plotting the results
    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax1.plot(df['Week'], df['Demand'], label='Retailer Demand', color='blue', marker='o', linestyle='--')
    ax1.plot(df['Week'], df['Player_Orders'], label='Your Orders to Mfg', color='red', marker='x')
    ax1.set_xlabel('Week')
    ax1.set_ylabel('Units')
    ax1.set_title('Demand vs. Your Orders (The Bullwhip Effect)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    st.pyplot(fig)
    
    st.dataframe(df.set_index('Week'))
    
    if st.button("Play Again"):
        initialize_game()
        st.rerun()

# --- Main Game Dashboard ---
else:
    current_week = st.session_state.round
    current_demand = DEMAND_SCENARIO[current_week - 1]
    incoming_delivery = st.session_state.order_pipeline[0]
    
    # Dashboard metrics
    st.header(f"📅 Week {current_week} of {TOTAL_ROUNDS}")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📦 Current Inventory", st.session_state.inventory)
    col2.metric("⚠️ Backorders (Owed)", st.session_state.backorders)
    col3.metric("🚚 Arriving this week", incoming_delivery)
    col4.metric("💰 Total Cost So Far", f"${st.session_state.total_cost:.2f}")
    
    st.divider()
    
    # This week's events
    st.markdown(f"### 📥 Retailer Demand this week: **{current_demand} units**")
    
    with st.form("order_form"):
        st.markdown("Based on your current stock, arriving shipments, and this week's demand, how many units do you want to order from the Manufacturer?")
        order_amount = st.number_input("Order Quantity", min_value=0, max_value=500, value=10, step=5)
        submitted = st.form_submit_button("Place Order & Advance Week")
        
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
            
            # 5. Save History
            st.session_state.history['Week'].append(current_week)
            st.session_state.history['Demand'].append(current_demand)
            st.session_state.history['Player_Orders'].append(order_amount)
            st.session_state.history['Inventory'].append(new_inventory)
            st.session_state.history['Backorders'].append(new_backorders)
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
            
    # Show pipeline visibility to help students plan
    with st.expander("🔍 View Order Pipeline (En route shipments)"):
        st.write(f"Arriving Next Week: {st.session_state.order_pipeline[0]} units")
        if LEAD_TIME > 1:
            st.write(f"Arriving in 2 Weeks: {st.session_state.order_pipeline[1]} units")
