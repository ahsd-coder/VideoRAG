Collection: 5
QID: 22
Mode: causal_only
Question: Describe the process of using sub-agents and a super agent to analyze financial reports in a PDF format.

### Using Sub-Agents and Super Agent to Analyze Financial Reports in PDF Format

The process of using sub-agents and a super agent to analyze financial reports in PDF format involves several steps, each designed to efficiently extract and process relevant information. Below is a detailed breakdown of the process:

#### Step 1: Define the Super Agent
- **Purpose**: The super agent acts as the orchestrator, managing multiple sub-agents and coordinating their tasks.
- **Tools**: Utilizes a larger model, often referred to as 'Opus', to generate prompts for sub-agents.
- **Example**: The super agent might generate a specific prompt for an LLM sub-agent to extract relevant information from earning reports.

#### Step 2: Set Up Sub-Agents
- **Objective**: Each sub-agent is assigned a specific task, such as extracting financial data from a single quarterly earning report.
- **Configuration**: Sub-agents are configured with instructions tailored to their specific roles.
- **Details**:
  - **Prompt Generation**: The super agent creates detailed instructions for each sub-agent, specifying the exact financial figures to extract (e.g., total net sales).
  - **Execution**: Each sub-agent runs independently, accessing only one quarterly earning report PDF file at a time.
  - **Output**: Sub-agents output only the extracted information, without additional content.

#### Step 3: Define Functions for Processing PDFs
- **Tool Usage**: The process leverages Python scripts and libraries like `pdfminer`, `PIL`, and `requests` to handle PDF files.
- **Process**:
  - Convert PDF pages into base64-encoded PNG images.
  - Use smaller models (e.g., Haiku models) to extract specific information from these images.
  - Format the extracted data into structured XML tags for clarity and separation of information.

#### Step 4: Parallel Execution
- **Efficiency**: To handle multiple PDF files simultaneously, the system executes code in parallel.
- **Implementation**:
  - Run multiple instances of the sub-agents concurrently, each processing a different quarterly report.
  - Make four different calls to the Haiku API endpoint to process the PDFs.

#### Step 5: Collect and Aggregate Data
- **Collection**: Gather the extracted information from all sub-agents.
- **Aggregation**: Combine the data into a comprehensive report using a larger model (e.g., Opus) to generate a final response.
- **Final Output**: Provide a detailed analysis based on the combined data, addressing the initial user question.

#### Example Workflow
1. **Input Prompt**: The user inputs a question, such as "What is the net sales change in Apple's quarter-to-quarter comparison in 2023?"
2. **Super Agent Action**: The super agent generates a prompt for an LLM sub-agent, specifying to extract net sales figures from Apple's earning reports.
3. **Sub-Agent Execution**: Multiple sub-agents process different quarterly earning reports, each focusing on one report at a time.
4. **Parallel Processing**: Each sub-agent converts PDF pages to images and extracts net sales figures using Haiku models.
5. **Data Collection**: All extracted net sales figures are collected and aggregated.
6. **Final Analysis**: The super agent generates a final report summarizing the net sales changes across quarters.

### Conclusion
By leveraging sub-agents and a super agent, the system can efficiently and accurately analyze financial reports from PDF files. This approach ensures that each task is handled by a dedicated sub-agent, optimizing resource utilization and enhancing the overall processing speed and accuracy.
