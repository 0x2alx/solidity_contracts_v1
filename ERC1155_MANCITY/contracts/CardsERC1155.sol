// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC1155/ERC1155.sol";
import "@openzeppelin/contracts/token/common/ERC2981.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Strings.sol";
import "@openzeppelin/contracts/token/ERC1155/extensions/ERC1155Burnable.sol";
import "@openzeppelin/contracts/token/ERC1155/extensions/ERC1155Supply.sol";
import "./RevokableDefaultOperatorFilterer.sol";
import "./UpdatableOperatorFilterer.sol";

contract Card1155 is ERC1155, Ownable, ERC2981, RevokableDefaultOperatorFilterer, ERC1155Burnable, ERC1155Supply {

    string public constant name = "CARDS";
    string public constant symbol = "CARD";
    string private baseURI;
    uint256[] public maxSupplies = [0, 166, 285, 284, 216, 168, 351, 78, 59, 355, 66, 122, 139, 181, 25, 169, 89, 285, 293, 290, 205, 52, 226, 233, 64, 107, 381, 102, 388, 318, 315, 238, 211, 375, 82, 384, 226, 320, 131, 170, 219, 37, 316, 259, 219, 247, 275, 365, 145, 362, 244, 371, 264, 215, 374, 197, 155, 21, 366, 137, 134, 197, 246, 310, 198, 102, 227, 54, 267, 267, 220, 30, 178, 397, 367, 391, 203, 266, 72, 363, 236, 297, 279, 394, 323, 380, 237, 389, 145, 41, 20, 190, 51, 272, 396, 22, 324, 82, 373, 387, 232, 374, 301, 328, 191, 144, 344, 288, 26, 211, 163, 248, 361, 105, 302, 388, 194, 348, 27, 61, 369, 103, 48, 194, 363, 346, 353, 193, 346, 191, 240, 160, 286, 57, 121, 91, 266, 287, 159, 343, 266, 202, 82, 100, 136, 386, 241, 286, 308, 150, 143, 261, 140, 163, 107, 43, 53, 163, 223, 50, 166, 290, 185, 170, 301, 106, 198, 179, 226, 131, 289, 166, 126, 232, 42, 98, 293, 133, 73, 98, 121, 147, 119, 79, 233, 200, 285, 115, 209, 182, 380, 80, 360, 210, 260, 228, 287, 391, 260, 236, 364, 169, 276, 228, 359, 230, 280, 306, 114, 49, 281, 76, 143, 259, 89, 182, 216, 371, 98, 394, 167, 151, 101, 296, 20, 35, 377, 99, 251, 307, 143, 222, 80, 344, 62, 338, 396, 316, 370, 231, 289, 117, 52, 162, 119, 124, 381, 168, 304, 201, 29, 112, 22, 363, 253, 130, 61, 387, 155, 217, 45, 383, 105, 33, 281, 37, 374, 68, 330, 140, 31, 188, 235, 399, 254, 384, 200, 387, 35, 99, 78, 26, 281, 235, 130, 96, 374, 313, 167, 379, 38, 263, 304, 369, 157, 107, 228, 24, 396, 157, 38, 135, 92];

    uint256 public highestTokenId;

    bool public mintState;

    mapping(address => bool) public minters;

    constructor() ERC1155("") {
        _setDefaultRoyalty(msg.sender, 500);    
        highestTokenId=302;
    }

    function setBaseURI(string calldata _baseURI) external onlyOwner {
        baseURI = _baseURI;
    }

    function mint(address _to, uint256 _id, uint256 _amount) public {
        require(mintState, "mint is not active");
        require(minters[msg.sender], "Only permissioned addresses can mint.");
        require(totalSupply(_id)+_amount<=maxSupplies[_id],"Max supply exceeded!");
        _mint(_to, _id, _amount, "");
    }

    function mintBatch(address _to, uint256[] calldata _ids, uint256[] calldata _amounts) public {
        require(mintState, "mint is not active");
        require(minters[msg.sender], "Only permissioned addresses can mint.");
        for (uint256 ind=0;ind<_ids.length;ind++) {
            require(totalSupply(_ids[ind])+_amounts[ind]<=maxSupplies[_ids[ind]],"Max supply exceeded!");
        }
        _mintBatch(_to, _ids, _amounts, "");
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
    function ownerMint(address _receiver, uint256 _id, uint256 _amount) public onlyOwner {
        require(totalSupply(_id)+_amount<=maxSupplies[_id],"Max supply exceeded!");
        _mint(_receiver, _id, _amount, "");
    }
    function _beforeTokenTransfer(address operator, address from, address to, uint256[] memory ids, uint256[] memory amounts, bytes memory data)
        internal
        override(ERC1155, ERC1155Supply)
    {
        super._beforeTokenTransfer(operator, from, to, ids, amounts, data);
    }

    function flipMintState() public onlyOwner {
        mintState = !mintState;
    }

    function flipMinter(address _minter) public onlyOwner {
        minters[_minter] = !minters[_minter];
    }

    function setHighestId(uint256 _highest_id) external onlyOwner {
        highestTokenId = _highest_id;
    }

    function ownedTokens(address _address) public view returns(uint256[] memory, uint256[] memory) {
        uint256 _total_cards_owned = 0;
        for (uint256 tid = 1; tid <=highestTokenId; tid++) {
            if (balanceOf(_address, tid) > 0) {
                _total_cards_owned = _total_cards_owned + 1;
            }
        }

        uint256[] memory _tokens = new uint256[](_total_cards_owned);
        uint256[] memory _balances = new uint256[](_total_cards_owned);
        uint256 _array_index = 0;
        for (uint256 tid = 1; tid <=highestTokenId; tid++) {
            if (balanceOf(_address, tid) > 0) {
                _tokens[_array_index] = tid;
                _balances[_array_index] = balanceOf(_address,tid);
                _array_index = _array_index + 1;
            }
        }
        return (_tokens, _balances);
    }

    function currentTotalSupplies() public view returns(uint256[] memory) {
        uint256[] memory _curr_supplies = new uint256[](highestTokenId+1); 
        for (uint256 tid = 1; tid<=highestTokenId; tid++) {
            _curr_supplies[tid] = totalSupply(tid);
        }        
        return _curr_supplies;
    }

    function withdraw() public onlyOwner {
        (bool success, ) = payable(owner()).call{value: address(this).balance}('');
        require(success);
    }

    function uri(uint256 id) public view override returns (string memory) {
        require(exists(id), "Invalid token id!");
        
        return
            bytes(baseURI).length > 0
                ? string(
                    abi.encodePacked(baseURI, Strings.toString(id), ".json")
                )
                : "";
    }

    // Set royalties info.
    function setDefaultRoyalty(address receiver, uint96 feeNumerator) public onlyOwner {
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
        return ERC1155.supportsInterface(interfaceId) || ERC2981.supportsInterface(interfaceId);
    }
}