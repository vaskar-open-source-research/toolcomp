import argparse
import json
import os
import numpy as np
from openai import OpenAI
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from utils.keystore import auth_litellm, get_any_from_env
import jsonlines
import pandas as pd


USER_PROMPT = """
Question: {question}
Correct Answer: {correct_answer}
Student Answer: {student_answer}""".strip()

SYSTEM_PROMPT = """
You are an expert test grader evaluating student responses. You'll compare each student answer to the correct answer based on specific criteria, considering both content accuracy and formatting.

Evaluation Process
For each submission, you will receive:

Question: The original problem
Correct Answer: The expected response (a list of strings/values)
Student Answer: The response to evaluate

You will need to evaluate the student answer based on the following criteria and assign a grade of CORRECT, CORRECT BUT BAD FORMATTING, or INCORRECT:

CORRECT

 - Content matches the correct answer
 - Format matches the correct answer
 - Numerical values are within 10% of the correct answer
 - Lists contain the same elements in the same order (if special sorting is requested)
 - Strings contain equivalent information

CORRECT BUT BAD FORMATTING

 - Content matches the correct answer but format differs
 - Contains natural language or additional text
 - Numbers are within 10% but differently formatted
 - Lists contain the same elements but are wrapped differently
 - Strings contain equivalent information but are formatted differently
 - Additional information is acceptable if the correct answer is included

INCORRECT

 - Content differs significantly from the correct answer
 - Numbers differ by more than 10%
 - Strings contain different or incorrect information

Examples

Example 1: Basic Evaluation
Question: Find the name of the city known for its famous tourist attraction Alcatraz, also give its current temperature and a list of names of all the NBA teams whose home stadium is within a 400 mile radius
Correct Answer: ['San Francisco', 78, ['Golden State Warriors', 'Los Angeles Lakers']]
Student Answer: ['San Francisco', 74, ['Los Angeles Lakers', 'Golden State Warriors']]
Reasoning: The Student Answer is correct because it identifies the same city, the temperature is within 10% of the Correct Answer, and the same team names are present in the list.
Final Grade: CORRECT

Example 2: Formatting Issues
Question: Find the name of the city known for its famous tourist attraction Alcatraz, also give its current temperature and a list of names of all the NBA teams whose home stadium is within a 400 mile radius
Correct Answer: ['San Francisco', 78, ['Golden State Warriors', 'Los Angeles Lakers']]
Student Answer: The city name is San Francisco, its temperature is 80 degrees and the Los Angeles Lakers and the Golden State Warriors are two NBA teams whose home stadium is within a 400 mile radius
Reasoning: Although the Student Answer is correct (identifies the same city, the temperature is within 10% of the Correct Answer, and the same team names are present), it's not formatted properly and contains extra text and natural language.
Final Grade: CORRECT BUT BAD FORMATTING

Example 3: Incorrect Content
Question: Find the name of the city known for its famous tourist attraction Alcatraz, also give its current temperature and a list of names of all the NBA teams whose home stadium is within a 400 mile radius
Correct Answer: ['San Francisco', 78, ['Golden State Warriors', 'Los Angeles Lakers']]
Student Answer: ['San Francisco', -15, ['Los Angeles Lakers', 'Golden State Warriors']]
Reasoning: The Student Answer is incorrect because although it identifies the same city and the same team names are present in the list, the temperature is well outside of 10% of the Correct Answer.
Final Grade: INCORRECT

Example 4: Specific Ordering Requirements
Question: Find the name of the city known for its famous tourist attraction Alcatraz, also give its current temperature and a list of names of all the NBA teams whose home stadium is within a 400 mile radius in alphabetical order
Correct Answer: ['San Francisco', 78, ['Golden State Warriors', 'Los Angeles Lakers']]
Student Answer: ['SF', 75, ['Golden State Warriors', 'Los Angeles Lakers']]
Reasoning: The Student Answer is correct because it identifies the same city (SF is a commonly known short form for San Francisco), the temperature is within 10% of the Correct Answer, and the same team names are present in the list and sorted as specified in the question.
Final Grade: CORRECT

Example 5: Format Issues with Correct Ordering
Question: Find the name of the city known for its famous tourist attraction Alcatraz, also give its current temperature and a list of names of all the NBA teams whose home stadium is within a 400 mile radius in alphabetical order
Correct Answer: ['San Francisco', 78, ['Golden State Warriors', 'Los Angeles Lakers']]
Student Answer: The city name is San Francisco, its temperature is 80 degrees and the Golden State Warriors and the Los Angeles Lakers are two NBA teams whose home stadium is within a 400 mile radius (in alphabetical order)
Reasoning: Although the Student Answer is correct (identifies the same city, the temperature is within 10% of the Correct Answer, and the same team names are present in the same order), it's not formatted properly and contains extra text and natural language.
Final Grade: CORRECT BUT BAD FORMATTING

Example 6: Incorrect Order
Question: Find the name of the city known for its famous tourist attraction Alcatraz, also give its current temperature and a list of names of all the NBA teams whose home stadium is within a 400 mile radius in alphabetical order
Correct Answer: ['San Francisco', 78, ['Golden State Warriors', 'Los Angeles Lakers']]
Student Answer: ['San Francisco', 79, ['Los Angeles Lakers', 'Golden State Warriors']]
Reasoning: The Student Answer is correct but bad formatting because although it identifies the same city and the temperature is within 10% of the Correct Answer, the list of team names is in a different order when the question explicitly asks for a specific sorting.
Final Grade: CORRECT BUT BAD FORMATTING

Grading Format
Your output must follow the following format:

Reasoning: <detailed explanation of your evaluation>
Final Grade: <INCORRECT/CORRECT BUT BAD FORMATTING/CORRECT>[ENDOFGRADE]

Important Note
Your role is solely to compare the student answer to the provided correct answer. Do not attempt to determine the correct answer yourself.""".strip()


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
    
def complete(input, client):
    max_tries = 3
    while max_tries > 0:
        try:
            response = client.chat.completions.create(
                model="openai/o1",
                messages=input[1],
                stop=["[ENDOFGRADE]"],
            )
            return input[0], response.choices[0].message.content
        except Exception as e:
            print(e)
            error=str(e)
            max_tries -= 1
    return input[0], error

def extract_student_answer(response):
    """Extract the student answer of the form ```json\n{\"final_answer\": student_answer}\n``` from the response"""
    if response is None:
        return ""
    
    if isinstance(response, list) or isinstance(response, int) or isinstance(response, float) or isinstance(response, dict):
        response = str(response)
        return response

    response = response.strip()
    # check if the response starts with ```json\n
    if not response.startswith('```json') or not response.endswith('```'):
        return response
    # extract the student answer
    sub_str = response[len('```json'):-len('```')].strip()

    try:
        return sub_str[len('{"final_answer":'):-len('}')].strip()
    except Exception as e:
        print(f"Error extracting student answer: {response}, {sub_str}")
        return response

def grade(args):

    api_key, base_url = auth_litellm()
    client = OpenAI(api_key=api_key, base_url=base_url)
    data = json.load(open(args.input_file, "r"))
    all_prompts = []

    for i, entry in enumerate(data):
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT}, 
            {"role": "user", "content": USER_PROMPT.format(question=entry['prompt'], correct_answer=entry['answer'], student_answer=extract_student_answer(entry['policy_answer']))}, 
            {"role": "assistant", "content": "Reasoning: "}
        ]
        all_prompts.append((i, messages))
    
       
    with tqdm(total=len(all_prompts)) as pbar:
        with ThreadPoolExecutor(max_workers=args.num_workers) as executor:
            futures = [executor.submit(complete, input, client) for input in all_prompts]
            for future in as_completed(futures):
                i, response = future.result()
                data[i]['gpt_grader_out'] = response
                data[i]['gpt_grader_reasoning'] = response.split('Reasoning: ')[-1].split('Final Grade: ')[0].strip()
                data[i]['gpt_grader_grade'] = response.split('Final Grade: ')[-1].strip()
                pbar.update(1)

    chat_data = [entry for entry in data if len(entry['tools']) == 2]
    enterprise_data = [entry for entry in data if len(entry['tools']) > 2]

    chat_metrics = {
        'correct': sum([entry['gpt_grader_grade'] == 'CORRECT' for entry in chat_data]),
        'correct_but_bad_formatting': sum([entry['gpt_grader_grade'] == 'CORRECT BUT BAD FORMATTING' for entry in chat_data]),
        'incorrect': sum([entry['gpt_grader_grade'] == 'INCORRECT' for entry in chat_data]),
        'accuracy': sum([entry['gpt_grader_grade'] == 'CORRECT' or entry['gpt_grader_grade'] == 'CORRECT BUT BAD FORMATTING' for entry in chat_data]) / len(chat_data) if len(chat_data) > 0 else 0,
    }

    chat_metrics['ci'] = 1.96 * np.sqrt(chat_metrics['accuracy'] * (1 - chat_metrics['accuracy']) / len(chat_data)) if len(chat_data) > 0 else 0

    enterprise_metrics = {
        'correct': sum([entry['gpt_grader_grade'] == 'CORRECT' for entry in enterprise_data]),
        'correct_but_bad_formatting': sum([entry['gpt_grader_grade'] == 'CORRECT BUT BAD FORMATTING' for entry in enterprise_data]),
        'incorrect': sum([entry['gpt_grader_grade'] == 'INCORRECT' for entry in enterprise_data]),
        'accuracy': sum([entry['gpt_grader_grade'] == 'CORRECT' or entry['gpt_grader_grade'] == 'CORRECT BUT BAD FORMATTING' for entry in enterprise_data]) / len(enterprise_data) if len(enterprise_data) > 0 else 0,
    }

    enterprise_metrics['ci'] = 1.96 * np.sqrt(enterprise_metrics['accuracy'] * (1 - enterprise_metrics['accuracy']) / len(enterprise_data)) if len(enterprise_data) > 0 else 0
    

    with jsonlines.open(os.path.join(args.output_dir, 'llm_grader_chat_output.jsonl'), 'w') as writer:
        writer.write_all(chat_data)

    with jsonlines.open(os.path.join(args.output_dir, 'llm_grader_enterprise_output.jsonl'), 'w') as writer:
        writer.write_all(enterprise_data)

    # save csv to export to sheet
    full_data = chat_data + enterprise_data
    full_df = pd.DataFrame(full_data)
    full_df.to_csv(os.path.join(args.output_dir, 'full_output.csv'), index=False)

    with open(os.path.join(args.output_dir, 'llm_grader_metrics.json'), 'w') as f:
        json.dump({'chat': chat_metrics, 'enterprise': enterprise_metrics}, f)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_file", type=str, required=True)
    parser.add_argument("--output_dir", type=str, required=True)
    parser.add_argument("--num_workers", type=int, default=30)
    args = parser.parse_args()
    grade(args)