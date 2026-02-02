import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# INITIAL CONSTRAINTS
threshold = 0.95                                # Wave success rate of 95% enforced
weapon_number_range = range(0, 7, 1)            # Max total number of weapons is 6
attack_speed_range = range(0, 201, 1)           # Max 'reasonable' attack speed is 200, however in reality it can occasionally go higher in-game
accuracy_percentage_range = range(0, 101, 1)    # Accuracy must be between 0 and 100
weapon_dict = {"T2 VS": (55, 0.99, 1/1.11),     # Weapon tier: (Cost, OHKO rate per attack, attack rate per sec)
               "T3 VS": (100, 0.98, 1/1.03),
               "T4 VS": (200, 0.97, 1/1.02)
               }

# COST FUNCTION 
# Function determining the cost of each combination which will be optimised for
# Attack speed is priced at 5.28 materials per 1%, which is the average of all attack speed items in the shop
# Each weapon is priced as it would be in the shop
def cost_function(VS_T2_Num, VS_T3_Num, VS_T4_Num, AttSpe):
    return AttSpe*5.28+VS_T2_Num*weapon_dict["T2 VS"][0]+VS_T3_Num*weapon_dict["T3 VS"][0]+VS_T4_Num*weapon_dict["T4 VS"][0]

# WAVE SUCCESS FUNCTION
# Uses the OHKO rate and attack speed for each weapon to calculate the chance of success in a 60 sec wave
def wave_success_rate_function(VS_T2_Num, VS_T3_Num, VS_T4_Num, AttSpe, AccuracyPercentage):  

    # Calculate the chance that each weapon will FAIL to OHKO each second
    VS_T2_OHKO_failure_rate_per_sec = weapon_dict["T2 VS"][1]**(VS_T2_Num*weapon_dict["T2 VS"][2]*(1+AttSpe/100))
    VS_T3_OHKO_failure_rate_per_sec = weapon_dict["T3 VS"][1]**(VS_T3_Num*weapon_dict["T3 VS"][2]*(1+AttSpe/100))
    VS_T4_OHKO_failure_rate_per_sec = weapon_dict["T4 VS"][1]**(VS_T4_Num*weapon_dict["T4 VS"][2]*(1+AttSpe/100))
    
    # Calculate the OHKO chance per second
    OHKO_Rate_Per_Sec = 1-(VS_T2_OHKO_failure_rate_per_sec)*(VS_T3_OHKO_failure_rate_per_sec)*(VS_T4_OHKO_failure_rate_per_sec)
    
    # Return the OHKO rate per wave
    return 1-(1-OHKO_Rate_Per_Sec)**(60*AccuracyPercentage/100)

# OPTIMISATION FUNCTION
# Goes through all possible combinations of weapons and attack speed and returns the combination that minimises cost while meeting the success rate threshold
def optimisation_algorithm(weapon_number_range, attack_speed_range, AccuracyPercentage):
    # Set minimum cost as something extra-ordinarily high to serve as the initial comparator
    min_cost = 1e6
    
    # Cycle through all possible weapon combinations
    for VS_T2_Num in weapon_number_range:
        for VS_T3_Num in weapon_number_range:
            for VS_T4_Num in weapon_number_range:
                
                # Disregard the weapon combination if it exceeds the maximum number of weapons
                if VS_T2_Num + VS_T3_Num + VS_T4_Num <=6:
                    
                    # Cycle through all possible attack speed values
                    for AttSpe in attack_speed_range:
                        
                        # Only proceed if the combination meets the success rate threshold
                        if wave_success_rate_function(VS_T2_Num, VS_T3_Num, VS_T4_Num, AttSpe, AccuracyPercentage) > 0.95:
                            cost_check = cost_function(VS_T2_Num, VS_T3_Num, VS_T4_Num, AttSpe)
                            
                            # Update minimum cost and best combo if a lower cost is found
                            if cost_check < min_cost:
                                min_cost = cost_check
                                best_combo = [AccuracyPercentage,6-VS_T2_Num- VS_T3_Num- VS_T4_Num, VS_T2_Num, VS_T3_Num, VS_T4_Num, AttSpe, min_cost, wave_success_rate_function(VS_T2_Num, VS_T3_Num, VS_T4_Num, AttSpe, AccuracyPercentage)]
    
    # If there were no successful combinations, the min_cost will remain unchanged, therefore return a blank combination
    if min_cost == 1e6:
        return [AccuracyPercentage,0,0,0,0,0,0,0]
    
    # Otherwise return the cheapest combination
    else:
        return best_combo

# Create an empty DataFrame to store the results in
Summary_DF = pd.DataFrame(np.nan, index = accuracy_percentage_range, columns = ["Accuracy", "Number of Non-OHKO Weapons","Number of T2 VS", "Number of T3 VS", "Number of T4 VS", "Number of AttSpe", "Minimum Cost", "Chance of Success in Wave"])

# ITERATE OVER ACCURACY LEVELS
# Iterate our optimisation function over each accuracy level from 0-100%
for AccuracyPercentage in accuracy_percentage_range:
    
    # Store the optimised combination in the DataFrame
    Summary_DF.iloc[AccuracyPercentage,0:] = optimisation_algorithm(weapon_number_range, attack_speed_range, AccuracyPercentage)

###################
# FINAL DATA OUTPUT
###################
print(Summary_DF)

###############
# PLOT THE DATA
###############

# Generate three subplots - 1) cost of build vs accuracy, 2) number of each weapon required vs accuracy, 3) attack speed required vs accuracy
fig, ax = plt.subplots(nrows=3, ncols=1, figsize=(12, 8),layout="constrained")
fig.text(0.5, 3.7, "The cheapest possible combination of weapons and attack speed for a given accuracy level, with each combination producing a 95% success rate per wave", horizontalalignment='center', verticalalignment='center', transform=plt.gca().transAxes, style = 'italic')
colours = ("#2e536eff", "#5A307D", "#7B2626", "#196505")

# SUBPLOT 1 - Cost of build vs accuracy
ax[0].stackplot(Summary_DF["Accuracy"], Summary_DF["Number of T2 VS"]*55, Summary_DF["Number of T3 VS"]*100, Summary_DF["Number of T4 VS"]*200, Summary_DF["Number of AttSpe"]*5.28, colors=colours, labels=["T2 VS", "T3 VS", "T4 VS", "AttSpe"])
ax[0].set_ylabel("Cost (materials)")
ax[0].legend(loc="upper right")
ax[0].yaxis.set_major_formatter(plt.matplotlib.ticker.StrMethodFormatter('{x:,.0f}'))
ax[0].set_title("Brotato Cost Optimisation", pad=30, fontsize=24)
ax[0].set_ylim(0,2500)
ax[0].yaxis.set_major_locator(mticker.MultipleLocator(base=500))

# SUBPLOT 2 - Number of each weapon required vs accuracy
ax[1].bar(Summary_DF["Accuracy"], Summary_DF["Number of T2 VS"], color=colours[0], width=1)
ax[1].bar(Summary_DF["Accuracy"], Summary_DF["Number of T3 VS"], bottom=Summary_DF["Number of T2 VS"], color=colours[1], width=1)
ax[1].bar(Summary_DF["Accuracy"], Summary_DF["Number of T4 VS"], bottom=Summary_DF["Number of T2 VS"]+Summary_DF["Number of T3 VS"], color=colours[2], width=1)
ax[1].set_ylabel("Weapon\nCombination")
ax[1].set_ylim(0,7)
ax[1].yaxis.set_major_locator(mticker.MultipleLocator(base=2))
ax[1].yaxis.set_minor_locator(mticker.MultipleLocator(base=1))
ax[1].xaxis.set_minor_locator(mticker.MultipleLocator(base=5))

# SUBPLOT 3 - Attack speed required vs accuracy
ax[2].plot(Summary_DF["Accuracy"], Summary_DF["Number of AttSpe"], color="#196505")
ax[2].set_ylabel("Required\nAttack Speed")
ax[2].yaxis.set_major_formatter(plt.matplotlib.ticker.StrMethodFormatter('{x:,.0f}%'))
ax[2].yaxis.set_major_locator(mticker.MultipleLocator(base=50))
ax[2].set_ylim(0,200)
ax[2].fill_between(Summary_DF["Accuracy"], Summary_DF["Number of AttSpe"], color="#196505", alpha=0.3)

# Generic subplot formatting
for n, ax in enumerate(ax.flat):
    if n == 0 or n == 2:
        ax.minorticks_on()
    ax.grid(which='major', color='black', linestyle='-', linewidth=0.8)
    ax.grid(which='minor', color='black', linestyle='--', linewidth=0.4, alpha=0.7)
    ax.set_xlim(0,100)
    ax.set_xlabel("Accuracy")
    ax.xaxis.set_major_formatter(plt.matplotlib.ticker.StrMethodFormatter('{x:,.0f}%'))

plt.show()