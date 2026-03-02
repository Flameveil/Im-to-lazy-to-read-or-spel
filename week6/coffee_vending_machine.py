
"""
Complete the coffee vending machine class below by finishing the following:
1. Complete the set_cream, set_sugar, set_strength methods. The implementation should test that sufficient funds have been entered and that the entered values are in the valid range.
2. Create a test Python script that constructs a coffee vending machine object by supplying the necessary information in the constructor. Each cup of coffee costs $1.50 and the machine should be constructed with enough supplies for 10 cups of coffee.

Each cup of coffee has a strength level (1-3), a cream count (0-2), and a sugar count (0-2). The methods to set these values prior to purchasing the coffee should only function if sufficient funds have been entered. When the coffee is purchased, print out the strength, cream, and sugar levels of the cup of coffee being dispensed. The default value for these is strong, black coffee with no cream or sugar. (the only way to drink it!). Regardless of what the customer selects, the defaults should be reset for the next customer and will dispense accordingly if not changed.

Assume that the inventory item contains all the cream, sugar, beans, filter, water, etc., needed for each cup of coffee. I.e. you don't have to track these ingredients in inventory.

Typical Order Pattern:
1. Insert sufficient funds
2. Select strength, cream, and sugar
3. Order coffee
4. As coffee is dispensed, display a message reflecting the specifics of the order
5. After dispensing and defaults are reset for the next order.

"""
import time
import vending_machine as vm

class CoffeeVendingMachine(vm.VendingMachine):
    def __init__(self, item_name, item_price, stock):
        super().__init__(item_name, item_price, stock)
        
        # add per order coffee attributes
        self.strength = 3 
        self.cream = 0
        self.sugar = 0

    def set_cream(self, count):
        if self.balance < self.item_price:
            print("Please insert sufficient funds first.")
            return
        
        if 0 <= count <= 2:
            self.cream = count
            print(f"Cream level set to {count}.")
        else:
            print("Invalid cream amount. Must be between 0 and 2.")

    def set_sugar(self, count):
        if self.balance < self.item_price:
            print("Please insert sufficient funds first.")
            return
        
        if 0 <= count <= 2:
            self.sugar = count
            print(f"Sugar level set to {count}.")
        else:
            print("Invalid sugar amount. Must be between 0 and 2.")

    def set_strength(self, count):
        if self.balance < self.item_price:
            print("Please insert sufficient funds first.")
            return
        
        if 1 <= count <= 3:
            self.strength = count
            print(f"Strength set to {count}.")
        else:
            print("Invalid strength. Must be between 1 and 3.")
            
    def purchase(self):
        if super().purchase():
            print("Brewing...", end = "")
            for i in range(6):
                print(".",end='',flush=True)
                time.sleep(0.5)
            print(f"\nCup of coffee with Strength: {self.strength}, Cream: {self.cream}, and Sugar: {self.sugar} is complete. Enjoy!")
            self.cream = 0
            self.sugar = 0
            self.strength = 3
        else:
            print("Unable to purchase, please come back later!")

    def menu(self):
        while True:
            print("\nBalance:",self.balance,"Price:", self.item_price, "Strength:",self.strength, "Creams:",self.cream, "Sugar:",self.sugar)
            print("\nU-Brewit Coffee Dispenser")
            print("1. Add Funds to Purchase Coffee")
            print("2. Set Strength")
            print("3. Set Cream Level")
            print("4. Set Sugar Level")
            print("5. Brew Coffee")
            print("6. Refund Money Entered")
            print("7. Quit")
            option = int(input("Enter Selection: "))
            if option == 1:
                money = float(input("Enter money submitted: $"))
                self.insert_money(money)
            elif option == 2:
                strength = int(input("Enter strength (1-3): "))
                self.set_strength(strength)
            elif option == 3:
                cream = int(input("Enter tsp of cream (0-2): "))
                self.set_cream(cream)
            elif option == 4:
                sugar = int(input("Enter tsp of sugar (0-2): "))
                self.set_sugar(sugar)
            elif option == 5:
                self.purchase()
            elif option == 6:
                self.refund()
            elif option == 7:
                break
        
if __name__ == '__main__':        
    coffee = CoffeeVendingMachine("strong coffee here", 1.0, 5)
    coffee.menu()