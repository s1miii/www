import os
import time
import requests
from bs4 import BeautifulSoup
from web3 import Web3
import logging

# Configure logging for tracking and troubleshooting
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
BASE_RPC_URL = os.getenv('BASE_RPC_URL')  # Base chain RPC URL
WALLET_ADDRESS = os.getenv('WALLET_ADDRESS')
PRIVATE_KEY = os.getenv('PRIVATE_KEY')

# Connect to the Base chain using Web3
web3 = Web3(Web3.HTTPProvider(BASE_RPC_URL))

# ERC-20 ABI for interacting with tokens
ERC20_ABI = '''
[
    {
        "constant": true,
        "inputs": [],
        "name": "name",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    },
    {
        "constant": false,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": true,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    }
]
'''

# Step 1: Function to Fetch New Tokens from Wow.xyz
def fetch_new_tokens():
    """
    Scrape Wow.xyz to get the list of new tokens.
    Returns a list of dictionaries with token name and contract address.
    """
    url = 'https://wow.xyz'  # Replace with Wow.xyz's actual URL
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    tokens = []
    for token_element in soup.find_all('div', class_='token-class'):  # Adjust based on Wow.xyz structure
        try:
            token_name = token_element.find('span', class_='token-name').text
            contract_address = token_element.find('a', class_='contract-link')['href']
            tokens.append({'name': token_name, 'address': contract_address})
        except Exception as e:
            logging.error(f"Error parsing token: {e}")
    return tokens

# Step 2: Function to Buy a Token
def buy_token(contract_address):
    """
    Creates and sends a transaction to buy 0.002 ETH worth of a given token.
    Returns the transaction hash if successful.
    """
    try:
        # Initialize token contract
        token_contract = web3.eth.contract(address=contract_address, abi=ERC20_ABI)
        
        # Build transaction
        txn = {
            'to': contract_address,
            'from': WALLET_ADDRESS,
            'value': Web3.toWei(0.002, 'ether'),
            'gas': 200000,
            'gasPrice': web3.toWei('50', 'gwei'),  # Adjust if Base network norms differ
            'nonce': web3.eth.getTransactionCount(WALLET_ADDRESS)
        }
        
        # Sign and send transaction
        signed_txn = web3.eth.account.sign_transaction(txn, private_key=PRIVATE_KEY)
        tx_hash = web3.eth.sendRawTransaction(signed_txn.rawTransaction)
        logging.info(f'Transaction sent with hash: {tx_hash.hex()}')
        return tx_hash
    except Exception as e:
        logging.error(f"Failed to buy token at {contract_address}: {e}")
        return None

# Step 3: Main Function for Monitoring and Purchasing
def main():
    """
    Main loop that monitors Wow.xyz for new tokens and attempts to buy them.
    If a purchase fails, it skips that token and continues with the next one.
    """
    seen_tokens = set()
    while True:
        # Fetch new tokens from Wow.xyz
        new_tokens = fetch_new_tokens()
        for token in new_tokens:
            if token['address'] not in seen_tokens:
                tx_hash = buy_token(token['address'])
                
                # Only add to seen tokens if the transaction was successful
                if tx_hash:
                    seen_tokens.add(token['address'])
                    logging.info(f"Bought 0.002 ETH of token {token['name']} at {token['address']}")
                else:
                    logging.warning(f"Skipping token {token['name']} at {token['address']} due to failed transaction.")
        
        # Wait before checking again
        time.sleep(60)  # Adjust frequency of checks as needed

if __name__ == '__main__':
    main()
