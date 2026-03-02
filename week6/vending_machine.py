class VendingMachine:
    """
    A simple class to represent a Vending Machine.
    Teaches: Attributes, Methods, and State Management.
    """

    def __init__(self, item_name, item_price, stock):
        # Attributes: This is the 'State' of our machine
        self.item_name = item_name
        self.item_price = item_price
        self.stock = stock
        self.balance = 0.0  # Every machine starts with $0 inserted

    def insert_money(self, amount):
        """Action: Add money to the machine."""
        if amount > 0:
            self.balance += amount
            print(f"Added ${amount:.2f}. Current balance: ${self.balance:.2f}")
        else:
            print("Please insert a valid amount.")

    def purchase(self):
        """Action: Try to buy the item."""
        if self.stock <= 0:
            print(f"Sorry, {self.item_name} is out of stock!")
            return False
        elif self.balance < self.item_price:
            missing = self.item_price - self.balance
            print(f"Insufficient funds. You need ${missing:.2f} more.")
            return False
        else:
            # Successful transaction
            self.stock -= 1
            self.balance -= self.item_price
            print(f"Dispensing {self.item_name}...")
            print(f"Remaining balance: ${self.balance:.2f}")
            return True

    def refund(self):
        """Action: Give back the unused money."""
        if self.balance > 0:
            print(f"Returning ${self.balance:.2f} to user.")
            self.balance = 0.0
        else:
            print("No balance to refund.")

    def restock(self, quantity):
        self.stock = self.stock + quantity