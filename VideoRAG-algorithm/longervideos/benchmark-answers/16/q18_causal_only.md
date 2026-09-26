Collection: 16
QID: 18
Mode: causal_only
Question: How to define and utilize rating scales in SuperDecisions when implementing a ratings model? 

### Defining and Utilizing Rating Scales in SuperDecisions

#### Step 1: Adding Bottom-Level Criteria
To begin, you need to add bottom-level criteria to your hierarchical tree. These criteria are the factors against which you will evaluate your alternatives. For example, in a car-buying scenario, you might consider criteria such as "Prestige," "Price," "Miles Per Gallon," and "Driving Performance."

**Example:** 
- Add "Prestige" and "Price" as criteria.
- Define "Miles Per Gallon" and "Driving Performance" as bottom-level criteria.

#### Step 2: Adding Alternatives
Once the criteria are set, add the alternatives you wish to evaluate against these criteria. For instance, if you're choosing the best car, you might include models like "Accurate EL," "BMW," and "Audi."

**Example:**
- Add "Accurate EL," "BMW," and "Audi" as alternatives.

#### Step 3: Defining Rating Scales
Next, define rating scales for each criterion. You can either use pre-existing scales or create new ones. Common rating scales include:

- **Intensity Scales**: Use an existing scale or create a new one.
- **High-Medium-Low**: Create a scale with levels such as "Excellent," "Good," "Average," "Below Average," and "Poor."

**Example:**
- For "Prestige," load an existing scale from a file or create a new one.
- For "Price," create a new scale and assign values like "Excellent," "Good," "Average," "Below Average," and "Poor."

#### Step 4: Entering Ratings
After defining the scales, rate each alternative against each criterion using the defined scales. Ensure that the ratings reflect the ideal criteria you have in mind, avoiding direct comparisons between alternatives.

**Example:**
- Rate "Accurate EL" on "Prestige" as "Above Average."
- Rate "BMW" on "Price" as "Excellent."

#### Step 5: Prioritizing Ratings
Once all ratings are entered, prioritize them to compute the weightages for each alternative. This involves sorting the priorities and synthesizing the results.

**Example:**
- Sort the ratings to determine the overall priority for each alternative.
- Synthesize the ratings to get the final priorities and total scores.

#### Step 6: Synthesizing Results
Use the SuperDecisions software to synthesize the ratings and obtain the final priorities for the alternatives. This step helps in identifying the best alternative based on the synthesized data.

**Example:**
- Click on "Synthesize Whole Model" to generate the final priorities and rankings.

#### Step 7: Exporting Data
Finally, you can export the ratings data to an Excel spreadsheet for further analysis using tools like Excel Solver. This allows for more detailed optimization and decision-making processes.

**Example:**
- Copy the ratings data from SuperDecisions to Excel.
- Use Excel Solver to optimize resource allocation based on the ratings.

### Key Features and Tools

- **Graphical Representation**: Use graphical tools to adjust scores visually.
- **Direct Entry Mode**: Input priority values directly into the matrix.
- **Comparative Ratings Table**: Compare scale items pairwise to refine values.
- **Manage Ratings Options**: Clean up the ratings table without affecting the actual model.

### Conclusion
By following these steps, you can effectively define and utilize rating scales in SuperDecisions to implement a ratings model for evaluating alternatives based on specified criteria. This process ensures a systematic and accurate approach to decision-making, providing valuable insights into the best alternatives based on the criteria you have set.
