// SPDX-License-Identifier: MIT
pragma solidity 0.8.15;

/*
 *           ....                 ....
 *       .xH888888Hx.         .xH888888Hx.
 *     .H8888888888888:     .H8888888888888:
 *     888*"""?""*88888X    888*"""?""*88888X
 *    'f     d8x.   ^%88k  'f     d8x.   ^%88k
 *    '>    <88888X   '?8  '>    <88888X   '?8
 *     `:..:`888888>    8>  `:..:`888888>    8>
 *            `"*88     X          `"*88     X
 *       .xHHhx.."      !     .xHHhx.."      !
 *      X88888888hx. ..!     X88888888hx. ..!
 *     !   "*888888888"     !   "*888888888"
 *            ^"***"`              ^"***"`
 *
 * FOUNDER: @psychedemon
 * ART: @Cho_Though, @madison_nft, @ccalicobuns
 * DEV: @ghooost0x2a
 **********************************
 * @title: Demonic Dorks
 * @author: @ghooost0x2a ⊂(´･◡･⊂ )∘˚˳°
 **********************************
 * ERC721B2FA - Ultra Low Gas - 2 Factor Authentication
 *****************************************************************
 * ERC721B2FA is based on ERC721B low gas contract by @squuebo_nft
 * and the LockRegistry/Guardian contracts by @OwlOfMoistness
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
import "./GuardianLiteB2FA.sol";
import "@openzeppelin/contracts/utils/Address.sol";
import "@openzeppelin/contracts/utils/Strings.sol";

contract DemonicDorks is ERC721B2FAEnumLitePausable, GuardianLiteB2FA {
    using Address for address;
    using Strings for uint256;

    event Withdrawn(address indexed payee, uint256 weiAmount);

    uint256 public MAX_SUPPLY = 10000;
    string internal0xd59430d7e026313cB82c92455DaDf8319df8069c baseURI = "";
    string internal uriSuffix = "";
    string internal commonURI = "revealed";

    address private paymentRecipient =
        0xBB9422050576bf1792117c18941804034286f232;

    // dev: public mints
    uint256 public maxPublicDDPerWallet = 3;
    uint256 public maxPublicDDPerTx = 1;

    constructor() ERC721B2FAEnumLitePausable("DemonicDorks", "DD", 1) {}

    fallback() external payable {
        revert("You hit the fallback fn, fam! Try again.");
    }

    receive() external payable {}

    //getter fns
    function getPaymentRecipient()
        external
        view
        onlyDelegates
        returns (address)
    {
        return paymentRecipient;
    }

    function tokenURI(uint256 tokenId)
        external
        view
        override
        returns (string memory)
    {
        require(
            _exists(tokenId),
            "ERC721Metadata: URI query for nonexistent token"
        );
        string memory rev_str = "revealed";
        if (
            keccak256(abi.encodePacked(commonURI)) !=
            keccak256(abi.encodePacked(rev_str))
        ) {
            return string(abi.encodePacked(commonURI));
        }

        return
            bytes(baseURI).length > 0
                ? string(
                    abi.encodePacked(baseURI, tokenId.toString(), uriSuffix)
                )
                : "";
    }

    //setter fns
    function togglePause(uint256 pauseIt) external onlyDelegates {
        if (pauseIt == 0) {
            _unpause();
        } else {
            _pause();
        }
    }

    function setCommonURI(string calldata newCommonURI) external onlyDelegates {
        //dev: Set to "" to disable commonURI
        commonURI = newCommonURI;
    }

    function setBaseSuffixURI(
        string calldata newBaseURI,
        string calldata newURISuffix
    ) external onlyDelegates {
        baseURI = newBaseURI;
        uriSuffix = newURISuffix;
    }

    function setMaxPublicDDPerWallet(uint256 maxMint) external onlyDelegates {
        maxPublicDDPerWallet = maxMint;
    }

    function setMaxPublicDDPerTx(uint256 maxPerTx) external onlyDelegates {
        maxPublicDDPerTx = maxPerTx;
    }

    function setPaymentRecipient(address addy) external onlyDelegates {
        paymentRecipient = addy;
    }

    function setReducedMaxSupply(uint256 new_max_supply)
        external
        onlyDelegates
    {
        require(new_max_supply < MAX_SUPPLY, "Can only set a lower size.");
        require(
            new_max_supply >= totalSupply(),
            "New supply lower current totalSupply"
        );
        MAX_SUPPLY = new_max_supply;
    }

    function feelinMinty(uint256 quantity) external {
        bool is_delegate = _isDelegate(_msgSender());
        require(!paused() || is_delegate, "Public mint is not open yet!");
        require(quantity > 0, "Can't mint 0 tokens!");
        require(
            quantity <= maxPublicDDPerTx,
            "You can only mint one DD at a time"
        );
        uint256 owner_wallet_qty = balanceOf(_msgSender());
        require(
            quantity + owner_wallet_qty <= maxPublicDDPerWallet,
            "Max NFTs per wallet reached!"
        );
        uint256 totSup = totalSupply();
        require(quantity + totSup <= MAX_SUPPLY, "Max supply reached!");
        for (uint256 i = 0; i < quantity; i++) {
            _safeMint(_msgSender(), next());
        }
    }

    //Just in case some ETH ends up in the contract so it doesn't remain stuck.
    function withdraw() external onlyDelegates {
        uint256 contract_balance = address(this).balance;

        address payable w_addy = payable(paymentRecipient);

        (bool success, ) = w_addy.call{value: (contract_balance)}("");
        require(success, "Withdrawal failed!");

        emit Withdrawn(w_addy, contract_balance);
    }
}
