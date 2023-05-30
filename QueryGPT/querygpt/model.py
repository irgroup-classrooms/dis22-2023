import json
from dataclasses import dataclass
from pathlib import Path
import re
from copy import deepcopy

@dataclass
class DatasetEntry:
    """Dataclass for dataset Entry"""
    topic: str
    query: str
    persona_name: str
    keywords: str
    questions: str
    result_queries: str

    @staticmethod
    def from_json(line: str):
        jsonl = json.loads(line)
        return DatasetEntry(jsonl["topic"], jsonl["query"], jsonl["persona"], jsonl["result"]["keywords"], jsonl["result"]["questions"], jsonl["result"]["queries"])

    def extract_answers(self):
        ds_dict = deepcopy(self.__dict__)
        del ds_dict["query"]
        del ds_dict["keywords"]
        del ds_dict["questions"]
        answer = [
                    {
                        "topic": ds_dict["topic"],
                        "query_id": result,
                        "query": ds_dict["result_queries"][result],
                        "persona": ds_dict["persona_name"], 
                    }
                    for result in ds_dict["result_queries"]]
        return answer
    

@dataclass
class Persona:
    """Dataclass for a persona"""
    name: str
    age: int = None
    gender: str = None
    profession: str = None
    goal: str = None
    residence: str = None
    query_length: int = None
    complexity: str = None

    @staticmethod
    def from_json(fn: str):
        """Load a persona from a JSON file"""
        return Persona(**json.load(open(fn)))
    
    @staticmethod
    def from_register(name: str):
        """Load a persona from the register"""
        fn = Path(__file__).parent / Path("personas") / Path(name + ".json")
        return Persona.from_json(fn)

    @staticmethod
    def list_register():
        """List all saved Personas"""
        dir_ = Path(__file__).parent / Path("personas")
        personas = [file.stem for file in dir_.iterdir()]
        return personas

    def to_json(self, fn: str):
        """Save a persona to a JSON file"""
        json.dump(self.__dict__, open(fn, 'w'))


class Query():
    """Class for a query"""
    def __init__(self):
        self.query_type = None
        self.persona = None
        self.query_folder = None
        self._queries = {}
        self.query = None
        self.openai_key = None

        self._load_queries()

    def _load_queries(self):
        """Create dict QueryType from all files listes in queries/"""
        queries_folder = Path(__file__).parent / "queries"
        for q in queries_folder .iterdir():
            self.add_queries(q.stem, self._load_querie(q))


    def add_queries(self, query_type: str, query: str):
        """Add custom query to Query class. Queries are just normal strings with placeholders for the persona attributes.
        placehpolders are of the form $PERSONA_ATTRIBUTE_LIKE_THIS. A simple example would be: 
        
        "Provide me with example queries in the length of $PERSONA_QUERY_LENGTH words for a Persona named $PERSONA_NAME that is $PERSONA_AGE years old."
        
        Args:
            query_type (str): Type of query
            query (str): Query as a string

        """
        self._queries[query_type] = query

    def list_query_types(self):
        """List all query types

        Returns:
            _type_: _description_
        """
        return self._queries.keys()

    def _load_querie(self, query_fn: str):
        """load a query from a file"""
        return open(query_fn).read()

    def add_custom_query_from_file(self, query_fn: str, query_type: str = None) -> None:
        """Add a custom query from a file

        Args: 
            query_fn (str): Path to query file
            query_type (str): Type of query (default: filename)
        
        Returns:
            None
        
        """

        if query_type is None:
            query_type = Path(query_fn).stem

        self.add_queries(query_type, self._load_querie(query_fn))


    def add_custom_query_from_folder(self, query_folder) -> None:
        """
        Summary: Loads queries from a folder

        Args:
            query_folder (str): Path to folder containing queries
        
        Returns:
            None
        """

        for q in Path(query_folder):
            self.add_custom_query_from_file(q)


    def select_querie_type(self, query_type: str) -> None:
        """Select a query type

        Args:
            query_type (str): Type of query
        
        Returns:
            None
        """

        if query_type not in self._queries.keys():
            raise ValueError(f"Query type {query_type} not found. Available query types: {self.list_query_types()}")

        self.query_type = query_type
        print(f"Selected query type: {query_type}")


    def select_persona(self, persona: Persona) -> None:
        """Select a persona

        Args:
            persona (Persona): Persona
        
        Returns:
            None
        """

        if not isinstance(persona, Persona):
            raise ValueError(f"Expected Persona, got {type(persona)}")

        self.persona = persona
        print(f"Selected persona: {persona.name}")


    def try_query_mappings(self) -> str:
        """Map query parameters to persona

        Args:
            query (str): Query
            persona (Persona): Persona
        
        Returns:
            str: Query with mapped persona attributes
        """

        if not self.query_type:
            raise ValueError("No query type selected. Please select a query type.")
        
        if not self.persona:
            raise ValueError("No persona selected. Please select a persona.")

        persona_mappings = []
        query = self._queries[self.query_type]
        query_changed = query
        for attr in self.persona.__dict__.keys():
            if self.persona.__dict__[attr] is None:
                print(f"Attribute {attr} not replaced because its value is None. Please use .manual_replace(parameter, attribute) to supply it.")
                continue
            query = query.replace(f"$PERSONA_{attr.upper()}", str(self.persona.__dict__[attr]))
            if query == query_changed:
                print(f"$PERSONA_{attr.upper()} not found in query. Skipping attribute.")

            query_changed = query


        self.query = query

        regex = re.compile(r"\$[A-Z_]+\b")
        not_found = [attr for attr in regex.findall(query)]
        
        print(f"Unused parameters in query: {not_found} Please use .manual_replace(parameter, attribute) to supply them.")

        # print(f"Query mappings: {query_mappings}")
        # print(f"Persona mappings: {persona_mappings}")
        

    def manual_replace(self, param, attr):
        """Manually replace a parameter inside the query with an attribute

        Args:
            param (_type_): _description_
            attr (_type_): _description_
        """
        self.query = self.query.replace(param, attr)


    def generate_query(self, title: str, narr: str=None, desc: str=None, n_queries:int=5) -> str:
        """Generate a query

        Args:
            topic (str): Topic of query
            narrative (str): Narrative of query
            description (str): Description of query
        
        Returns:
            str: Generated query
        """

        if not self.query:
            raise ValueError("No query selected. Please select a query.")

        if not title:
            raise ValueError("No title selected. Please select a title.")

        query = self.query + f"\nPlease generate {n_queries} search queries that could have been written by {self.persona.name} to do research on the following.\nTopic: {title}."

        if narr:
            query += f"\nNarrative: {narr}"


        if desc:
            query += f"\nDescription: {desc}"

        return query
