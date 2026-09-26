Collection: 16
QID: 21
Mode: entity_only
Question: How can the 'inconsistency report' feature in SuperDecisions be used to identify and rectify inconsistencies in pairwise comparison judgments? 

### Using the 'Inconsistency Report' Feature in SuperDecisions

The 'Inconsistency Report' feature in SuperDecisions is a powerful tool for identifying and rectifying inconsistencies in pairwise comparison judgments. Here's a step-by-step guide on how to use this feature effectively:

#### Step 1: Accessing the Inconsistency Report
1. **Navigate to the Inconsistency Report**: Within the SuperDecisions software, you can access the inconsistency report typically from the 'Computations' section or by clicking on a dedicated 'Inconsistency Report' button. This report provides a detailed breakdown of all comparisons made in your model.
   
   ```example
   [9.04s -> 14.72s] We can click inconsistency report. So it will give us the whole list of options to improve inconsistent.
   ```

#### Step 2: Identifying Inconsistent Judgments
2. **Review Inconsistent Entries**: The report lists all entries that exceed a certain inconsistency threshold (commonly 10%). Highlighted cells or specific markers denote these entries, making them easy to spot. For instance, if the inconsistency value for 'Growth versus Location' is 3.0000, it should be brought down to a more acceptable level, ideally below 1.18.

   ```example
   [21.28s -> 29.84s] Growth versus location at this moment, the number is three. But this number should be shown in red colors. It is one over 1.18.
   ```

#### Step 3: Rectifying Identified Inconsistencies
3. **Adjust Judgments**: Once you've identified the inconsistent entries, you can modify the judgments to bring the inconsistency values within acceptable limits. This often involves revisiting the original pairwise comparisons and adjusting the values accordingly.

   - **Example Adjustment**:
     - If the inconsistency is high between 'Prestige' and 'Price', you might need to reassess the importance of each factor and adjust the comparison accordingly.
     
     ```example
     [14.72s -> 21.28s] Let's take the first one. Growth versus location, this number three should be 0.847.
     ```

#### Step 4: Monitoring Consistency Levels
4. **Monitor Changes**: After making adjustments, re-run the inconsistency report to monitor whether the changes have reduced the inconsistency levels. Continue refining judgments until the inconsistency is minimized.

   ```example
   [17.80s -> 19.78s] Now, for price versus miles per gallon, since I'm price sensitive, I'm going to give to price some priority.
   ```

#### Step 5: Synthesizing Final Results
5. **Synthesize Results**: Once all inconsistencies are resolved, you can synthesize the final results to obtain a comprehensive ranking or evaluation of the alternatives based on the corrected judgments.

   ```example
   [24.00s -> 30.00s] Instead of using the per wise comparison, we can synthesize to see our final result.
   ```

### Additional Tips
- **Use Visual Aids**: SuperDecisions often provides visual aids like graphs and charts to help understand the distribution of judgments and identify outliers.
- **Regular Checks**: Regularly run the inconsistency report during the decision-making process to catch inconsistencies early and avoid cumulative errors.
- **Expert Input**: Consult with experts or stakeholders to validate judgments, especially for critical comparisons.

By following these steps and tips, you can effectively use the 'Inconsistency Report' feature in SuperDecisions to ensure that your pairwise comparison judgments are consistent and reliable.
