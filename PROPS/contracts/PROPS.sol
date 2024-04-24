// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

/**
 *
 *
 *    PPPPPPPPPPPPPPPPP   RRRRRRRRRRRRRRRRR        OOOOOOOOO     PPPPPPPPPPPPPPPPP      SSSSSSSSSSSSSSS
 *    P::::::::::::::::P  R::::::::::::::::R     OO:::::::::OO   P::::::::::::::::P   SS:::::::::::::::S
 *    P::::::PPPPPP:::::P R::::::RRRRRR:::::R  OO:::::::::::::OO P::::::PPPPPP:::::P S:::::SSSSSS::::::S
 *    PP:::::P     P:::::PRR:::::R     R:::::RO:::::::OOO:::::::OPP:::::P     P:::::PS:::::S     SSSSSSS
 *      P::::P     P:::::P  R::::R     R:::::RO::::::O   O::::::O  P::::P     P:::::PS:::::S
 *      P::::P     P:::::P  R::::R     R:::::RO:::::O     O:::::O  P::::P     P:::::PS:::::S
 *      P::::PPPPPP:::::P   R::::RRRRRR:::::R O:::::O     O:::::O  P::::PPPPPP:::::P  S::::SSSS
 *      P:::::::::::::PP    R:::::::::::::RR  O:::::O     O:::::O  P:::::::::::::PP    SS::::::SSSSS
 *      P::::PPPPPPPPP      R::::RRRRRR:::::R O:::::O     O:::::O  P::::PPPPPPPPP        SSS::::::::SS
 *      P::::P              R::::R     R:::::RO:::::O     O:::::O  P::::P                   SSSSSS::::S
 *      P::::P              R::::R     R:::::RO:::::O     O:::::O  P::::P                        S:::::S
 *      P::::P              R::::R     R:::::RO::::::O   O::::::O  P::::P                        S:::::S
 *    PP::::::PP          RR:::::R     R:::::RO:::::::OOO:::::::OPP::::::PP          SSSSSSS     S:::::S
 *    P::::::::P          R::::::R     R:::::R OO:::::::::::::OO P::::::::P          S::::::SSSSSS:::::S
 *    P::::::::P          R::::::R     R:::::R   OO:::::::::OO   P::::::::P          S:::::::::::::::SS
 *    PPPPPPPPPP          RRRRRRRR     RRRRRRR     OOOOOOOOO     PPPPPPPPPP           SSSSSSSSSSSSSSS
 *
 * DEV: @ghooost0x2a
 **********************************
 * @author: @ghooost0x2a
 * @founders: @ghooost0x2a / @youareinmymovie
 **********************************
 * ERC721B - Ultra Low Gas
 *****************************************************************
 * ERC721B2FA is based on ERC721B low gas contract by @squuebo_nft
 *****************************************************************
 *      .-----.
 *    .' -   - '.
 *   /  .-. .-.  \
 *   |  | | | |  |
 *    \ \o/ \o/ /
 *   _/    ^    \_
 *  | \  '---'  / |
 *  / /`--. .--`\ \
 * / /'---` `---'\ \
 * '.__.       .__.'
 *     `|     |`
 *      |     \
 *      \      '--.
 *       '.        `\
 *         `'---.   |
 *            ,__) /
 *             `..'
 */

import "./ERC721B2FAEnumLitePausable.sol";
import "@openzeppelin/contracts/utils/Address.sol";
import "@openzeppelin/contracts/utils/Strings.sol";

contract PROPS is ERC721B2FAEnumLitePausable {
    using Address for address;
    using Strings for uint256;

    event Withdrawn(address indexed payee, uint256 weiAmount);

    uint256 public MAX_SUPPLY = 2 ** 256 - 1;
    uint256 public mint_price = 0;
    bool public MINT_OPEN = false;

    string internal baseURI = "";
    string internal altBaseURI = "";
    string internal uriSuffix = "";
    string internal contract_URI = "";

    address public payment_recipient =
        0xA94F799A34887582987eC8C050f080e252B70A21;

    address internal MASTER_SIGNER = address(0);
    uint256 public MASTER_SIG_VALIDITY = 60;

    mapping(uint256 => bool) public use_static_metadata;

    struct Master_Approval {
        address approved_address;
        uint256 master_sig_timestamp;
    }

    struct EIP712Domain {
        string name;
        string version;
        uint256 chainId;
        address verifyingContract;
    }

    bytes32 constant EIP712DOMAIN_TYPEHASH =
        keccak256(
            "EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)"
        );
    bytes32 constant MA_TYPEHASH =
        keccak256(
            "Master_Approval(address approved_address,uint256 master_sig_timestamp)"
        );
    bytes32 DOMAIN_SEPARATOR;

    constructor() ERC721B2FAEnumLitePausable("PROPS", "PROPS", 1) {
        DOMAIN_SEPARATOR = hash(
            EIP712Domain({
                name: "PROPS",
                version: "1",
                //chainId: block.chainId,
                chainId: 1,
                // verifyingContract: this
                verifyingContract: address(this)
            })
        );
    }

    fallback() external payable {}

    receive() external payable {}

    function hash(
        EIP712Domain memory eip712Domain
    ) internal pure returns (bytes32) {
        return
            keccak256(
                abi.encode(
                    EIP712DOMAIN_TYPEHASH,
                    keccak256(bytes(eip712Domain.name)),
                    keccak256(bytes(eip712Domain.version)),
                    eip712Domain.chainId,
                    eip712Domain.verifyingContract
                )
            );
    }

    function hash(Master_Approval memory m_a) internal pure returns (bytes32) {
        return
            keccak256(
                abi.encode(
                    MA_TYPEHASH,
                    m_a.approved_address,
                    m_a.master_sig_timestamp
                )
            );
    }

    function get_master_signer()
        external
        view
        onlyDelegates
        returns (address master_signer)
    {
        return MASTER_SIGNER;
    }

    function get_signer(
        Master_Approval calldata m_a,
        bytes memory _master_signature
    ) public view returns (address) {
        bytes32 digest = keccak256(
            abi.encodePacked("\x19\x01", DOMAIN_SEPARATOR, hash(m_a))
        );
        (bytes32 r, bytes32 s, uint8 v) = split_signature(_master_signature);
        return ecrecover(digest, v, r, s);
    }

    function split_signature(
        bytes memory sig
    ) public pure returns (bytes32 r, bytes32 s, uint8 v) {
        require(sig.length == 65, "invalid signature length");

        assembly {
            /*
                First 32 bytes stores the length of the signature

                add(sig, 32) = pointer of sig + 32
                effectively, skips first 32 bytes of signature

                mload(p) loads next 32 bytes starting at the memory address p into memory
                */

            // first 32 bytes, after the length prefix
            r := mload(add(sig, 32))
            // second 32 bytes
            s := mload(add(sig, 64))
            // final byte (first byte of the next 32 bytes)
            v := byte(0, mload(add(sig, 96)))
        }

        // implicitly return (r, s, v)
    }

    function tokenURI(
        uint256 tokenId
    ) external view override returns (string memory) {
        require(
            _exists(tokenId),
            "ERC721Metadata: URI query for nonexistent token"
        );

        if (use_static_metadata[tokenId]) {
            return
                bytes(baseURI).length > 0
                    ? string(
                        abi.encodePacked(
                            altBaseURI,
                            tokenId.toString(),
                            uriSuffix
                        )
                    )
                    : "";
        } else {
            return
                bytes(baseURI).length > 0
                    ? string(
                        abi.encodePacked(baseURI, tokenId.toString(), uriSuffix)
                    )
                    : "";
        }
    }

    function setBaseSuffixURI(
        string calldata newBaseURI,
        string calldata newAltBaseURI,
        string calldata newURISuffix,
        string calldata newContractURI
    ) external onlyDelegates {
        baseURI = newBaseURI;
        uriSuffix = newURISuffix;
        altBaseURI = newAltBaseURI;
        contract_URI = newContractURI;
    }

    function contractURI() public view returns (string memory) {
        return contract_URI;
    }

    function toggleMint(bool mint_open) external onlyDelegates {
        MINT_OPEN = mint_open;
    }

    function resetStaticMetadataTokens(
        uint256[] calldata _new_static_tokens
    ) external onlyDelegates {
        for (uint256 i = 0; i < _new_static_tokens.length; i++) {
            use_static_metadata[i] = false;
        }
    }

    function setStaticMetadataTokens(
        uint256[] calldata _new_static_tokens
    ) external onlyDelegates {
        for (uint256 i = 0; i < _new_static_tokens.length; i++) {
            use_static_metadata[i] = true;
        }
    }

    function setMasterSigConf(
        address _master_signer,
        uint256 _master_sig_validity
    ) external onlyDelegates {
        MASTER_SIGNER = _master_signer;
        MASTER_SIG_VALIDITY = _master_sig_validity;
    }

    function setPaymentRecipient(address addy) external onlyDelegates {
        payment_recipient = addy;
    }

    function setReducedMaxSupply(
        uint256 new_max_supply
    ) external onlyDelegates {
        require(new_max_supply < MAX_SUPPLY, "Can only set a lower size.");
        require(
            new_max_supply >= totalSupply(),
            "New supply lower than current totalSupply"
        );
        MAX_SUPPLY = new_max_supply;
    }

    function setMintPrice(uint256 new_mint_price) external onlyDelegates {
        mint_price = new_mint_price;
    }

    // Mint fns
    function ghostyMint(
        uint256 quantity,
        address[] memory recipients
    ) external onlyDelegates {
        if (recipients.length == 1) {
            for (uint256 i = 0; i < quantity; i++) {
                _minty(1, recipients[0]);
            }
        } else {
            require(
                quantity == recipients.length,
                "Number of recipients doesn't match quantity."
            );
            for (uint256 i = 0; i < recipients.length; i++) {
                _minty(1, recipients[i]);
            }
        }
    }

    // Mint
    function propsMint(
        Master_Approval calldata m_a,
        bytes memory _master_sig
    ) external payable {
        require(MINT_OPEN || _isDelegate(_msgSender()), "Mint not open yet!");
        if (mint_price > 0) {
            require(msg.value == mint_price, "Invalid amount of ETH");
        }
        if (MASTER_SIGNER != address(0)) {
            require(
                get_signer(m_a, _master_sig) == MASTER_SIGNER,
                "Invalid master sig!"
            );
            require(
                m_a.approved_address == _msgSender(),
                "Not approved minter!"
            );
            require(
                m_a.master_sig_timestamp + MASTER_SIG_VALIDITY >
                    block.timestamp,
                "Master sig has expired!"
            );
        }
        _minty(1, _msgSender());
    }

    function _minty(uint256 quantity, address addy) internal {
        require(quantity > 0, "Can't mint 0 tokens!");
        require(quantity + totalSupply() <= MAX_SUPPLY, "Max supply reached!");
        for (uint256 i = 0; i < quantity; i++) {
            _safeMint(addy, next());
        }
    }

    function withdraw() external onlyDelegates {
        require(
            payment_recipient != address(0),
            "Don't send ETH to null address"
        );
        uint256 contract_balance = address(this).balance;

        address payable w_addy = payable(payment_recipient);

        (bool success, ) = w_addy.call{value: (contract_balance)}("");
        require(success, "Withdrawal failed!");

        emit Withdrawn(w_addy, contract_balance);
    }
}
