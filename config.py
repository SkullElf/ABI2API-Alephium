EnableManager = True
USERNAME = 'admin'
PASSWORD = 'password'
DB_PATH = "./databases/Config.db"
PORT = 80
ENVIRONMENT = "mainnet"
ENVIRONMENTS = {
    "mainnet": "https://wallet-v20.mainnet.alephium.org/"
}
PROXY_URL = ENVIRONMENTS[ENVIRONMENT]