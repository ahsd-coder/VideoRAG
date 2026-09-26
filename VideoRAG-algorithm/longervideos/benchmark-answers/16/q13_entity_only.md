Collection: 16
QID: 13
Mode: entity_only
Question: How to establish connections between different elements in an AHP hierarchy within SuperDecisions?

### Establishing Connections Between Elements in an AHP Hierarchy Using SuperDecisions

To establish connections between different elements in an AHP (Analytic Hierarchy Process) hierarchy within the SuperDecisions software, follow these steps:

1. **Creating Clusters**:
   - Start by creating clusters for your nodes. Clusters are containers for knowledge and help organize your hierarchy. For example, you might create clusters for "Goal," "Criteria," and "Alternatives."
     - Open SuperDecisions and navigate to the "Design" section.
     - Click on "Cluster" and then "New" to create a new cluster. Name it appropriately, such as "Goal."
     - Repeat the process for other clusters like "Criteria" and "Alternatives."

2. **Adding Criteria and Alternatives**:
   - Add criteria under the "Criteria" cluster and alternatives under the "Alternatives" cluster.
     - Go to the "Design" section and click on "Add" to add nodes under your clusters.
     - For example, add criteria like "Price," "Fuel Efficiency," and "Comfort" under the "Criteria" cluster.
     - Similarly, add alternatives like "Acura TL," "Toyota Camry," and "Honda Civic" under the "Alternatives" cluster.

3. **Connecting Nodes**:
   - Connect the goal node to all criteria nodes.
     - Right-click on the goal node and select "Connect" or "Node Connection Form."
     - Choose the criteria nodes you want to connect to the goal node.
   - Connect each criterion node to all alternative nodes.
     - Right-click on a criterion node and select "Connect."
     - Choose the alternative nodes you want to connect to this criterion node.

4. **Entering Judgments**:
   - Enter judgments for the connections you've established.
     - Navigate to the "Assess/Compare" section and select "Pairwise Comparison."
     - Use the questionnaire mode or direct entry mode to input judgments.
     - For example, rate how important "Price" is compared to "Fuel Efficiency" for each alternative.

5. **Synthesizing Results**:
   - Once all judgments are entered, synthesize the results to obtain priorities.
     - Go to the "Computations" section and select "Synthesize."
     - This will generate the overall priorities for your alternatives based on the criteria and the goal.

### Example Workflow

Here's a simplified workflow based on the steps outlined above:

1. **Create Clusters**:
   ```plaintext
   - Goal
   - Criteria (Price, Fuel Efficiency, Comfort)
   - Alternatives (Acura TL, Toyota Camry, Honda Civic)
   ```

2. **Connect Goal to Criteria**:
   ```plaintext
   - Goal → Price
   - Goal → Fuel Efficiency
   - Goal → Comfort
   ```

3. **Connect Criteria to Alternatives**:
   ```plaintext
   - Price → Acura TL
   - Price → Toyota Camry
   - Price → Honda Civic
   - Fuel Efficiency → Acura TL
   - Fuel Efficiency → Toyota Camry
   - Fuel Efficiency → Honda Civic
   - Comfort → Acura TL
   - Comfort → Toyota Camry
   - Comfort → Honda Civic
   ```

4. **Enter Judgments**:
   - Use pairwise comparison to rate how important each criterion is for each alternative.
   - For example, rate "Price" for "Acura TL" compared to "Toyota Camry" and "Honda Civic."

5. **Synthesize Results**:
   - Synthesize the judgments to get the final priorities for each alternative.

By following these steps, you can effectively establish and manage connections between different elements in an AHP hierarchy within SuperDecisions.
