// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "erc721a/contracts/extensions/ERC721AQueryable.sol";
import "@openzeppelin/contracts/token/common/ERC2981.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Strings.sol";
import "operator-filter-registry/src/DefaultOperatorFilterer.sol";
import "./RevokableDefaultOperatorFilterer.sol";

contract Cards is ERC721AQueryable, ERC2981, RevokableDefaultOperatorFilterer, Ownable {

    bool public mintState;
    uint256 public maxSupply;
    string public baseURL;

    mapping(address => bool) public minters;

    constructor() ERC721A("Cards", "CARD") {
        setBaseURL("");
        maxSupply = 69420;
        _setDefaultRoyalty(msg.sender, 500);
    }

    function mint(address _to, uint256 _numberOfTokens) external canMint(_numberOfTokens) {
        require(mintState, "mint is not active");
        require(minters[msg.sender], "Only permissioned addresses can mint.");

        _safeMint(_to, _numberOfTokens);
    }

    function ownerMint(address _to, uint256 _numberOfTokens) external onlyOwner{
        _safeMint(_to, _numberOfTokens);
    }

    function tokenURI(uint256 _tokenId)
        public
        view
        override(IERC721A, ERC721A)
        returns (string memory)
    {
        require(
        _exists(_tokenId),
        "ERC721Metadata: URI query for nonexistent token"
        );

        string memory currentBaseURI = _baseURI();
        return
        bytes(currentBaseURI).length > 0
            ? string(
            abi.encodePacked(currentBaseURI, Strings.toString(_tokenId), ".json")
            )
            : "";
    }

    function _baseURI() internal view override returns (string memory) {
        return baseURL;
    }

    function _startTokenId() internal view virtual override returns (uint256) {
        return 1;
    }

    function setBaseURL(string memory _baseURL) public onlyOwner {
        baseURL = _baseURL;
    }

    function flipMintState() public onlyOwner {
        mintState = !mintState;
    }

    function setMaxSupply(uint256 _newMaxSupply) public onlyOwner {
        require(_newMaxSupply < maxSupply, "max supply cannot be more than current");
        maxSupply = _newMaxSupply;
    }

    function flipMinter(address _minter) public onlyOwner {
        minters[_minter] = !minters[_minter];
    }

    function withdraw() public onlyOwner {
        (bool os, ) = payable(owner()).call{value: address(this).balance}("");
        require(os);
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
    ) public override(IERC721A, ERC721A) onlyAllowedOperatorApproval(operator) {
        super.setApprovalForAll(operator, approved);
    }

    function approve(
        address operator, 
        uint256 tokenId
    ) public payable override(IERC721A, ERC721A) onlyAllowedOperatorApproval(operator) {
        super.approve(operator, tokenId);
    }

    function transferFrom(
        address from, 
        address to, 
        uint256 tokenId
    ) public payable override(IERC721A, ERC721A) onlyAllowedOperator(from) {
        super.transferFrom(from, to, tokenId);
    }

    function safeTransferFrom(
        address from, 
        address to, 
        uint256 tokenId
    ) public payable override(IERC721A, ERC721A) onlyAllowedOperator(from) {
        super.safeTransferFrom(from, to, tokenId);
    }

    function safeTransferFrom(
        address from, 
        address to, 
        uint256 tokenId, 
        bytes memory data
    ) public payable override(IERC721A, ERC721A) onlyAllowedOperator(from) {
        super.safeTransferFrom(from, to, tokenId, data);
    }

    function supportsInterface(
        bytes4 interfaceId
    ) public view virtual override(IERC721A, ERC721A, ERC2981) returns (bool){
        return ERC721A.supportsInterface(interfaceId) || ERC2981.supportsInterface(interfaceId);
    }

}