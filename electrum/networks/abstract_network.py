from electrum import bitcoin
from electrum.util import inv_dict

class AbstractNet(object):

    BLOCK_HEIGHT_FIRST_LIGHTNING_CHANNELS = 0
    CHECKPOINTS = []
    GENESIS = None
    HEADER_SIZE = 80  # bytes
    MAX_TARGET = 0x00000fffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
    MAX_INCOMING_MSG_SIZE = 1_000_000  # in bytes


    @classmethod
    def max_checkpoint(cls) -> int:
        return max(0, (len(cls.CHECKPOINTS)-1) * 2016 - 1)

    @classmethod
    def rev_genesis_bytes(cls) -> bytes:
        return bytes.fromhex(bitcoin.rev_hex(cls.GENESIS))

    @classmethod
    def is_segwit_enabled(cls) -> bool:
        return hasattr(cls, 'SEGWIT_HRP') and cls.SEGWIT_HRP
