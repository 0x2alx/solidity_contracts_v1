// SPDX-License-Identifier: MIT
pragma solidity ^0.8.13;

/*************************************************************************
 *           ....                 ....                ...                *
 *       .xH888888Hx.         .xH888888Hx.         xH88"`~ .x8X          *
 *     .H8888888888888:     .H8888888888888:     :8888   .f"8888Hf       *
 *     888*"""?""*88888X    888*"""?""*88888X   :8888>  X8L  ^""`        *
 *    'f     d8x.   ^%88k  'f     d8x.   ^%88k  X8888  X888h             *
 *    '>    <88888X   '?8  '>    <88888X   '?8  88888  !88888.           *
 *     `:..:`888888>    8>  `:..:`888888>    8> 88888   %88888           *
 *            `"*88     X          `"*88     X  88888 '> `8888>          *
 *       .xHHhx.."      !     .xHHhx.."      !  `8888L %  ?888   !       *
 *      X88888888hx. ..!     X88888888hx. ..!    `8888  `-*""   /        *
 *     !   "*888888888"     !   "*888888888"       "888.      :"         *
 *            ^"***"`              ^"***"`           `""***~"`           *
 *                                                                       *
 *************************************************************************
 * ERC721B2FA - Ultra Low Gas - 2 Factor Authentication                  *
 * @author: @ghooost0x2a                                                 *
 *************************************************************************
 * ERC721B2FA is based on ERC721B low gas contract by @squuebo_nft       *
 * and the LockRegistry/Guardian contracts by @OwlOfMoistness            *
 *************************************************************************
 *     :::::::              ::::::::      :::                            *
 *    :+:   :+: :+:    :+: :+:    :+:   :+: :+:                          *
 *    +:+  :+:+  +:+  +:+        +:+   +:+   +:+                         *
 *    +#+ + +:+   +#++:+       +#+    +#++:++#++:                        *
 *    +#+#  +#+  +#+  +#+    +#+      +#+     +#+                        *
 *    #+#   #+# #+#    #+#  #+#       #+#     #+#                        *
 *     #######             ########## ###     ###                        *
 *************************************************************************/

import "./ERC721B2FAEnumLitePausable.sol";
import "./GuardianLiteB2FA.sol";
import "@openzeppelin/contracts/utils/Address.sol";
import "@openzeppelin/contracts/utils/Strings.sol";

contract ERC721B2FA_DDCs02 is ERC721B2FAEnumLitePausable, GuardianLiteB2FA {
    using Address for address;
    using Strings for uint256;

    event Withdrawn(address indexed payee, uint256 weiAmount);

    uint256 public constant MAX_SUPPLY = 6666;
    uint256 public publicPrice = 0.0042 ether;
    uint256 public maxMintsPerTx = 10;

    string private baseURI = "";
    string private uriSuffix = ".json";
    string private commonURI = ""; // dev: is not "", this is the URI returned for any token (unrevealed)
    address[] private paymentRecipients;

    constructor()
        ERC721B2FAEnumLitePausable("Demon Death Cult s02", "DDCs02", 1)
    {}

    fallback() external payable {
        revert("You hit the fallback fn, fam! Try again.");
    }

    receive() external payable {
        revert("I love ETH, but don't send it to this contract!");
    }

    function togglePause(uint256 pauseIt) external onlyDelegates {
        if (pauseIt == 0) {
            _unpause();
        } else {
            _pause();
        }
    }

    function paymentRecipients() external view onlyDelegates {
        return paymentRecipients;
    }

    function tokenURI(uint256 tokenId)
        external
        view
        virtual
        override
        returns (string memory)
    {
        require(
            _exists(tokenId),
            "ERC721Metadata: URI query for nonexistent token"
        ); // dev: Sorry homie, that token doesn't exist

        if (bytes(commonURI).length > 0) {
            return string(abi.encodePacked(commonURI));
        }

        return
            bytes(baseURI).length > 0
                ? string(
                    abi.encodePacked(baseURI, tokenId.toString(), uriSuffix)
                )
                : "";
    }

    function setWithdrawalAddy(address newWithdrawalWallet)
        external
        onlyDelegates
    {
        withdrawalAddy = newWithdrawalWallet;
    }

    // dev: Set to "" to disable commonURI
    function setCommonURI(string calldata newCommonURI) external onlyDelegates {
        commonURI = newCommonURI;
    }

    function setBaseSuffixURI(
        string calldata newBaseURI,
        string calldata newURISuffix
    ) external onlyDelegates {
        baseURI = newBaseURI;
        uriSuffix = newURISuffix;
    }

    function setPublicPrice(uint256 newPrice) external onlyDelegates {
        publicPrice = newPrice;
    }

    function setMaxMintsPerTx(uint256 maxMint) external onlyDelegates {
        maxMintsPerTx = maxMint;
    }

    function setPaymentRecipients(address[] calldata addys)
        external
        onlyDelegates
    {
        paymentRecipients = addys;
    }

    function freeMints(uint256 quantity, address[] calldata recipients)
        external
        onlyDelegates
    {
        minty(quantity, recipients);
    }

    function publicMints(
        uint256 quantity,
        address[] calldata recipients,
        bytes32[] memory proof
    ) external payable whenNotPaused {
        require(quantity <= maxMintsPerTx, "You can't mint that many at once!");
        require(
            msg.value == publicPrice * quantity,
            "Incorrect amount of ETH sent!"
        );
        minty(quantity, recipients);
    }

    function minty(uint256 quantity, address[] calldata recipients) internal {
        require(quantity > 0, "Can't mint 0 tokens!");
        require(
            quantity == recipients.length || recipients.length == 1,
            "Call data is invalid"
        ); // dev: Call parameters are no bueno
        uint256 totSup = totalSupply();
        require(quantity + totSup <= MAX_SUPPLY, "Max supply reached!");

        address mintTo = withdrawalAddy;
        for (uint256 i = 0; i < quantity; i++) {
            mintTo = recipients.length == 1 ? recipients[0] : recipients[i];
            //_safeMint(mintTo, totSup + i + _offset);
            _safeMint(mintTo, next());
        }
    }

    function withdraw() external onlyDelegates {
        require(paymentRecipients.length == 3, "paymentRecipients.length != 3");

        uint256 contract_balance = address(this).balance;

        address payable demon_addy = payable(paymentRecipients[0]);
        address payable madi_thebaddie_addy = payable(paymentRecipients[1]);
        address payable ghosty_addy = payable(paymentRecipients[2]);

        uint256 demon_amount = (contract_balance / 1000) * 400;
        uint256 madi_thebaddie_amount = (contract_balance / 1000) * 300;
        uint256 ghosty_amount = (contract_balance / 1000) * 300;

        (bool success1, ) = demon_addy.call{value: (demon_amount)}("");
        require(success1, "Withdrawal 1 failed!");

        (bool success2, ) = madi_thebaddie_addy.call{
            value: (madi_thebaddie_amount)
        }("");
        require(success2, "Withdrawal 2 failed!");

        (bool success3, ) = ghosty_addy.call{value: (ghosty_amount)}("");
        require(success3, "Withdrawal 3 failed!");

        emit Withdrawn(demon_addy, demon_amount);
        emit Withdrawn(madi_thebaddie_addy, madi_thebaddie_amount);
        emit Withdrawn(ghosty_addy, ghosty_amount);
    }
}
