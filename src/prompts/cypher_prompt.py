from langchain.prompts.prompt import PromptTemplate

def create_prompt():
    CYPHER_GENERATION_TEMPLATE = """Task:Generate Cypher statement to query a graph database.
    Instructions:
    Use only the provided relationship types and properties in the schema.
    Do not use any other relationship types or properties that are not provided.
    Do not include any other knowledge other than what is provided in the user query.
    Schema:
    {schema}
    Note: Do not include any explanations or apologies in your responses.
    Do not respond to any questions that might ask anything else than for you to construct a Cypher statement.
    Do not include any text except the generated Cypher statement.
    If the query requires Graph Data Science (GDS), ensure it uses `CALL gds.<function>` correctly.

    Examples: Here are a few examples of generated Cypher statements for particular questions:
    # Which Microservices has External Dependency?
    MATCH (m:Microservice)-[:DEPENDS_ON]->(e:Microservice {{name: 'ExternalAPI'}})
    RETURN m.name AS Microservice, e.name AS ExternalDependency;

    # I want to fix a bug in CatalogService what are the dependencies of it?
    MATCH (c:Microservice {{name: 'CatalogService'}})-[:DEPENDS_ON]->(d:Microservice)
    RETURN d.name AS DependentMicroservice;

    # What are the most similar Tasks?
    MATCH (t1:Task)-[:LINKED_TO]->(m:Microservice)<-[:LINKED_TO]-(t2:Task)
    WHERE t1 <> t2
    WITH t1, t2, m, apoc.text.sorensenDiceSimilarity(t1.description, t2.description) AS similarity
    RETURN t1.name AS Task1, t2.name AS Task2, m.name AS CommonMicroservice, similarity
    ORDER BY similarity DESC
    LIMIT 10;

    # I noticed a bug in AuthService that has something to do with Node.js, who from the Team should I contact that is familiar with that technology.
    MATCH (m:Microservice {{name: 'AuthService', technology: 'Node.js'}})-[:MAINTAINED_BY]->(t:Team)<-[:PART_OF]-(p:Person)
    RETURN p.name AS TeamMember, t.name AS Team;

    # Which team members are working on RecommendationService?
    MATCH (m:Microservice {{name: 'RecommendationService'}})-[:MAINTAINED_BY]->(t:Team)<-[:PART_OF]-(p:Person)
    RETURN p.name AS TeamMember, t.name AS Team;
    
    The question is:
    {question}"""

    CYPHER_GENERATION_PROMPT = PromptTemplate(
        input_variables=["schema", "question"], template=CYPHER_GENERATION_TEMPLATE
    )
    return CYPHER_GENERATION_PROMPT
