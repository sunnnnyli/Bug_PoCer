from decimal import Decimal


dex_1_bal = Decimal(100)
dex_2_bal = Decimal(100)

user_1_bal = Decimal(10)
user_2_bal = Decimal(10)



def swapPrice(from_t, to_t, amt):
    if to_t == "2":
        return (amt * dex_2_bal) / dex_1_bal
    elif to_t == "1":
        return (amt * dex_1_bal) / dex_2_bal
    
def swap(from_t, to_t, amt):
    global dex_1_bal, dex_2_bal, user_1_bal, user_2_bal
    swap_amt = swapPrice(from_t, to_t, amt)

    if from_t == "1":
        dex_1_bal += amt
        user_1_bal -= amt
        dex_2_bal -= swap_amt
        user_2_bal += swap_amt

    elif from_t == "2":
        dex_2_bal += amt
        user_2_bal -= amt
        dex_1_bal -= swap_amt
        user_1_bal += swap_amt

amt_to_transfer = 10

def print_bals():
    print("Dex 1 Bal: ", dex_1_bal)
    print("Dex 2 Bal: ", dex_2_bal)
    print("User 1 Bal: ", user_1_bal)
    print("User 2 Bal: ", user_2_bal)

for i in range(10):
    print("------------------")
    print_bals()
    print(f"\tSwap 1 to 2: {min(user_1_bal, dex_1_bal)}")
    swap("1", "2", min(user_1_bal, dex_1_bal))
    print_bals()
    print(f"\tSwap 2 to 1: {min(user_2_bal, dex_2_bal)}")
    swap("2", "1", min(user_2_bal, dex_2_bal))


'''
    swap(added, "1", "2")
    new_price = 

'''


