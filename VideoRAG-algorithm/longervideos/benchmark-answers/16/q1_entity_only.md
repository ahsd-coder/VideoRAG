Collection: 16
QID: 1
Mode: entity_only
Question: How can an AHP model be converted into an ANP model in Super Decisions, and what additional judgments are required?

### Converting an AHP Model to an ANP Model in Super Decisions

To convert an AHP (Analytic Hierarchy Process) model into an ANP (Analytic Network Process) model using Super Decisions, follow these steps:

#### Initial Setup
1. **Open Sample Model**: Start by opening a sample model from the Super Decisions interface. Typically, you can access these models via the `Help` menu under `Sample Models`.
   - Example: Open the "Car_NeuralNet.sdm" model from the "Introductory Models" category.

#### Removing the Goal Cluster
2. **Identify and Remove Goal Cluster**:
   - **AHP vs. ANP Difference**: In AHP models, there is a distinct goal cluster. However, ANP models do not have a goal cluster.
   - **Action**: Remove the goal cluster from your AHP model. Highlight the goal node and delete it from the model.
   - **Confirmation**: Ensure that the model now reflects the ANP structure without a goal cluster.

#### Adding Connections Between Criteria and Alternatives
3. **Create Connections**:
   - **Purpose**: In ANP models, you need to establish connections between criteria and alternatives, as well as among criteria themselves.
   - **Process**: Use the `Make/Show Connections` option to create these connections. This involves selecting the appropriate criteria and alternatives and establishing links between them.
   - **Example**: If you have criteria such as "Prestige" and "Price," and alternatives like "Acura TL," "Toyota Camry," and "Honda Civic," you would create connections from each criterion to each alternative.

#### Entering Judgments
4. **Enter Pairwise Comparisons**:
   - **Judgment Entry**: Enter judgments for all the newly established connections. This involves comparing each criterion with respect to each alternative and vice versa.
   - **Tools**: Utilize different judgment entry methods provided by Super Decisions, such as the Graphical, Verbal, Matrix, and Questionnaire modes.
     - **Graphical Mode**: Move graphics to set values.
     - **Verbal Mode**: Drag and drop to find preferences.
     - **Matrix View**: Input actual numbers for the super matrix.
     - **Questionnaire Mode**: Select color buttons on a scale from 1 to 9 to indicate preference.
   - **Direct Mode**: Input tangible values directly if applicable.

#### Synthesizing Results
5. **Synthesize Priorities**:
   - **Sanity Check**: Before synthesizing, ensure there are no errors or warnings by conducting a sanity check.
   - **Synthesize**: Go to the `Computations` section and select `Synthesize` to generate the final priorities for your alternatives.
   - **Review Results**: Examine the synthesized priorities to identify the best alternative based on the ANP model.

#### Additional Judgments Required
- **Comparative Judgments**: In ANP, you need to provide comparative judgments for each pair of criteria and alternatives. Unlike AHP, where judgments are made hierarchically, ANP requires judgments to be made in a network structure.
- **Dynamic Sensitivity Analysis**: Consider performing sensitivity analysis to understand how changes in criteria weights affect the overall priorities of alternatives.

By following these steps, you can effectively convert an AHP model into an ANP model in Super Decisions, ensuring that all necessary judgments are made and the model accurately reflects the relationships between criteria and alternatives.
