def similarity(a, b):
    return b * a

def match(first_entities, first_idx, second_entities, second_idx): # return total sim + sims array
    if (first_idx >= len(first_entities)):
        return (0, [])
    if (second_idx >= len(second_entities)):
        return (0, [])

    out1 = similarity(first_entities[first_idx], second_entities[second_idx]) # 1.1 to 1.1
    a_result, a_arr = match(first_entities, first_idx + 1, second_entities, second_idx + 1)
    a_arr = [out1] + a_arr

    b_result, b_arr = match(first_entities, first_idx, second_entities, second_idx + 1) # skip 1.first

    c_result, c_arr = match(first_entities, first_idx + 1, second_entities, second_idx) # skip 2.first
    
    if out1 + a_result >= b_result and out1 + a_result >= c_result:
        return (out1 + a_result , a_arr)
    
    if b_result >= out1 + a_result and b_result >= c_result:
        return (b_result, b_arr)
    
    return (c_result, c_arr)


a = [1, 2, 3, 4, 5]
b = [2, 1, 2, 1, 0]
print(match(a, 0, b, 0))