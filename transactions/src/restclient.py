import requests
import time
from account import Account
from typing import Any, Dict, Optional

class RestClient:
    """
        Wrapper to call the Aptos-core Rest API
    """

    def __init__(self, url: str) -> None:
        self.url = url

    def account(self, account_address: str) -> Dict[str, str]:
        """：
            Returns the seq number & authentication key for the account.
        """
        
        response = requests.get(f"{self.url}/accounts/{account_address}")
        assert response.status_code == 200, f"{response.text} - {account_address}"
        return response.json()

    def account_resource(self, account_address: str, resource_type: str) -> Optional[Dict[str, Any]]:
        response = requests.get(f"{self.url}/accounts/{account_address}/resource/{resource_type}")
        if response.status_code == 404:
            return None
        assert response.status_code == 200, response.text
        return response.json()

    def generate_transaction(self, sender: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        account_res = self.account(sender)
        seq_num = int(account_res["sequence_number"])
        txn_request = {
            "sender": f"0x{sender}",
            "sequence_number": str(seq_num),
            "max_gas_amount": "2000",
            "gas_unit_price": "1",
            "gas_currency_code": "XUS",
            "expiration_timestamp_secs": str(int(time.time()) + 600),
            "payload": payload,
        }
        return txn_request

    def sign_transaction(self, account_from: Account, txn_request: Dict[str, Any]) -> Dict[str, Any]:
        """
            Sign the generated transaction.
        """
        res = requests.post(f"{self.url}/transactions/signing_message", json=txn_request)
        assert res.status_code == 200, res.text
        to_sign = bytes.fromhex(res.json()["message"][2:])
        signature = account_from.signing_key.sign(to_sign).signature
        txn_request["signature"] = {
            "type": "ed25519_signature",
            "public_key": f"0x{account_from.pub_key()}",
            "signature": f"0x{signature.hex()}",
        }
        return txn_request

    def submit_transaction(self, txn: Dict[str, Any]) -> Dict[str, Any]:
        """
            Submit the signed transacton to the blockchain.
        """
        headers = {'Content-Type': 'application/json'}
        response = requests.post(f"{self.url}/transactions", headers=headers, json=txn)
        assert response.status_code == 202, f"{response.text} - {txn}"
        return response.json()

    def transaction_pending(self, txn_hash: str) -> bool:
        response = requests.get(f"{self.url}/transactions/{txn_hash}")
        if response.status_code == 404:
            return True
        assert response.status_code == 200, f"{response.text} - {txn_hash}"
        return response.json()["type"] == "pending_transaction"

    def wait_for_transaction(self, txn_hash: str) -> None:
        count = 0
        while self.transaction_pending(txn_hash):
            assert count < 10, f"transaction {txn_hash} timed out"
            time.sleep(1)
            count += 1
        response = requests.get(f"{self.url}/transactions/{txn_hash}")
        assert "success" in response.json(), f"{response.text} - {txn_hash}"

    def account_balance(self, account_address: str) -> Optional[int]:
        return self.account_resource(account_address, "0x1::coin::CoinStore<0x1::aptos_coin::AptosCoin>")

    def transfer(self, account_from: Account, recipient: str, amount: int) -> str:
        payload = {
            "type": "script_function_payload",
            "function": "0x1::coin::transfer",
            "type_arguments": ["0x1::aptos_coin::AptosCoin"],
            "arguments": [
                f"0x{recipient}",
                str(amount),
            ]
        }
        txn_request = self.generate_transaction(account_from.address(), payload)
        signed_txn = self.sign_transaction(account_from, txn_request)
        res = self.submit_transaction(signed_txn)
        return str(res["hash"])

