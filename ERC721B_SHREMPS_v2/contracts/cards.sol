// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./ERC721B2FAEnumLitePausable.sol";
import "@openzeppelin/contracts/utils/Address.sol";
import "@openzeppelin/contracts/utils/Strings.sol";

contract Cards is ERC721B2FAEnumLitePausable {
    using Address for address;
    using Strings for uint256;

    bool public mintState;
    uint256 public maxSupply;
    string public baseURL;

    mapping(address => bool) public minters;

    constructor() ERC721B2FAEnumLitePausable("Shremp Cards", "CARD", 1) {
        setBaseURL("");
        maxSupply = 69420;
        _setDefaultRoyalty(msg.sender, 500);
    }

    fallback() external payable {}

    receive() external payable {}


    function _minty(address addy, uint256 quantity) internal {
        require(quantity > 0, "Can't mint 0 tokens!");
        require(totalSupply() + quantity <= maxSupply, "Max supply exceeded!");
        for (uint256 i = 0; i < quantity; i++) {
            _safeMint(addy, next());
        }
    }

    function mint(address _to, uint256 _numberOfTokens) public {
        require(mintState, "mint is not active");
        require(minters[msg.sender], "Only permissioned addresses can mint.");
        _minty(_to, _numberOfTokens);
    }

    function ownerMint(address _to, uint256 _numberOfTokens) public onlyOwner{
        _minty(_to, _numberOfTokens);
    }
    function tokenURI(uint256 _tokenId)
        public
        view
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

    function _baseURI() internal view returns (string memory) {
        return baseURL;
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

    // OpenSea royalties.
    function setApprovalForAll(address operator, bool approved)
        public
        override(ERC721B, IERC721)
        onlyAllowedOperatorApproval(operator)
    {
        ERC721B.setApprovalForAll(operator, approved);
    }

    function approve(address operator, uint256 tokenId)
        public
        override(ERC721B, IERC721)
        onlyAllowedOperatorApproval(operator)
    {
        ERC721B.approve(operator, tokenId);
    }

    function transferFrom(
        address from,
        address to,
        uint256 tokenId
    )
        public
        override(ERC721B, IERC721)
        onlyAllowedOperator(from)
    {
        ERC721B.transferFrom(from, to, tokenId);
    }

    function safeTransferFrom(
        address from,
        address to,
        uint256 tokenId
    )
        external
        override(ERC721B, IERC721)
        onlyAllowedOperator(from)
    {
        ERC721B.safeTransferFrom(from, to, tokenId, "");
    }

    function safeTransferFrom(
        address from,
        address to,
        uint256 tokenId,
        bytes memory _data
    )
        public
        override(ERC721B, IERC721)
        onlyAllowedOperator(from)
    {
        ERC721B.safeTransferFrom(from, to, tokenId, _data);
    }

}