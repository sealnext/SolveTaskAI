import os

from dotenv import load_dotenv

load_dotenv()


OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
OPENAI_EMBEDDING_MODEL = os.getenv('OPENAI_EMBEDDING_MODEL', 'text-embedding-3-small')
NUMBER_OF_DOCS_TO_RETRIEVE = int(os.getenv('NUMBER_OF_DOCS_TO_RETRIEVE', 5))
