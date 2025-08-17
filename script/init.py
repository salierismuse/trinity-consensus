import os
from dotenv import load_dotenv
from llama_cpp import Llama
os.environ['LLAMA_CPP_VULKAN'] = '1'
os.environ['GGML_VULKAN_DEVICE'] = '0'
from llama_cpp import Llama
from sentence_transformers import SentenceTransformer
sent = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')

TOKENS = 100

#setup
load_dotenv()
db_host = os.getenv("DB_HOST")
MODEL1 = os.getenv("MODEL1")
MODEL2 = os.getenv("MODEL2") 
MODEL3 = os.getenv("MODEL3")
LLAMA_ADDR = os.getenv("LLAMA_ADDR")

SYS_PROMPT1 = os.getenv("SYS_PROMPT1")
SYS_PROMPT2 = os.getenv("SYS_PROMPT2")
SYS_PROMPT3 = os.getenv("SYS_PROMPT3")

DSYS_PROMPT1 = os.getenv("DSYS_PROMPT1")
DSYS_PROMPT2 = os.getenv("DSYS_PROMPT2")
DSYS_PROMPT3 = os.getenv("DSYS_PROMPT3")
CONDITIONAL_AGREEMENT_PROMPT1 = os.getenv("CONDITIONAL_AGREEMENT_PROMPT1")
CONDITIONAL_AGREEMENT_PROMPT2 = os.getenv("CONDITIONAL_AGREEMENT_PROMPT2")
CONDITIONAL_AGREEMENT_PROMPT3 = os.getenv("CONDITIONAL_AGREEMENT_PROMPT3")

models = [MODEL1, MODEL2, MODEL3]

llm1 = Llama(
    model_path=MODEL1,
    n_gpu_layers = 28,  
    verbose=False,
    n_ctx=2048,
)

llm2 = Llama(
    model_path=MODEL2,
    n_gpu_layers=28,  
    verbose=False,
    n_ctx=2048,
)

llm3 = Llama(
    model_path=MODEL3,
    n_gpu_layers=0,  
    verbose=False,
    n_ctx=2048,
)



prompts = {llm1: SYS_PROMPT1, llm2: SYS_PROMPT2, llm3: SYS_PROMPT3}
dprompts = {llm1: DSYS_PROMPT1, llm2: DSYS_PROMPT2, llm3: DSYS_PROMPT3}
conditional_prompts = [CONDITIONAL_AGREEMENT_PROMPT1, CONDITIONAL_AGREEMENT_PROMPT2, CONDITIONAL_AGREEMENT_PROMPT3]
responses = {}
responses[llm1] = []
responses[llm2] = []
responses[llm3] = []
llms = [llm1, llm2, llm3]
decisions = []
ans = []