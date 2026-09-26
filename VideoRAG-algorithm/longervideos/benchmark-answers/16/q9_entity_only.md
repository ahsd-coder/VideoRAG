Collection: 16
QID: 9
Mode: entity_only
Question: In SuperDecisions software, what steps are involved in performing sensitivity analysis for an AHP model?

### Steps Involved in Performing Sensitivity Analysis for an AHP Model Using SuperDecisions Software

#### Step 1: Loading a Sample Model
- **Load a Sample Model**: Begin by loading a sample model in SuperDecisions. For instance, you can load the "Card Choice" model.
- **Access Sensitivity Analysis**: Navigate to the sensitivity analysis feature by selecting `Computation -> AHP Sensitivity`.

#### Step 2: Setting Up Independent and Dependent Variables
- **Edit Independent Variable**: Specify the independent variable that you wish to analyze. This typically involves choosing a criterion or sub-criterion whose variation will be examined.
- **Select Dependent Variable**: Choose the dependent variable that will be affected by changes in the independent variable. This could be an alternative or another criterion.

#### Step 3: Viewing Results
- **Graphical Sensitivity**: Use the graphical sensitivity option to visualize how the priorities of alternatives change as the priority of a criterion varies. For example, you can observe how the best choice of card changes when price becomes more important.
- **Dynamic Sensitivity Analysis**: Perform dynamic sensitivity analysis to understand the impact of varying a specific criterion's importance on all alternatives simultaneously. To initiate this, go to `Computation -> Node Sensitivity`.

#### Step 4: Interpreting Results
- **Rank Reversals**: Pay attention to rank reversals, where the order of alternatives changes significantly as the weight of a criterion is altered. For instance, when the prestige priority exceeds a certain threshold, it may become more favorable to choose one alternative over another.
- **Consistency Check**: Ensure the model maintains consistency throughout the sensitivity analysis by checking the consistency ratio.

#### Step 5: Adjusting Parameters
- **Adjust Parameters**: Modify the parameters and update the model to observe how changes in criteria weights affect the overall priorities of alternatives.
- **Visual Representation**: Utilize bar charts, pie charts, and other visual aids provided by the software to interpret the sensitivity analysis results more effectively.

#### Example Scenarios
- **Example 1**: When the prestige weight is above 27%, the best choice might switch from Honda Civic to Acura TL.
- **Example 2**: When price becomes more important, the best choice might change from one car to another, depending on the priority thresholds set.

By following these steps, you can thoroughly perform sensitivity analysis in SuperDecisions to evaluate the robustness of your decision-making model and understand how variations in criteria weights affect the priorities of alternatives.
