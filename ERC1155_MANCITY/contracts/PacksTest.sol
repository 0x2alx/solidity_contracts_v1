// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC1155/ERC1155.sol";
import "@openzeppelin/contracts/token/common/ERC2981.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC1155/extensions/ERC1155Supply.sol";
import "@openzeppelin/contracts/utils/Strings.sol";
import "./RevokableDefaultOperatorFilterer.sol";
import "./UpdatableOperatorFilterer.sol";

interface ICARDS {
    function mintBatch(
        address _account,
        uint256[] memory _ids,
        uint256[] memory _amount
    ) external;
}

contract PacksT is
    ERC1155,
    Ownable,
    ERC2981,
    RevokableDefaultOperatorFilterer,
    ERC1155Supply
{
    using Strings for uint256;
    ICARDS public cardContract;

    string public constant name = "Packs";
    string public constant symbol = "PCK";
    string private baseURI =
        "ipfs://QmXuJKB9iHb1mkjFtxTooV1nAsqoZMGrLvGWq1WHbKg2AU/";

    uint256 public saleState = 0; //0 - Mint paused / 1 - Presale Mint only / 2 - Presale and public sale both open

    uint256 public cost = 0.0069 ether;

    address private signerAddress = 0xA4de23640d29DF1671f2B245676035e3E07909A3;

    mapping(uint256 => uint256) public maxTokenSupply;
    mapping(uint256 => bool) public tokensEnabled;
    mapping(uint256 => uint256) public currentSupply;

    mapping(uint256 => bytes32) internal processedNonces;
    mapping(uint256 => bytes32) internal processedNoncesBurn;

    struct EIP712Domain {
        string name;
        string version;
        uint256 chainId;
        address verifyingContract;
    }

    struct WhitelistMintParams {
        address addy; // Address authorized to mint
        uint256 valid_until_timestamp; // Unix timestamp of the master sig
        uint256[] ids; // Token ID authorized for mint
        uint256[] qtys; // Amount authorized to mint
        uint256[] paid_ids; // Token ID authorized for mint
        uint256[] paid_qtys; // Amount authorized to mint
        uint256 sig_nonce; // Generated by master when signing - If different than 0, track and enforce unique signatures
    }
    struct WhitelistMintParams2 {
        address addy; // Address authorized to mint
        uint256 valid_until_timestamp; // Unix timestamp of the master sig
        uint256 ids; // Token ID authorized for mint
        uint256 qtys; // Amount authorized to mint
        uint256 paid_ids; // Token ID authorized for mint
        uint256 paid_qtys; // Amount authorized to mint
        uint256 sig_nonce; // Generated by master when signing - If different than 0, track and enforce unique signatures
    }
    struct BurnMintParams {
        address addy; // Address authorized to mint
        uint256 valid_until_timestamp; // Unix timestamp of the master sig
        uint256[] ids;  
        uint256[] amounts;
        uint256[] mintIds;
        uint256[] mintAmounts;
        uint256 nonce;
    }
    bytes32 constant EIP712DOMAIN_TYPEHASH =
        keccak256(
            "EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)"
        );
    bytes32 constant WhitelistMintParams_TYPEHASH =
        keccak256(
            "WhitelistMintParams(address addy,uint256 valid_until_timestamp,uint256[] ids,uint256[] qtys,uint256[] paid_ids,uint256[] paid_qtys,uint256 sig_nonce)"
        );
    bytes32 constant WhitelistMintParams2_TYPEHASH =
        keccak256(
            "WhitelistMintParams2(address addy,uint256 valid_until_timestamp,uint256 ids,uint256 qtys,uint256 paid_ids,uint256 paid_qtys,uint256 sig_nonce)"
        );        
    bytes32 constant BurnMintParams_TYPEHASH =
        keccak256(
            "BurnMintParams(address addy,uint256 valid_until_timestamp,uint256[] ids,uint256[] amounts,uint256[] mintIds,uint256[] mintAmounts,uint256 nonce)"
        );
    bytes32 DOMAIN_SEPARATOR;

    constructor() ERC1155("") {
        _setDefaultRoyalty(msg.sender, 500);
        DOMAIN_SEPARATOR = hash(
            EIP712Domain({
                name: "ShrempPacks",
                version: "1",
                //chainId: block.chainId,
                chainId: 1,
                // verifyingContract: this
                verifyingContract: address(this)
            })
        );
        tokensEnabled[1] = true;
        maxTokenSupply[1] = 7713;
        tokensEnabled[2] = true;
        maxTokenSupply[2] = 7713;
        tokensEnabled[3] = true;
        maxTokenSupply[3] = 7714;
    }

    function owner()
        public
        view
        virtual
        override(Ownable, UpdatableOperatorFilterer)
        returns (address)
    {
        return Ownable.owner();
    }

    function hash(BurnMintParams calldata m_a) internal pure returns (bytes32) {
        return
            keccak256(
                abi.encode(
                    BurnMintParams_TYPEHASH,
                    m_a.addy,
                    m_a.valid_until_timestamp,
                    m_a.ids,
                    m_a.amounts,
                    m_a.mintIds,
                    m_a.mintAmounts,
                    m_a.nonce
                )
            );
    }
    function hash(
        WhitelistMintParams2 calldata m_a
    ) internal pure returns (bytes32) {
        return
            keccak256(
                abi.encode(
                    WhitelistMintParams2_TYPEHASH,
                    m_a.addy,
                    m_a.valid_until_timestamp,
                    m_a.ids,
                    m_a.qtys,
                    m_a.paid_ids,
                    m_a.paid_qtys, 
                    m_a.sig_nonce
                )
            );
    }
    function hash(
        WhitelistMintParams calldata m_a
    ) internal pure returns (bytes32) {
        return
            keccak256(
                abi.encode(
                    WhitelistMintParams_TYPEHASH,
                    m_a.addy,
                    m_a.valid_until_timestamp,
                    keccak256(abi.encodePacked(m_a.ids)),
                    keccak256(abi.encodePacked(m_a.qtys)),
                    keccak256(abi.encodePacked(m_a.paid_ids)),
                    keccak256(abi.encodePacked(m_a.paid_qtys)),
                    m_a.sig_nonce
                )
            );
    }

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

    function get_signer_wl(
        WhitelistMintParams calldata m_a,
        bytes memory _master_signature
    ) public view returns (address) {
        bytes32 digest = keccak256(
            abi.encodePacked("\x19\x01", DOMAIN_SEPARATOR, hash(m_a))
        );
        (bytes32 r, bytes32 s, uint8 v) = split_signature(_master_signature);
        return ecrecover(digest, v, r, s);
    }
    function get_signer_wl2(
        WhitelistMintParams2 calldata m_a,
        bytes memory _master_signature
    ) public view returns (address) {
        bytes32 digest = keccak256(
            abi.encodePacked("\x19\x01", DOMAIN_SEPARATOR, hash(m_a))
        );
        (bytes32 r, bytes32 s, uint8 v) = split_signature(_master_signature);
        return ecrecover(digest, v, r, s);
    }
    function get_signer_burn(
        BurnMintParams calldata m_a,
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
            r := mload(add(sig, 32))
            s := mload(add(sig, 64))
            v := byte(0, mload(add(sig, 96)))
        }
    }

    function setBaseURI(string calldata _baseURI) external onlyOwner {
        baseURI = _baseURI;
    }

    function setCardContractAddress(ICARDS _cardContract) external onlyOwner {
        cardContract = _cardContract;
    }

    function setSignerAddress(address _signerAddress) external onlyOwner {
        signerAddress = _signerAddress;
    }
    function _mintChecks(
        uint256 _id, uint256 _amount
    ) internal {
        require(tokensEnabled[_id], "Token id not enabled!");
        require(
            currentSupply[_id] + _amount <= maxTokenSupply[_id],
            "Max supply exceeded for pack!"
        );
        currentSupply[_id] += _amount;
    }

    function mint(uint256 _id, uint256 _amount) external payable {
        require(saleState >= 2, "public sale not active");
        _mintChecks(_id, _amount);
        require(msg.value >= cost * _amount, "Insufficient funds!");
        _mint(msg.sender, _id, _amount, "");
    }

    function whitelistMint(
        WhitelistMintParams calldata _params,
        bytes memory _signature
    ) external payable {
        require(saleState >= 1, "presale not active");
        require(
            get_signer_wl(_params, _signature) == signerAddress,
            "Invalid master sig!"
        );
        require(_params.addy == _msgSender(), "Not approved minter!");
        require(
            block.timestamp < _params.valid_until_timestamp,
            "Signature Expired!"
        );
        bytes32 msig = keccak256(_signature);
        require(
            processedNonces[_params.sig_nonce] != msig,
            "Sig already used!"
        );
        processedNonces[_params.sig_nonce] = msig;

        for (uint256 i = 0; i < _params.ids.length; i++) {
            require(tokensEnabled[_params.ids[i]], "Token id not enabled!");
            require(
                currentSupply[_params.ids[i]] + _params.qtys[i] <=
                    maxTokenSupply[_params.ids[i]],
                "Max supply exceeded for pack!"
            );
            currentSupply[_params.ids[i]] += _params.qtys[i];
        }
        if (_params.paid_ids.length == 1) {
            _mintChecks(_params.paid_ids[0], _params.paid_qtys[0]);
            require(msg.value >= cost * _params.paid_qtys[0], "Insufficient funds!");
            _mint(msg.sender, _params.paid_ids[0], _params.paid_qtys[0], "");            
        }     
        else if (_params.paid_ids.length > 1) {
            uint256 tamount = _mintBatchChecks(_params.paid_ids,_params.paid_qtys);
            require(msg.value >= cost * tamount, "Insufficient funds!");
            _mintBatch(msg.sender, _params.paid_ids, _params.paid_qtys, "");
        }  
        _mintBatch(msg.sender, _params.ids, _params.qtys, "");
    }

    function _mintBatchChecks(
        uint256[] calldata _ids,
        uint256[] calldata _amounts
    ) internal returns (uint256) {
        uint256 tamount;
        for (uint256 i = 0; i < _ids.length; i++) {
            require(tokensEnabled[_ids[i]], "Token id not enabled!");
            require(
                currentSupply[_ids[i]] + _amounts[i] <= maxTokenSupply[_ids[i]],
                "Max supply exceeded for pack!"
            );
            currentSupply[_ids[i]] += _amounts[i];
            tamount += _amounts[i];
        }
        return tamount;
    }

    function mintBatch(
        uint256[] calldata _ids,
        uint256[] calldata _amounts
    ) external payable {
        require(saleState >= 2, "public sale not active");
        uint256 tamount = _mintBatchChecks(_ids,_amounts);
        require(msg.value >= cost * tamount, "Insufficient funds!");
        _mintBatch(msg.sender, _ids, _amounts, "");
    }

    function ownerMint(
        address _receiver,
        uint256 _id,
        uint256 _amount
    ) external onlyOwner {
        require(tokensEnabled[_id], "Token id not enabled!");
        require(
            currentSupply[_id] + _amount <= maxTokenSupply[_id],
            "Max supply exceeded!"
        );
        currentSupply[_id] += _amount;
        _mint(_receiver, _id, _amount, "");
    }

    function getSignerAddress() external view returns (address) {
        return signerAddress;
    }

    function _beforeTokenTransfer(
        address operator,
        address from,
        address to,
        uint256[] memory ids,
        uint256[] memory amounts,
        bytes memory data
    ) internal override(ERC1155, ERC1155Supply) {
        super._beforeTokenTransfer(operator, from, to, ids, amounts, data);
    }

    function setTokenEnabled(
        uint256 _tokenId,
        uint256 _maxSupply
    ) external onlyOwner {
        require(!tokensEnabled[_tokenId], "Token already enabled");
        tokensEnabled[_tokenId] = true;
        maxTokenSupply[_tokenId] = _maxSupply;
    }

    function setCost(uint256 _newCost) public onlyOwner {
        cost = _newCost;
    }

    function setSaleState(uint256 _newSaleState) public onlyOwner {
        saleState = _newSaleState;
    }

    function withdraw() public onlyOwner {
        (bool success, ) = payable(owner()).call{value: address(this).balance}(
            ""
        );
        require(success);
    }

    function uri(uint256 id) public view override returns (string memory) {
        require(exists(id), "Token id does not exist!");

        return
            bytes(baseURI).length > 0
                ? string(abi.encodePacked(baseURI, id.toString(), ".json"))
                : "";
    }

    function burnToMint(
        BurnMintParams calldata params,
        bytes memory _signature
    ) external {
        require(
            get_signer_burn(params, _signature) == signerAddress,
            "Invalid master sig!"
        );
        require(params.addy == _msgSender(), "Not approved minter!");
        require(
            block.timestamp < params.valid_until_timestamp,
            "Signature Expired!"
        );
        bytes32 msig = keccak256(_signature);
        require(processedNoncesBurn[params.nonce] != msig, "Sig already used!");
        processedNoncesBurn[params.nonce] = msig;

        if (params.ids.length == 1) {
            _burn(msg.sender, params.ids[0], params.amounts[0]);
        } else {
            _burnBatch(msg.sender, params.ids, params.amounts);
        }

        cardContract.mintBatch(msg.sender, params.mintIds, params.mintAmounts);
    }

    // Set royalties info.
    function setDefaultRoyalty(
        address receiver,
        uint96 feeNumerator
    ) public onlyOwner {
        _setDefaultRoyalty(receiver, feeNumerator);
    }

    function deleteDefaultRoyalty() public onlyOwner {
        _deleteDefaultRoyalty();
    }

    // OpenSea royalties.
    function setApprovalForAll(
        address operator,
        bool approved
    ) public override onlyAllowedOperatorApproval(operator) {
        super.setApprovalForAll(operator, approved);
    }

    function safeTransferFrom(
        address from,
        address to,
        uint256 tokenId,
        uint256 amount,
        bytes memory data
    ) public override onlyAllowedOperator(from) {
        super.safeTransferFrom(from, to, tokenId, amount, data);
    }

    function safeBatchTransferFrom(
        address from,
        address to,
        uint256[] memory ids,
        uint256[] memory amounts,
        bytes memory data
    ) public virtual override onlyAllowedOperator(from) {
        super.safeBatchTransferFrom(from, to, ids, amounts, data);
    }

    function supportsInterface(
        bytes4 interfaceId
    ) public view virtual override(ERC1155, ERC2981) returns (bool) {
        return
            ERC1155.supportsInterface(interfaceId) ||
            ERC2981.supportsInterface(interfaceId);
    }
}
