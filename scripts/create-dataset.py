from querygpt.model import Query, Persona
import openai
import json
from pathlib import Path
from tqdm.contrib.concurrent import process_map
from functools import partial


def create_dataset_line(nist, persona_name, result_file="dataset.jsonl"):
    topic, query = nist
    content_dict  = send_query(query)
    save_result(result_file, (topic, query, content_dict, persona_name))


def send_query(query):
    
    content_dict = None
    
    while content_dict is None:
        try:
            completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": query}
            ],
            temperature=0.2
            )
            content = completion.choices[0].message["content"]
        
            try:
                content_dict = eval(content)
                return content_dict
            except:
                print("Message not valid json:\n", content)
                pass

        except openai.error.RateLimitError:
            pass

    return None


def save_result(file, result: tuple[str, str, str, str]):
    topic, query, queries, persona = result
    result_dict = {"topic": topic, "query": query, "result": queries, "persona": persona}
    result_json = json.dumps(result_dict)
    with open(file, "a") as f:
        f.write(result_json + "\n")


if __name__ == '__main__':
    openai.api_key = "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"

    core_nist = json.load(open("../notebooks/core_nist.json", "r"))[1:]
    
    
    for pers in Persona.list_register():
        persona = Persona.from_register(pers)
        query = Query()
        query.select_querie_type("QUERY_NO_EXAMPLE")
        query.select_persona(persona)
        query.try_query_mappings()
        queries = [
            (
                nist["title"],
                query.generate_query(title=nist["title"],
                                        desc=nist["desc"],
                                        n_queries=5)
                                        )
                                        for nist in core_nist]
        
        partial_create_ds_line = partial(create_dataset_line, persona_name=persona.name, result_file="dataset.jsonl")
        process_map(partial_create_ds_line, queries, max_workers=10)