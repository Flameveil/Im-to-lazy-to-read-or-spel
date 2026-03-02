import vending_machine as vm # as creates an alias for import name. Handy for long file names.
import refrigerated_vending_machine as rvm

# --- LIVE DEMO SECTION ---

# 1. Create an 'Instance' of the machine
soda_machine = vm.VendingMachine("Doritos Nacho Cheese", 1.50, 5)

# 2. Interact with it
soda_machine.insert_money(1.00)
soda_machine.purchase()      # This should fail (not enough money)
soda_machine.insert_money(1.00)
soda_machine.purchase()      # This should succeed!
soda_machine.refund()        # Get the remaining $0.50 back

# --- VENDING MACHINE LAB (OO) ---   
# Add a restock(amount) method to the VendingMachine class that allows you to add more items to 
# the stock. Then, create a break room vending machine and restock it with 10 items. Test by 
# displaying the stock on hand.

gumball_machine = vm.VendingMachine("Hubba Bubba", 1.0, 50,)
print("current stock", gumball_machine.stock)
gumball_machine.restock(100)
print("new current stock", gumball_machine.stock)


# --- REFRIGERATED VENDING MACHINE LAB (Inheritance) ---   
 
# Create the refrigerated version
juice_cooler = rvm.RefrigeratedVendingMachine("Orange Juice", 2.50, 10, 4.0)

# call method to add 3 dollars to the machine so we can buy some juice
juice_cooler.insert_money(3)
# Notice: We never wrote 'insert_money' in the new class, 
# but it works because of inheritance!
# Try to buy (This will fail because it's too warm initially)
juice_cooler.purchase()
# Cool it down and try again
juice_cooler.cool_down()
# Now attempt to buy again (This should work now)
juice_cooler.insert_money(2.50)
# Your friend wants one too, but you only put in $3.00, so add more money to cover the cost
juice_cooler.insert_money(2.50)
