from electrum.exceptions import MissingHeader
from electrum.util import inv_dict, read_json
from .abstract_network import AbstractNet
from .auxpow_mixin import AuxPowMixin


class PruxcoinMainnet(AbstractNet, AuxPowMixin):

    NAME = 'Pruxcoin'
    NAME_LOWER = 'pruxcoin'
    SHORT_CODE = 'PRUX'
    TESTNET = False
    WIF_PREFIX = 183
    ADDRTYPE_P2PKH = 55
    ADDRTYPE_P2SH = 117
    SEGWIT_HRP = "pr"
    GENESIS = "32dca787cfb73d50595a599b6fd72afce9a7c52ead22b8f15dfd8aabc5eaac32"
    DEFAULT_PORTS = {'t': '50001', 's': '50002'}
    DEFAULT_SERVERS = read_json('servers/Pruxcoin-Mainnet.json', {})
    CHECKPOINTS = read_json('checkpoints/Pruxcoin-Mainnet.json', [])
    BLOCK_HEIGHT_FIRST_LIGHTNING_CHANNELS = 99999999
    DATA_DIR = 'prux'

    XPRV_HEADERS = {
        'standard':    0x0488ade4,  # xprv
        'p2wpkh-p2sh': 0x049d7878,  # yprv
        'p2wsh-p2sh':  0x0295b005,  # Yprv
        'p2wpkh':      0x04b2430c,  # zprv
        'p2wsh':       0x02aa7a99,  # Zprv
    }
    XPRV_HEADERS_INV = inv_dict(XPRV_HEADERS)
    XPUB_HEADERS = {
        'standard':    0x0488b21e,  # xpub
        'p2wpkh-p2sh': 0x049d7cb2,  # ypub
        'p2wsh-p2sh':  0x0295b43f,  # Ypub
        'p2wpkh':      0x04b24746,  # zpub
        'p2wsh':       0x02aa7ed3,  # Zpub
    }
    XPUB_HEADERS_INV = inv_dict(XPUB_HEADERS)
    BIP44_COIN_TYPE = 0
    LN_REALM_BYTE = 0
    LN_DNS_SEEDS = []
    OPEN_ALIAS_PREFIX = 'prux'
    PAYMENT_URI_SCHEME = 'pruxcoin'
    PAYMENT_REQUEST_PKI_TYPE = "dnssec+prux"
    APPLICATION_PAYMENT_REQUEST_TYPE = 'application/prux-paymentrequest'
    APPLICATION_PAYMENT_TYPE = 'application/prux-payment'
    APPLICATION_PAYMENT_ACK_TYPE = 'application/prux-paymentack'
    COINBASE_MATURITY = 259
    COIN = 100000000
    TOTAL_COIN_SUPPLY_LIMIT = 141375
    SIGNED_MESSAGE_PREFIX = b"\x18Pruxcoin Signed Message:\n"

    BASE_UNITS = {'PRUX': 8, 'mPRUX': 5, 'uPRUX': 2, 'sat': 0}
    BASE_UNITS_INVERSE = inv_dict(BASE_UNITS)
    BASE_UNITS_LIST = ['PRUX', 'mPRUX', 'uPRUX', 'sat']
    DECIMAL_POINT_DEFAULT = 8  # mPRUX
    AUXPOW_CHAIN_ID = 0x03BF
    AUXPOW_START_HEIGHT = 15615201
    BLOCK_VERSION_AUXPOW_BIT = 0x100

    BLOCK_EXPLORERS = {}
    # The default Bitcoin frame size limit of 1 MB doesn't work for AuxPoW-based
    # chains, because those chains' block headers have extra AuxPoW data.  A limit
    # of 10 MB works fine for Namecoin as of block height 418744 (5 MB fails after
    # height 155232); we set a limit of 20 MB so that we have extra wiggle room.
    MAX_INCOMING_MSG_SIZE = 100_000_000_000  # in bytes

    TARGET_TIMESPAN = int(60 * 6)
    TARGET_SPACING = int(3)
    INTERVAL = int(TARGET_TIMESPAN / TARGET_SPACING)
