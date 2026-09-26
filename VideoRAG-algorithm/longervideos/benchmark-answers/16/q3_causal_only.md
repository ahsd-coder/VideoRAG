Collection: 16
QID: 3
Mode: causal_only
Question: How is the unweighted supermatrix used in AHP, and how is it generated in Super Decisions?

### Unweighted Supermatrix in AHP and Its Generation in Super Decisions

#### Unweighted Supermatrix in AHP
In the Analytic Hierarchy Process (AHP), the unweighted supermatrix plays a pivotal role in consolidating pairwise comparison matrices into a single matrix that reflects the overall priorities and relationships between criteria and alternatives. Here are the key points:

1. **Consolidation of Comparisons**: The unweighted supermatrix combines the judgments made in pairwise comparison matrices for different criteria and alternatives. This consolidation ensures that each criterion and alternative is evaluated uniformly.
   
2. **Equal Weight Distribution**: Initially, each component in the supermatrix is assigned equal weight, typically 1/n where n is the number of components. This ensures that no criterion or alternative is biased during the initial synthesis phase.

3. **Hierarchical Structure Representation**: The supermatrix represents the hierarchical structure of the decision-making problem, reflecting the connections between the goal, criteria, and alternatives. Each layer of the hierarchy is mapped into the supermatrix, allowing for a comprehensive analysis.

4. **Normalization and Synthesis**: After generating the unweighted supermatrix, the next step often involves normalizing the matrix and synthesizing the priorities to obtain a final set of priorities for each alternative.

#### Generation of Unweighted Supermatrix in Super Decisions

Super Decisions is a software tool widely used for implementing AHP and generating unweighted supermatrices. Here's how it is done:

1. **Initial Setup**:
   - Open the Super Decisions software and navigate to the relevant project or create a new one.
   - Define the hierarchy by specifying the goal, criteria, and alternatives. Ensure that the nodes are correctly connected to form a coherent hierarchy.

2. **Pairwise Comparisons**:
   - Perform pairwise comparisons for each criterion and alternative. This involves selecting nodes and comparing them using a scale (often 1-9).
   - Input the judgments into the software, ensuring consistency in the comparisons.

3. **Generating the Unweighted Supermatrix**:
   - Once the pairwise comparisons are complete, navigate to the computational features within Super Decisions.
   - Select the option to generate the unweighted supermatrix. This step typically involves accessing the "Computations" menu and selecting "Unweighted Supermatrix".
   - The software will automatically generate the unweighted supermatrix based on the input judgments and hierarchical structure.

4. **Review and Verification**:
   - Review the generated unweighted supermatrix to ensure that all components have equal initial weights.
   - Verify that the matrix accurately reflects the hierarchical relationships and comparisons made during the pairwise comparisons.

5. **Further Analysis**:
   - Use the unweighted supermatrix as a foundation for further analysis, such as normalization, synthesis, and sensitivity analysis.
   - Save the generated matrix for future reference or export it for further processing outside the software.

### Example Scenarios

- **Job Selection**:
  - Criteria might include prestige, cost, and comfort. Alternatives could be different car models. The unweighted supermatrix would consolidate these comparisons to derive overall priorities for each car model.

- **Nuclear Waste Disposal**:
  - Criteria could be state of technology, health impacts, cost, socio-economic impact, lead time, and political impact. Alternatives might be different disposal methods. The supermatrix would combine judgments for these criteria and alternatives to determine the best disposal strategy.

By following these steps, users can effectively utilize Super Decisions to generate and analyze unweighted supermatrices for complex decision-making scenarios.
