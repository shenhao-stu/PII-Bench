"""
Official evaluation prompts for PII-Bench (ACL 2026, Appendix F.6).
Preserved verbatim from the paper's experimental setup for exact reproducibility.
"""

PII_DEFINITION = """1. PER | Names of people, including nicknames/aliases, usernames and initials.
2. CODE | Numbers and codes that identify something, such as SSN, phone number, passport number, license plate.
3. LOC | Places and locations, such as: cities, areas, countries, etc. or named infrastructures (bus stops, bridges, etc.)
4. ORG | Names of organisations, such as public and private companies schools, universities, public institutions, prisons, healthcare institutions non-governmental organisations, churches, etc.
5. DEM | Demographic attribute of a person, such as native language, descent, heritage, ethnicity, job titles, ranks, education, physical descriptions, diagnosis, birthmarks, ages.
6. DATETIME | Description of a specific date (e.g., October 3, 2018), time (e.g., 9:48 AM) or duration (e.g., 18 years).
7. QUANTITY | Description of a meaningful quantity, e.g., percentages and/or monetary values.
"""

SINGLE_RECOGNITION_PROMPT = """Please identify the PII entities and their corresponding PII types in the given user background description.
The PII types are defined as follows:
{pii_definition}
PII types include: ["PER","CODE","LOC","ORG","DEM","DATETIME","QUANTITY"]
## Given user background description: 
{user_desc}

Note: No need to identify interpersonal relationships and their corresponding entity relationships.

Please output the identified content in the following format. Output "Subject {{1}}" followed by a JSON string containing the PII entities and their types. The JSON string should have PII entities as keys and their types as values, both as strings.
The output format is:
Subject {{1}}  {{"ent1": "type1", "ent2": "type2", ...}}
"""

MULTI_RECOGNITION_PROMPT = """Please identify the PII entities and their corresponding PII types for each subject in the given user background description. 
The PII types are defined as follows:
{pii_definition}
PII types include: ["PER","CODE","LOC","ORG","DEM","DATETIME","QUANTITY"]
## Given user background description: 
{user_desc}

Note: No need to identify interpersonal relationships and their corresponding entity relationships.

Please output the identified content in the following format. For each subject, output "Subject {{1}}" or "Subject {{2}}" followed by a JSON string containing the PII entities and their types. The JSON string should have PII entities as keys and their types as values, both as strings.
The output format is:
Subject {{1}} {{"ent1": "type1", "ent2": "type2", ...}}
Subject {{2}} {{"ent1": "type1", "ent2": "type2", ...}}
"""

COMPLEX_RECOGNITION_PROMPT = """Please identify the PII entities and their corresponding PII types for each distinct individual mentioned in the conversation transcript, including both speakers and referenced individuals. 
The PII types are defined as follows:
{pii_definition}
PII types include: ["PER","CODE","LOC","ORG","DEM","DATETIME","QUANTITY"]

## Task Description:
Your task is to:
1. Identify ALL distinct individuals mentioned in the text, including:
   - Primary speakers (marked with [PER_X])
   - Individuals mentioned within others' statements
   - Referenced colleagues, family members, or associates

2. For each identified individual, extract their associated PII entities, ensuring:
   - Each entity is in its smallest viable text span
   - Entities are correctly categorized by type
   - Cross-referenced information is attributed to the correct individual

## Important Rules:
1. Treat each individual as a separate subject, even if mentioned within another person's statement
2. Include both explicitly named individuals and those referenced through relationships
3. Maintain clear boundaries between different individuals' information
4. Extract exact entity spans without additional context
5. Preserve special characters in codes and quantities
6. Handle both direct mentions and indirect references

## Given conversation transcript:
{user_desc}

## Required Output Format:
For each identified individual (both speakers and mentioned persons), output:
Subject {{N}} {{"ent1": "type1", "ent2": "type2", ...}}

## Example:
Input text: "[PER_1]: I'm Alex, working at Google. My friend Bob, who is 25 years old, works at Apple."
Expected output:
Subject {{1}} {{"Alex": "PER", "Google": "ORG"}}
Subject {{2}} {{"Bob": "PER", "25 years": "DATETIME", "Apple": "ORG"}}

Begin analysis now:"""

MULTI_QUERY_UNDERSTANDING_PROMPT = """Please identify highly relevant PII (Personally Identifiable Information) entities from the background description PII entities that directly address or relate to the user's query.

Rules:
- Extract entities in their smallest possible span
- Exclude all person names
- Focus only on entities crucial for answering the query
- Return entities exactly as they appear in the text

### Background description:
{desc}

### Query:
{query}

Your output will contain the following format:
### Answer: List the relevant PII entities. Return only the list without explanation. Example: ["key_pii_1", ..., "key_pii_n"]

Please have your prompt follow the format below: (if there is only one entity, please output ["key_pii_1"]):
### Answer: ["key_pii_1", ..., "key_pii_n"]
"""

MULTI_QUERY_UNDERSTANDING_PROMPT_CHOICE = """From the following options, Please identify highly relevant PII (Personally Identifiable Information) entities from the background description PII entities that directly address or relate to the user's query.

Rules:
- Extract entities in their smallest possible span
- Exclude all person names
- Focus only on entities crucial for answering the query
- Return entities exactly as they appear in the text
- Select only from the provided options

## User background description: {desc}
## User query: {query}
## Options: {choices}

Your output will contain the following format:
### Answer: List the relevant PII entities. Return only the list without explanation. Example: ["key_pii_1", ..., "key_pii_n"]

Please have your prompt follow the format below: (if there is only one entity, please output ["key_pii_1"]):
### Answer: ["key_pii_1", ..., "key_pii_n"]
"""

MULTI_QUERY_UNDERSTANDING_PROMPT_COT = """Please identify highly relevant PII (Personally Identifiable Information) entities from the background description PII entities that directly address or relate to the user's query.

Rules:
- Extract entities in their smallest possible span
- Exclude all person names
- Focus only on entities crucial for answering the query
- Return entities exactly as they appear in the text

### Background description:
{desc}

### Query:
{query}

Your output will contain the following format:
### Thought: Explain your reasoning step by step for selecting the relevant PII entities.
### Answer: List the relevant PII entities. Return only the list without explanation. Example: ["key_pii_1", ..., "key_pii_n"]

Please have your prompt follow the format below: (if there is only one entity, please output ["key_pii_1"]):
### Thought: xxx
### Answer: ["key_pii_1", ..., "key_pii_n"]
"""

MULTI_QUERY_UNDERSTANDING_PROMPT_AUTO_COT = """Please identify highly relevant PII (Personally Identifiable Information) entities from the background description that directly address or relate to the user's query.

Rules:
- Extract entities in their smallest possible span
- Exclude all person names
- Focus only on entities crucial for answering the query
- Return entities exactly as they appear in the text

### Background description:
{desc}

### Query:
{query}

You will be given 3 examples to help you understand the task.
Example 1:
## Background: "Hello, I'm Sarah. I work at Microsoft as a junior developer with 2 years of experience. I live in Seattle."
## Query: "What skills should I focus on developing in my early tech career at a leading software company to advance from my entry-level programming role?"
## Answer: ["Microsoft", "junior developer"]

Example 2:
## Background: "Hello, my name is Ozer. I am 23 years old and I hold a Master's degree. I work at TikTok with the employee ID EP001. I am currently based in Japan."
## Query: "How does my educational background influence my ability to contribute to my current workplace's team dynamics?"
## Answer: ["TikTok", "Master's degree"]

Example 3:
## Background: "I graduated from Stanford in 2020 with a Computer Science degree. Currently working at Amazon as an SDE-1 making $120,000 per year."
## Query: "What's the typical career progression and salary growth for someone with my background?"
## Answer: ["Stanford", "Computer Science degree", "Amazon", "SDE-1", "$120,000"]

Your output will contain the following format:
### Thought: Explain your reasoning step by step for selecting the relevant PII entities.
### Answer: List the relevant PII entities. Return only the list without explanation. Example: ["key_pii_1", ..., "key_pii_n"]

Please have your prompt follow the format below: (if there is only one entity, please output ["key_pii_1"]):
### Thought: xxx
### Answer: ["key_pii_1", ..., "key_pii_n"]
"""

MULTI_QUERY_UNDERSTANDING_PROMPT_SELF_CONSISTENCY = """Please identify highly relevant PII (Personally Identifiable Information) entities from the background description that directly address or relate to the user's query.

Rules:
- Extract entities in their smallest possible span
- Exclude all person names
- Focus only on entities crucial for answering the query
- Return entities exactly as they appear in the text

### Background description:
{desc}

### Query:
{query}

Your output will contain the following format:
### Thought: Generate 5 completely different perspectives of your reflections for selecting the relevant PII entities.
### Summary: Output a summary of all your thinking.
### Answer: List the relevant PII entities. Return only the list without explanation. Example: ["key_pii_1", ..., "key_pii_n"]

Please have your prompt follow the format below: (if there is only one entity, please output ["key_pii_1"]):
### Thought:
1. xxxxxx
2. xxxxxx
3. xxxxxx
4. xxxxxx
5. xxxxxx

### Summary:
xxxxx

### Answer: ["key_pii_1", ..., "key_pii_n"]
"""

MULTI_QUERY_UNDERSTANDING_PROMPT_PLAN_SOLVE = """Please identify highly relevant PII (Personally Identifiable Information) entities from the background description that directly address or relate to the user's query.

Rules:
- Extract entities in their smallest possible span
- Exclude all person names
- Focus only on entities crucial for answering the query
- Return entities exactly as they appear in the text

### Background description:
{desc}

### Query:
{query}

Your output will contain the following format:
### Thought: Please start with a general plan for selecting the relevant PII entities, and then think step-by-step how to solve it based on the plan.
### Answer: List the relevant PII entities. Return only the list without explanation. Example: ["key_pii_1", ..., "key_pii_n"]

Please have your prompt follow the format below: (if there is only one entity, please output ["key_pii_1"]):

### Thought: xxx
### Answer: ["key_pii_1", ..., "key_pii_n"]
"""

QUERY_PROMPT_MAP = {
    "naive": MULTI_QUERY_UNDERSTANDING_PROMPT,
    "base": MULTI_QUERY_UNDERSTANDING_PROMPT,
    "choice": MULTI_QUERY_UNDERSTANDING_PROMPT_CHOICE,
    "cot": MULTI_QUERY_UNDERSTANDING_PROMPT_COT,
    "auto_cot": MULTI_QUERY_UNDERSTANDING_PROMPT_AUTO_COT,
    "self_consistency": MULTI_QUERY_UNDERSTANDING_PROMPT_SELF_CONSISTENCY,
    "plan_solve": MULTI_QUERY_UNDERSTANDING_PROMPT_PLAN_SOLVE,
}
