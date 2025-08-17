from models_functions import *

def check_similarity(decisions):
    embeddings = sent.encode(decisions)
    for i in decisions:
        print(i) 
    print(embeddings.shape)
    similarities = sent.similarity(embeddings, embeddings)
    print(similarities)
    count = 0
    count2 = 0
    cond_model = None
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
    return count, cond_model

def intermediary_rounds(llm1, llm2, llm3, question):
    global decisions
    orig_response1 = responses[llms[0]][-1]
    orig_response2 = responses[llms[1]][-1]
    orig_response3 = responses[llms[2]][-1]
    

    ask_model_deliberation(llm1, orig_response1, orig_response2, orig_response3, 100, question, decisions[0], decisions[1], decisions[2])
    ask_model_deliberation(llm2, orig_response1, orig_response2, orig_response3, 100, question, decisions[0], decisions[1], decisions[2])
    ask_model_deliberation(llm3, orig_response1, orig_response2, orig_response3, 100, question, decisions[0], decisions[1], decisions[2])

    decisions = []
    for i in range(3):
        response = responses[llms[i]][-1]
        first_line = response.split('\n')[0].strip().lower()
        decisions.append(first_line)
        print(response)
        print("------")
    print("\n")
    count, cond_model = check_similarity(decisions)
    if count == 0:
        print("TOTAL AGREEMENT")
        print(final_decision(llm1, llm2, llm3, responses[llms[0]][-1], responses[llms[1]][-1], responses[llms[2]][-1], 150, question))
        return True
    if count == 1:
        print("PARTIAL DISAGREEMENT")
        final_round(llm1, llm2, llm3, question)
        print(final_decision(llm1, llm2, llm3, responses[llms[0]][-1], responses[llms[1]][-1], responses[llms[2]][-1], 150, question))
        return False
    if count > 1:
        print("DISAGREEMENT")
        final_round(llm1, llm2, llm3, question)
        return False
    
def round1(llm1, llm2, llm3, question):
    global decisions
    ask_models(llms, question, TOKENS)
    count = 0
    for i in range(3):
        response = responses[llms[i]][0]
        first_line = response.split('\n')[0].strip().lower()
        decisions.append(first_line)
        print(response)
        print("------")
    print("---------")
    count, cond_model = check_similarity(decisions)
    if count == 0:
        print("TOTAL AGREEMENT")
        print(final_decision(llm1, llm2, llm3, responses[llms[0]][-1], responses[llms[1]][-1], responses[llms[2]][-1], 150, question))
        return decisions
    if count == 1:
        print("PARTIAL DISAGREEMENT")
        print("-------------------")
        return intermediary_rounds(llm1, llm2, llm3, question)
    if count > 1:
        print("DISAGREEMENT")
        print("-------------------")
        return intermediary_rounds(llm1, llm2, llm3, question)

def reset_to_base():
    global decisions, ans
    responses[llm1] = []
    responses[llm2] = []
    responses[llm3] = []
    decisions = []
    ans = []

def final_round(llm1, llm2, llm3, question):
    global decisions
    orig_response1 = responses[llms[0]][-1]
    orig_response2 = responses[llms[1]][-1]
    orig_response3 = responses[llms[2]][-1]

    ask_model_deliberation(llm1, orig_response1, orig_response2, orig_response3, 100, question, decisions[0], decisions[1], decisions[2])
    ask_model_deliberation(llm2, orig_response1, orig_response2, orig_response3, 100, question, decisions[0], decisions[1], decisions[2])
    ask_model_deliberation(llm3, orig_response1, orig_response2, orig_response3, 100, question, decisions[0], decisions[1], decisions[2])
    decisions = []
    for i in range(3):
        response = responses[llms[i]][-1]
        first_line = response.split('\n')[0].strip().lower()
        decisions.append(first_line)
        print(response)
        print("------")
    print("\n")
    count, cond_model = check_similarity(decisions)
    
    if count == 0:
        print("TOTAL AGREEMENT")
        print("----------FINAL DECISION--------")
        print(final_decision(llm1, llm2, llm3, responses[llms[0]][-1], responses[llms[1]][-1], responses[llms[2]][-1], 150, question))
        return True
    if count == 1:
        print("PARTIAL DISAGREEMENT")
        condition = conditional_check(llms[cond_model], responses[llms[0]][-1], responses[llms[1]][-1], responses[llms[2]][-1], 100, question, cond_model)
        print("------FINALDECISION--------")
        print(final_decision(llm1, llm2, llm3, responses[llms[0]][-1], responses[llms[1]][-1], responses[llms[2]][-1], 150, question))
        if "AGREEMENT IMPOSSIBLE" in condition:
            print(cond_model + " cannot agree under any cirumstance.")
        elif "TOTAL AGREEMENT" not in condition:
            print(cond_model + "'S CONDITION: " + condition)
        
        return False
    if count > 1:
        print("DISAGREEMENT")
        return False

