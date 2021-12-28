from electrum import auxpow, blockchain, constants
from electrum.util import bfh, bh2u

from . import SequentialTestCase
from . import TestCaseForTestnet
from . import FAST_TESTS




class Test_auxpow(SequentialTestCase):

    @staticmethod
    def deserialize_with_auxpow(data_hex: str, **kwargs):
        """Deserializes a block header given as hex string

        This makes sure that the data is always deserialised as full
        block header with AuxPoW.

        The keyword-arguments expect_trailing_data and start_position can be
        set and will be passed on to deserialize_full_header."""

        # We pass a height beyond the last checkpoint, because
        # deserialize_full_header expects checkpointed headers to be truncated
        # by ElectrumX (i.e. not contain an AuxPoW).
        return blockchain.deserialize_full_header(bfh(data_hex), constants.net.max_checkpoint() + 1, **kwargs)

    @staticmethod
    def clear_coinbase_outputs(auxpow_header: dict, fix_merkle_root=True) -> None:
        """Clears the auxpow coinbase outputs

        Set the outputs of the auxpow coinbase to an empty list.  This is
        necessary when the coinbase has been modified and needs to be
        re-serialised, since present outputs are invalid due to the
        fast_tx_deserialize optimisation."""

        auxpow_header['parent_coinbase_tx']._outputs = []

        # Clear the cached raw serialization
        auxpow_header['parent_coinbase_tx'].invalidate_ser_cache()

        # Re-serialize.  Note that our AuxPoW library won't do this for us,
        # because it optimizes via fast_txid.
        auxpow_header['parent_coinbase_tx']._cached_network_ser_bytes = bfh(auxpow_header['parent_coinbase_tx'].serialize_to_network(force_legacy=True))

        # Correct the coinbase Merkle root.
        if fix_merkle_root:
            update_merkle_root_to_match_coinbase(auxpow_header)

    # Deserialize the AuxPoW header from Namecoin block #37,174.
    # This height was chosen because it has large, non-equal lengths of the
    # coinbase and chain Merkle branches.  It has an explicit coinbase MM
    # header.
    # Equivalent to parseAuxPoWHeader in libdohj tests.
    def test_deserialize_auxpow_header_explicit_coinbase(self):
        header = self.deserialize_with_auxpow(namecoin_header_37174)
        header_auxpow = header['auxpow']

        self.assertEqual(constants.net.AUXPOW_CHAIN_ID, header_auxpow['chain_id'])

        coinbase_tx = header_auxpow['parent_coinbase_tx']
        expected_coinbase_txid = '8a3164be45a621f85318647d425fe9f45837b8e42ec4fdd902d7f64daf61ff4a'
        observed_coinbase_txid = auxpow.fast_txid(coinbase_tx)

        self.assertEqual(expected_coinbase_txid, observed_coinbase_txid)

        self.assertEqual(header_auxpow['coinbase_merkle_branch'], [
            "f8f27314022a5165ae122642babb28dd44191dd36f99dad80b4f16b75197dde0",
            "c8a9dc420e17dee7b04bc0174c7a37ed9e5bc3f0ea0fdfe0b5d24bfc19ecedb0",
            "0ce9c5b98e212527e4aa7b9298435dc4e8f4dfc4dc63b7c89c06300637c33620",
            "3b6d0c4122a5b047cb879a440461839f0446f6bd451f01c6f0b14b6624e84136",
            "458500be38a68b215112df5e52d9c08fdd52034fb2005ce15d2a42be28e436cb",
        ])

        coinbase_merkle_index = header_auxpow['coinbase_merkle_index']
        self.assertEqual(0, coinbase_merkle_index)

        self.assertEqual(header_auxpow['chain_merkle_branch'], [
            "000000000000000000000000000000000000000000000000000000000000000a",
            "65bd8eb2c7e3a3646507977e8659e5396b197f197fbb51e7158927a263798302",
            "5f961bb13289d705abb28376a01f7097535c95f87b9e719b9ec39d8eb20d72e9",
            "7cb5fdcc41120d6135a40a6753bddc0c9b675ba2936d2e0cd78cdcb02e6beb50",
        ])

        chain_merkle_index = header_auxpow['chain_merkle_index']
        self.assertEqual(11, chain_merkle_index)

        expected_parent_header = blockchain.deserialize_pure_header(bfh('0100000055a7bc918827dbe7d8027781d803f4b418589b7b9fc03e718a03000000000000625a3d6dc4dfb0ab25f450cd202ff3bdb074f2edde1ddb4af5217e10c9dbafb9639a0a4fd7690d1a25aeaa97'), None)

        expected_parent_hash = blockchain.hash_header(expected_parent_header)
        observed_parent_hash = blockchain.hash_header(header_auxpow['parent_header'])
        self.assertEqual(expected_parent_hash, observed_parent_hash)

        expected_parent_merkle_root = expected_parent_header['merkle_root']
        observed_parent_merkle_root = header_auxpow['parent_header']['merkle_root']
        self.assertEqual(expected_parent_merkle_root, observed_parent_merkle_root)

    def test_deserialize_should_reject_trailing_junk(self):
        with self.assertRaises(Exception):
            self.deserialize_with_auxpow(namecoin_header_37174 + "00")

    def test_deserialize_with_expected_trailing_data(self):
        data = "00" + namecoin_header_37174 + "00"
        _, start_position = self.deserialize_with_auxpow(data, expect_trailing_data=True, start_position=1)
        self.assertEqual(start_position, len(namecoin_header_37174)//2 + 1)

    # Verify the AuxPoW header from Namecoin block #37,174.
    # Equivalent to checkAuxPoWHeader in libdohj tests.
    def test_verify_auxpow_header_explicit_coinbase(self):
        header = self.deserialize_with_auxpow(namecoin_header_37174)
        blockchain.Blockchain.verify_header(header, namecoin_prev_hash_37174, namecoin_target_37174)

    # Verify the AuxPoW header from Namecoin block #19,414.  This header
    # doesn't have an explicit MM coinbase header.
    # Equivalent to checkAuxPoWHeaderNoTxHeader in libdohj tests.
    def test_verify_auxpow_header_implicit_coinbase(self):
        header = self.deserialize_with_auxpow(namecoin_header_19414)
        blockchain.Blockchain.verify_header(header, namecoin_prev_hash_19414, namecoin_target_19414)

    # Verify a header whose auxpow has a coinbase transaction without outputs.
    def test_verify_auxpow_header_zero_output_coinbase(self):
        header = self.deserialize_with_auxpow(header_zero_output_auxpow)
        blockchain.Blockchain.verify_header(header, prev_hash_zero_output_auxpow, target_zero_output_auxpow)

    # Check that a non-generate AuxPoW transaction is rejected.
    # Equivalent to shouldRejectNonGenerateAuxPoW in libdohj tests.
    def test_should_reject_non_generate_auxpow(self):
        header = self.deserialize_with_auxpow(namecoin_header_37174)
        header['auxpow']['coinbase_merkle_index'] = 0x01

        with self.assertRaises(auxpow.AuxPoWNotGenerateError):
            blockchain.Blockchain.verify_header(header, namecoin_prev_hash_37174, namecoin_target_37174)

    # Check that block headers from the sidechain are rejected as parent chain
    # for AuxPoW, via checking of the chain ID's.
    # Equivalent to shouldRejectOwnChainID in libdohj tests.
    def test_should_reject_own_chain_id(self):
        parent_header = self.deserialize_with_auxpow(namecoin_header_19204)
        self.assertEqual(1, auxpow.get_chain_id(parent_header))

        header = self.deserialize_with_auxpow(namecoin_header_37174)
        header['auxpow']['parent_header'] = parent_header

        with self.assertRaises(auxpow.AuxPoWOwnChainIDError):
            blockchain.Blockchain.verify_header(header, namecoin_prev_hash_37174, namecoin_target_37174)

    # Check that where the chain merkle branch is far too long to use, it's
    # rejected.
    # Equivalent to shouldRejectVeryLongMerkleBranch in libdohj tests.
    def test_should_reject_very_long_merkle_branch(self):
        header = self.deserialize_with_auxpow(namecoin_header_37174)
        header['auxpow']['chain_merkle_branch'] = list([32 * '00' for i in range(32)])

        with self.assertRaises(auxpow.AuxPoWChainMerkleTooLongError):
            blockchain.Blockchain.verify_header(header, namecoin_prev_hash_37174, namecoin_target_37174)

    # Later steps in AuxPoW validation depend on the contents of the coinbase
    # transaction. Obviously that's useless if we don't check the coinbase
    # transaction is actually part of the parent chain block, so first we test
    # that the transaction hash is part of the merkle tree. This test modifies
    # the transaction, invalidating the hash, to confirm that it's rejected.
    # Equivalent to shouldRejectIfCoinbaseTransactionNotInMerkleBranch in libdohj tests.
    def test_should_reject_bad_coinbase_merkle_branch(self):
        header = self.deserialize_with_auxpow(namecoin_header_37174)

        # Clearing the outputs modifies the coinbase transaction so that its
        # hash no longer matches the parent block merkle root.
        self.clear_coinbase_outputs(header['auxpow'], fix_merkle_root=False)

        with self.assertRaises(auxpow.AuxPoWBadCoinbaseMerkleBranchError):
            blockchain.Blockchain.verify_header(header, namecoin_prev_hash_37174, namecoin_target_37174)

    # Ensure that in case of a malformed coinbase transaction (no inputs) it's
    # caught and processed neatly.
    # Equivalent to shouldRejectIfCoinbaseTransactionHasNoInputs in libdohj tests.
    def test_should_reject_coinbase_no_inputs(self):
        header = self.deserialize_with_auxpow(namecoin_header_37174)

        # Set inputs to an empty list
        header['auxpow']['parent_coinbase_tx']._inputs = []

        self.clear_coinbase_outputs(header['auxpow'])

        with self.assertRaises(auxpow.AuxPoWCoinbaseNoInputsError):
            blockchain.Blockchain.verify_header(header, namecoin_prev_hash_37174, namecoin_target_37174)

    # Catch the case that the coinbase transaction does not contain details of
    # the merged block. In this case we make the transaction script too short
    # for it to do so.  This test is for the code path with an implicit MM
    # coinbase header.
    # Equivalent to shouldRejectIfMergedMineHeaderMissing in libdohj tests.
    def test_should_reject_coinbase_root_too_late(self):
        header = self.deserialize_with_auxpow(namecoin_header_19414)

        input_script = header['auxpow']['parent_coinbase_tx'].inputs()[0].script_sig

        padded_script = bfh('00') * (auxpow.MAX_INDEX_PC_BACKWARDS_COMPATIBILITY + 4)
        padded_script += input_script[8:]

        header['auxpow']['parent_coinbase_tx']._inputs[0].script_sig = padded_script

        self.clear_coinbase_outputs(header['auxpow'])

        with self.assertRaises(auxpow.AuxPoWCoinbaseRootTooLate):
            blockchain.Blockchain.verify_header(header, namecoin_prev_hash_19414, namecoin_target_19414)

    # Catch the case that more than one merged mine header is present in the
    # coinbase transaction (this is considered an attempt to confuse the
    # parser).  We use this Namecoin header because it has an explicit MM
    # coinbase header (otherwise it won't be a duplicate).
    # Equivalent to shouldRejectIfMergedMineHeaderDuplicated in libdohj tests.
    def test_should_reject_coinbase_root_duplicated(self):
        header = self.deserialize_with_auxpow(namecoin_header_37174)

        input_script = header['auxpow']['parent_coinbase_tx'].inputs()[0].script_sig

        new_script = input_script + auxpow.COINBASE_MERGED_MINING_HEADER

        header['auxpow']['parent_coinbase_tx']._inputs[0].script_sig = new_script

        self.clear_coinbase_outputs(header['auxpow'])

        with self.assertRaises(auxpow.AuxPoWCoinbaseRootDuplicatedError):
            blockchain.Blockchain.verify_header(header, namecoin_prev_hash_37174, namecoin_target_37174)

    # Verifies that the commitment of the auxpow to the block header it is
    # proving for is actually checked.
    # Analogous to shouldRejectIfCoinbaseMissingChainMerkleRoot in libdohj tests.
    # TODO: Maybe make this test closer to libdohj's test?
    def test_should_reject_coinbase_root_missing(self):
        header = self.deserialize_with_auxpow(namecoin_header_19414)
        # Modify the header so that its hash no longer matches the
        # chain Merkle root in the AuxPoW.
        header["timestamp"] = 42
        with self.assertRaises(auxpow.AuxPoWCoinbaseRootMissingError):
            blockchain.Blockchain.verify_header(header, namecoin_prev_hash_19414, namecoin_target_19414)


def update_merkle_root_to_match_coinbase(auxpow_header):
    """Updates the parent block merkle root

    This modifies the merkle root in the auxpow's parent block header to
    match the auxpow coinbase transaction.  We need this after modifying
    the coinbase for tests.

    Note that this also breaks the PoW.  This is fine for tests that
    fail due to an earlier check already."""

    coinbase = auxpow_header['parent_coinbase_tx']

    revised_coinbase_txid = auxpow.fast_txid(coinbase)
    revised_merkle_branch = [revised_coinbase_txid]
    revised_merkle_root = auxpow.calculate_merkle_root(revised_coinbase_txid, revised_merkle_branch, auxpow_header['coinbase_merkle_index'])

    auxpow_header['parent_header']['merkle_root'] = revised_merkle_root
    auxpow_header['coinbase_merkle_branch'] = revised_merkle_branch
