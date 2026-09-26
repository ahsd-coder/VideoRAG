Collection: 16
QID: 22
Mode: entity_only
Question: How does the process of synthesizing a model with sub-criteria differ from synthesizing a model without sub-criteria in SuperDecisions?

### Synthesizing Models with and Without Sub-Criteria in SuperDecisions

#### Models Without Sub-Criteria

When synthesizing a model without sub-criteria, the process is relatively straightforward:

1. **Setup**: Create a model with a single level of criteria and alternatives. For instance, you might have criteria like "Price," "Quality," and "Comfort," directly connected to alternatives such as "Toyota Camry" and "Honda Civic."

2. **Input Judgments**: Enter judgments for each criterion relative to the alternatives. This involves comparing each alternative against the criteria and assigning a relative importance or rating.

3. **Synthesize**: Use the software's synthesis function to compute the overall priorities. This step generates a prioritized list of alternatives based on the combined judgments across all criteria.

#### Models with Sub-Criteria

Models with sub-criteria involve an additional layer of detail and complexity:

1. **Setup**: Create a hierarchical structure where criteria are broken down into sub-criteria. For example, under "Comfort," you might have sub-criteria like "Driving Performance" and "Ride Quality."

2. **Input Judgments**:
   - **Between Criteria and Sub-Criteria**: Enter judgments to establish the relationship between higher-level criteria and their sub-criteria.
   - **Between Sub-Criteria and Alternatives**: Input judgments for each sub-criterion relative to the alternatives. For instance, rate "Driving Performance" for each car model.
   
3. **Synthesize**:
   - **Hierarchical Synthesis**: The software synthesizes judgments from the lowest level (sub-criteria) up to the highest level (alternatives). This ensures that the impact of sub-criteria is accurately reflected in the overall priorities.
   - **Final Prioritization**: Once the synthesis completes, the model outputs the prioritized alternatives, taking into account both the main criteria and their sub-criteria.

### Key Differences

- **Complexity**: Models with sub-criteria require more detailed input as they involve multiple layers of judgments. This makes the setup and synthesis process more intricate but allows for a finer-grained analysis.
  
- **Granularity**: Sub-criteria allow for a more granular breakdown of criteria, enabling a more nuanced evaluation of alternatives. Without sub-criteria, the analysis is more straightforward but potentially less detailed.

- **Synthesis Process**: Models with sub-criteria undergo a hierarchical synthesis process, whereas models without sub-criteria follow a simpler, direct synthesis method.

In summary, while models without sub-criteria are easier to set up and synthesize, models with sub-criteria offer a more detailed and nuanced evaluation by breaking down criteria into smaller, manageable units.
