from deliberation import *



def check_similarity(decisions):
    embeddings = sent.encode(decisions)
    for i in decisions:
        print(i) 
    print(embeddings.shape)
    similarities = sent.similarity(embeddings, embeddings)
    print(similarities)
    count = 0
    count2 = 0
    total = 0
    for i in similarities:
        total += 1
        count2 = 0
        for ii in i:
            if ii < .9:
                count2+=1
            if count2 == 2:
                count += 1
                cond_model = total-1
                break
    embeddings = sent.encode(decisions)
    return count

def not_round_one(llm1, llm2, llm3, question):
    ask_model_deliberation(llm1, responses[llms[0]][-1], responses[llms[1]][-1], responses[llms[2]][-1], 150, question)
    ask_model_deliberation(llm2, responses[llms[1]][-1], responses[llms[2]][-1], responses[llms[0]][-1], 150, question)
    ask_model_deliberation(llm3, responses[llms[2]][-1], responses[llms[1]][-1], responses[llms[0]][-1], 150, question)
    for i in range(3):
        response = responses[llms[i]][-1]
        first_line = response.split('\n')[0].strip().lower()
        decisions.append(first_line)
        print(response)
        print("------")
    print("\n")
    count = check_similarity(decisions)
    if count == 0:
        print("TOTAL AGREEMENT")
        return True
    if count == 1:
        print("PARTIAL DISAGREEMENT")
        return False
    if count > 1:
        print("DISAGREEMENT")
        return False
    
def round1(llm1, llm2, llm3, question):
    ask_models(llms, question, TOKENS)
    decisions = []
    count = 0
    for i in range(3):
        response = responses[llms[i]][0]
        first_line = response.split('\n')[0].strip().lower()
        decisions.append(first_line)
        print(response)
        print("------")
    print("---------")
    count = check_similarity(decisions)

    if count == 0:
        print("TOTAL AGREEMENT")
        return True
    if count == 1:
        print("PARTIAL DISAGREEMENT")
        print("-------------------")
        #proceed to deliberation
        not_round_one(llm1, llm2, llm3, question)
        return False
    if count > 1:
        print("DISAGREEMENT")
        print("-------------------")
        not_round_one(llm1, llm2, llm3, question)
        return False

def reset_to_base():
    responses[llm1] = []
    responses[llm2] = []
    responses[llm3] = []
    decisions = []
    ans = []