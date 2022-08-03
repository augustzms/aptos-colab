import requests
from restclient import RestClient

class FaucetClient:
    """
        Faucet creates and funds accounts. 
    """

    def __init__(self, url: str, rest_client: RestClient) -> None:
        self.url = url
        self.rest_client = rest_client

    def fund_account(self, address: str, amount: int) -> None:
        txns = requests.post(f"{self.url}/mint?amount={amount}&address={address}")
        assert txns.status_code == 200, txns.text
        for txn_hash in txns.json():
            self.rest_client.wait_for_transaction(txn_hash)
