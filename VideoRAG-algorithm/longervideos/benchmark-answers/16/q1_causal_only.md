Collection: 16
QID: 1
Mode: causal_only
Question: How can an AHP model be converted into an ANP model in Super Decisions, and what additional judgments are required?

### Converting an AHP Model to an ANP Model in Super Decisions

#### Step-by-Step Guide:

1. **Open the Sample Model:**
   - Begin by opening a sample model from the "Help" menu. Specifically, you can use the "Car Selection" model under "Introductory Models."

2. **Understand the Initial Setup:**
   - The initial network model will have a "Criteria" cluster and an "Alternatives" cluster. Note that an ANP model does not require a "Goal" cluster, unlike an AHP model.

3. **Remove the Goal Node:**
   - Highlight the "Goal Node" in the "Criteria" cluster and remove it. This step is crucial because ANP models do not have a dedicated goal cluster.

4. **Prepare for Pairwise Comparisons:**
   - Navigate to the "Judgments" tab to prepare for pairwise comparisons. Ensure that the weights of nodes within clusters are equal before proceeding.

5. **Perform Pairwise Comparisons:**
   - Start comparing criteria with respect to the goal node. Use the "Judgments" tab to make these comparisons. The video tutorials demonstrate how to enter judgments using a scale from 1 to 9 in the questionnaire mode.

6. **Connect Alternatives to Criteria:**
   - Connect each alternative to all the criteria nodes. This ensures that each alternative is evaluated against every criterion.

7. **Evaluate Second-Level Criteria:**
   - If your model includes second-level criteria, ensure that you make judgments for all clusters. For example, compare "rebuild & maintain" criteria against the goal node.

8. **Synthesize Results:**
   - Once all judgments are entered, synthesize the results by selecting the "Synthesize" option from the "Computations" menu. This will generate the final priorities for each alternative.

#### Additional Judgments Required:

- **Comparisons Between Criteria:**
  - In an ANP model, you need to compare criteria against each other as well as against the alternatives. This involves assessing how each criterion relates to others in terms of importance or impact.

- **Comparisons Between Alternatives:**
  - Compare each alternative against every criterion. This step helps in determining the relative importance of each alternative with respect to the criteria.

- **Dynamic Sensitivity Analysis:**
  - Perform sensitivity analysis to understand how changes in criterion weights affect the overall priorities. This involves using dynamic sensitivity analysis methods to evaluate model robustness.

#### Key Points to Remember:

- **No Goal Cluster in ANP:** Unlike AHP models, ANP models do not have a separate goal cluster. Instead, they rely on the relationships between criteria and alternatives.
- **Hierarchical and Network Structures:** ANP models allow for a more complex network structure where criteria can influence each other, whereas AHP models are strictly hierarchical.
- **Judgment Entry:** Ensure judgments are entered accurately to reflect the true priorities and relationships within the model.

By following these steps and understanding the additional judgments required, you can successfully convert an AHP model into an ANP model in Super Decisions, leveraging the enhanced capabilities of ANP for more nuanced decision-making.
