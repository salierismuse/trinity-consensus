from models_functions import *

# model 3 now judges deterministically on canonical tokens from classify_response(...)

def intermediary_rounds(llm1, llm2, llm3, question):
    global decisions
    orig_response1 = responses[llms[0]][-1]
    orig_response2 = responses[llms[1]][-1]
    orig_response3 = responses[llms[2]][-1]

    ask_model_deliberation(llm1, orig_response1, orig_response2, orig_response3, 100, question, decisions[0], decisions[1], decisions[2])
    ask_model_deliberation(llm2, orig_response1, orig_response2, orig_response3, 100, question, decisions[0], decisions[1], decisions[2])
    ask_model_deliberation(llm3, orig_response1, orig_response2, orig_response3, 100, question, decisions[0], decisions[1], decisions[2])

    decisions = []
    tops = []
    for i in range(3):
        response = responses[llms[i]][-1]
        # classify whole response to a token
        token = classify_response(response)
        tops.append(token)
        decisions.append(token)
        print(response)
        print("------")
    print("\n")

    status, outlier = judge_logical_equivalence_by_model3(llm3, question, tops[0], tops[1], tops[2])

    if status == "total_same":
        print("TOTAL AGREEMENT")
        print(final_decision(llm1, llm2, llm3,
              responses[llms[0]][-1], responses[llms[1]][-1], responses[llms[2]][-1], 150, question))
        return True

    if status == "partial_same":
        print("PARTIAL DISAGREEMENT")
        final_round(llm1, llm2, llm3, question)
        return False

    print("DISAGREEMENT")
    final_round(llm1, llm2, llm3, question)
    return False

def round1(llm1, llm2, llm3, question):
    global decisions
    ask_models(llms, question, TOKENS)

    tops = []
    for i in range(3):
        response = responses[llms[i]][0]
        token = classify_response(response)
        tops.append(token)
        decisions.append(token)
        print(response)
        print("------")
    print("---------")

    status, outlier = judge_logical_equivalence_by_model3(llm3, question, tops[0], tops[1], tops[2])

    if status == "total_same":
        print("TOTAL AGREEMENT")
        print(final_decision(llm1, llm2, llm3,
              responses[llms[0]][-1], responses[llms[1]][-1], responses[llms[2]][-1], 150, question))
        return decisions

    if status == "partial_same":
        print("PARTIAL DISAGREEMENT")
        print("-------------------")
        return intermediary_rounds(llm1, llm2, llm3, question)

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
    tops = []
    for i in range(3):
        response = responses[llms[i]][-1]
        token = classify_response(response)
        tops.append(token)
        decisions.append(token)
        print(response)
        print("------")
    print("\n")

    status, outlier = judge_logical_equivalence_by_model3(llm3, question, tops[0], tops[1], tops[2])

    if status == "total_same":
        print("TOTAL AGREEMENT")
        print("----------FINAL DECISION--------")
        print(final_decision(llm1, llm2, llm3,
              responses[llms[0]][-1], responses[llms[1]][-1], responses[llms[2]][-1], 150, question))
        return True

    if status == "partial_same":
        print("PARTIAL DISAGREEMENT")
        # use explicit outlier if present; else default to model 3 as tiebreaker
        if outlier in (1, 2, 3):
            cond_model = outlier - 1
        else:
            cond_model = 2  # model 3 index

        condition = conditional_check(llms[cond_model],
                                      responses[llms[0]][-1],
                                      responses[llms[1]][-1],
                                      responses[llms[2]][-1],
                                      100, question, cond_model)

        print("------FINALDECISION--------")
        # collect the two non-outlier responses by index
        resp = []
        for i, m in enumerate(llms):
            if i != cond_model:
                resp.append(responses[m][-1])

        if "AGREEMENT IMPOSSIBLE" in condition or "AGREEMENT_IMPOSSIBLE" in condition:
            print(final_decision_two(llm1, llm2, resp[0], resp[1], 150, question))
            print(models[cond_model] + "'S CONDITION: " + condition)
        elif "TOTAL AGREEMENT" not in condition and "TOTAL_AGREEMENT" not in condition:
            print(final_decision_two(llm1, llm2, resp[0], resp[1], 150, question))
            print(models[cond_model] + "'S CONDITION: " + condition)
        else:
            print(final_decision(llm1, llm2, llm3,
                  responses[llms[0]][-1], responses[llms[1]][-1], responses[llms[2]][-1], 150, question))
        return False

    print("DISAGREEMENT")
    return False