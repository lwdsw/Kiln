# The contents of this file are adapted from the promptwrite library (https://github.com/StacklokLabs/promptwright),
# which was adapted from the pluto library (https://github.com/redotvideo/pluto).
# These libraries are licensed under the Apache License 2.0. Any modifications
# are licensed under the kiln AI Core license (MIT at time of writing). See /libs/core/LICENSE.txt for details.


TREE_GENERATION_PROMPT = """I want to train a large language model and I am using another, bigger large language model to generate training data for this. However, if we always ask the bigger model to generate training data with the same prompt, it will end up generating very repetitive training samples. Therefore, we will slightly modify our prompt for each sampling procedure according to some aspects. For instance, when asking the model to generate news articles, we could modify the prompt to let the model tell news articles about particular topics, such as business or politics. To further generate training data, we will do this recursively, and generate submodifications to the prompt. For instance, within the domain of business, we could adapt the prompt to generate news about the stock market or business scandals, and within politics, we could ask the model to generate articles for subtopics like elections or climate policy. We do this recursively, and therefore, we get a tree-like structure of topics.
Your job is the following: I will give you a path of nodes down the topic tree - you should then come up with a list of new subtopics for this given node and return it as a python list. Here are a few examples of what your outputs should look like, related to the news example I just gave you:

Example 1:
node path: "News Topics" -> "Sports" -> "Football"
desired number of subtopics: 5
subtopics: ["college football", "football stadiums", "health consequences football", "Seattle Seahawks", "football sponsorships"]

Example 2:
node path: "News Topics" -> "Entertainment" -> "Movies" -> "Star Portraits"
desired number of subtopics: 8
subtopics: ["Tom Hanks", "Meryl Streep", "Leonardo DiCaprio", "Jennifer Lawrence", "Denzel Washington", "Charlize Theron", "Robert Downey Jr.", "Emma Stone"]


Here are three new examples, this time for generating smalltalk topics for a friendly chat assistant:

Example 1:
node path: "Small Talk Topics"
desired number of subtopics: 7
subtopics: ["weather", "weekend plans", "hobbies", "family", "books", "food", "music"]

Example 2:
node path: y
desired number of subtopics: 5
subtopics: ["parents", "grandparents", "siblings", "family traditions", "family vacations"]

Example 3:
node path: "Small Talk Topics" -> "Hobbies" -> "Cooking"
desired number of subtopics: 6
subtopics: ["recipes", "asian food", "favourite dishes", "cookbooks", "kitchen gadgets", "vegan cooking"]


The system prompt for the model we want to train will be provided to you in a user message as system_prompt.

The node path will be provided to you in a user message as node_path. It will be formated as a list of strings from most general to most specific. For example, the node_path for Example 3 above would be ["Small Talk Topics", "Hobbies", "Cooking"]. If empty, the node path is the root node.

The user message will also contain the desired number of subtopics for this node as num_subtopics. Return exactly this number of subtopics.

The user message may optionally contain human_guidance, which is a string that contains additional instructions for how to generate the subtopics.

When generating subtopics, remain somewhat vague. Things can only be tangentially related and they don't have to be interpreted in a single way. Importantly, make sure that the subtopics fit the system prompt.
"""


SAMPLE_GENERATION_PROMPT = """I want to train a large language model and you should help me generate training data for it. 

In the user message we'll provide the following:
 - The system prompt as system_prompt
 - A potential topic to generate samples for. This will be a list of strings from most general to most specific. For example, the topic ["Small Talk Topics", "Hobbies", "Cooking"] would represent the topic "Cooking" in the "Hobbies" category of "Small Talk Topics". The list may be empty, in which case you should generate samples using the system prompt alone.
 - The number of samples to generate as num_samples. If greater than 1, generate a range of samples that are diverse and relevant to the system prompt, and the topic if provided.

The output must be formatted:
 - in the provided structured format, as an object with a single property "generated_samples" that maps to a list of generated samples.
 - With the correct number of samples (num_samples).
 - Do not include any other text or break the schema in any way.
"""
