import constants

from account import Account
from faucetclient import FaucetClient
from restclient import RestClient

def run() -> None:
    rest_client = RestClient(constants.TESTNET_URL)
    faucet_client = FaucetClient(constants.FAUCET_URL, rest_client)

    # Create two accounts, Alice and Bob, and fund Alice but not Bob
    alice = Account()
    bob = Account()

    print("\n=== Addresses ===")
    print(f"Alice: {alice.address()}")
    print(f"Bob: {bob.address()}")

    faucet_client.fund_account(alice.address(), 5_000)
    faucet_client.fund_account(bob.address(), 0)

    print("\n=== Initial Balances ===")
    print(f"Alice: {rest_client.account_balance(alice.address())}")
    print(f"Bob: {rest_client.account_balance(bob.address())}")

    # Have Alice give Bob 10 coins
    tx_hash = rest_client.transfer(alice, bob.address(), 1_000)
    rest_client.wait_for_transaction(tx_hash)

    print("\n=== Final Balances ===")
    print(f"Alice: {rest_client.account_balance(alice.address())}")
    print(f"Bob: {rest_client.account_balance(bob.address())}")



if __name__ == "__main__":
    run()
