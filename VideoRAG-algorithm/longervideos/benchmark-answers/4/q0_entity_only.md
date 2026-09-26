Collection: 4
QID: 0
Mode: entity_only
Question: Describe the main differences between the two RAG systems mentioned in the video (text-based and vision-based).

### Differences Between Text-Based and Vision-Based RAG Systems

#### Text-Based RAG Systems
Text-based RAG systems primarily rely on textual data to retrieve and generate responses. Here are the key aspects of text-based RAG systems:

1. **Input Handling**: User queries and documents are processed as plain text.
2. **Data Flow**:
   - **User Query**: The user inputs a query in text form.
   - **Processing**: The query is passed through an embedding model, which converts it into a vector representation.
   - **Indexing**: The system uses a vector store to index the textual data.
   - **Retrieval**: Relevant chunks of text are retrieved based on similarity to the query vector.
   - **Response Generation**: The retrieved chunks are combined with the original query and passed to a Large Language Model (LLM) to generate the final response.
   
3. **Challenges**:
   - **Query Formulation**: Poorly formulated queries can lead to inaccurate retrieval and hallucination (making up answers).
   - **Contextual Understanding**: Capturing context across multiple chunks of information can be challenging.
   
4. **Techniques**:
   - **Traditional RAG**: Single-shot retrieval.
   - **Agentic RAG**: Multiple retrieval opportunities to improve efficiency.
   - **Enhancements**: Use of powerful text embedding models and multi-vector indices for better retrieval accuracy.

#### Vision-Based RAG Systems
Vision-based RAG systems incorporate visual data, allowing for the handling of images and documents in their entirety. Below are the main characteristics of vision-based RAG systems:

1. **Input Handling**: Documents are processed as images, and user queries are handled similarly to text-based systems but with an additional layer of visual analysis.
2. **Data Flow**:
   - **Document Conversion**: Documents are converted into images and stored as multi-vector representations.
   - **User Query**: The user inputs a query, which is embedded using the same model used for the document images.
   - **Retrieval**: Relevant pages are retrieved based on the visual information contained in the images.
   - **Response Generation**: The retrieved pages, along with the original user query, are fed to a Vision Language Model (VLM) to generate the final response.
   
3. **Advantages**:
   - **Direct Document Handling**: No need for manual parsing or pre-processing of PDF files.
   - **Enhanced Explainability**: The model can analyze both text and images, providing more detailed information on where the data originates.
   - **Efficiency**: Utilizes advanced OCR (Optical Character Recognition) and document layout analysis to handle complex documents efficiently.
   
4. **Complexity**:
   - **Integration of Visual Data**: Requires robust OCR and image processing techniques to accurately convert and analyze visual data.
   - **Multi-Vector Representation**: Uses multi-vector indices to enhance retrieval accuracy and explainability.
   - **Advanced Models**: Leverages powerful vision language models for efficient and accurate retrieval and response generation.

### Summary
- **Text-Based RAG** systems focus on textual data and rely on powerful text embedding models for retrieval and response generation.
- **Vision-Based RAG** systems extend this capability by incorporating visual data, enabling direct handling of images and documents without manual preprocessing, thus providing enhanced explainability and efficiency.

Both systems aim to improve information retrieval and response generation but differ in their approach to handling input data and leveraging advanced models.
