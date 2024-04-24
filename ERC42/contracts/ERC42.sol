// SPDX-License-Identifier: MIT
// OpenZeppelin Contracts (last updated v4.7.0) (token/ERC1155/ERC1155.sol)

pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/IERC20Metadata.sol";
import "@openzeppelin/contracts/token/ERC1155/IERC1155.sol";
import "@openzeppelin/contracts/token/ERC1155/IERC1155Receiver.sol";
import "@openzeppelin/contracts/token/ERC1155/extensions/IERC1155MetadataURI.sol";
import "@openzeppelin/contracts/utils/Address.sol";
import "@openzeppelin/contracts/utils/Context.sol";
import "@openzeppelin/contracts/utils/Strings.sol";
import "@openzeppelin/contracts/utils/introspection/ERC165.sol";
import "@openzeppelin/contracts/token/common/ERC2981.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/cryptography/MerkleProof.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract ERC42 is
    Context,
    ERC165,
    ERC2981,
    IERC1155,
    IERC1155MetadataURI,
    IERC20,
    ReentrancyGuard,
    Ownable
{
    using MerkleProof for bytes32[];
    using Address for address;
    using Strings for uint256;

    //ERC-1155 VARS
    struct SUPREMEBEING {
        address bag_owner;
        uint256 bag_balance;
        uint256 last_farmed_timestamp;
        uint256 last_filling_timestamp;
        uint256 last_withdrawal_timestamp;
        uint256 mint_timestamp;
    }
    address internal _creator;
    mapping(address => uint256) public _presale_mints;
    mapping(address => uint256) public _public_mints;
    mapping(address => uint256) public _phase_two_mints;
    mapping(address => mapping(address => bool)) private _operatorApprovals;
    mapping(uint256 => SUPREMEBEING) _SB_NFTS;
    bytes32 private merkleRoot = 0;

    uint256 public constant MAX_MINTS_PER_WALLET = 3;
    uint256 public constant PRICE_PRESALE_MINT = 0.0242 ether;
    uint256 public constant PRICE_PUBLIC_MINT = 0.042 ether;
    uint256 public constant MAX_NFTS_PHASE_ONE = 2442;
    uint256 public constant MAX_NFTS_PER_PHASE = 420;
    uint256 public constant INITIAL_NFT_BAGS_TOKEN = 25000000000 * (10 ^ 18);

    uint256 public _last_phase_one_mint_tstamp;
    uint256 public _contract_creation_timestamp;
    uint256 private _bagsReserve;
    uint256 private next_bag_id = 1;
    string private _uri;

    //FORTY TWO FARMING
    uint256 private constant FARMER_GRACE_DAYS = 3;
    uint256 private constant FARMING_MULTIPLIER_NUM = 420;
    uint256 private constant FARMING_MULTIPLIER_DEN = 100000;

    //BAG FILLING WINDOW
    uint256 public constant EMPTY_BAG_MAX_DEPOSIT = 10000000000 * (10 ^ 18);
    uint256 public constant FILLIN_BAG_MAX_RATIO_NUM = 24000;
    uint256 public constant FILLIN_BAG_MAX_RATIO_DEN = 100000;
    event FillBag(
        address indexed _from_wallet,
        uint256 to_token_id,
        uint256 amount
    );
    event EmptyBag(
        address indexed _from_wallet,
        uint256 to_token_id,
        uint256 amount
    );
    event FORTYTWOTOKENBURN(address from, uint256 amount);
    event FORTYTWOTOKENRESERVEBURN(uint256 from_token_id, uint256 amount);

    //EMPTYING WINDOW
    uint256 public constant WEEK_ONE_EMPTY_BAG_TOKEN_ID_MAX = 600;
    uint256 public constant WEEK_TWO_EMPTY_BAG_TOKEN_ID_MAX = 1200;
    uint256 public constant WEEK_THREE_EMPTY_BAG_TOKEN_ID_MAX = 1800;
    uint256 public constant WEEK_FOUR_EMPTY_BAG_TOKEN_ID_MAX = 2400;
    uint256 public constant TRANSFER_BURN_FEE_NUM = 420;
    uint256 public constant TRANSFER_BURN_FEE_DEM = 100000;

    //ERC-20 VARS
    uint256 constant TOTAL_MAX_ERC20TOKENS = 424242424242424242424242424242424;
    mapping(address => uint256) private _balances_token;
    mapping(address => mapping(address => uint256)) private _allowances;
    uint256 private _totalSupplyCirculation;
    uint256 private _totalSupplyBags;
    string private constant _name = "FORTYTWO";
    string private constant _symbol = "FORTYTWO";

    constructor() {
        _mint20(
            msg.sender,
            TOTAL_MAX_ERC20TOKENS / 2,
            TOTAL_MAX_ERC20TOKENS / 2
        );
        _creator = msg.sender;
        _contract_creation_timestamp = block.timestamp;
    }

    function supportsInterface(
        bytes4 interfaceId
    ) public view virtual override(ERC165, ERC2981, IERC165) returns (bool) {
        return
            interfaceId == type(IERC1155).interfaceId ||
            interfaceId == type(IERC1155MetadataURI).interfaceId ||
            interfaceId == type(IERC2981).interfaceId ||
            super.supportsInterface(interfaceId);
    }

    function uri(uint256) public view virtual override returns (string memory) {
        return _uri;
    }

    function balanceOf(
        address account,
        uint256 id
    ) public view virtual override returns (uint256) {
        require(
            account != address(0),
            "ERC1155: address zero is not a valid owner"
        );
        if (account == _SB_NFTS[id].bag_owner) {
            return 1;
        }
        return 0;
    }

    modifier onlyCreator() {
        require(_msgSender() == _creator, "!Authorized");
        _;
    }

    function balanceOfBatch(
        address[] memory accounts,
        uint256[] memory ids
    ) public view virtual override returns (uint256[] memory) {
        require(
            accounts.length == ids.length,
            "ERC1155: accounts and ids length mismatch"
        );

        uint256[] memory batchBalances = new uint256[](accounts.length);

        for (uint256 i = 0; i < accounts.length; ++i) {
            batchBalances[i] = balanceOf(accounts[i], ids[i]);
        }

        return batchBalances;
    }

    function setApprovalForAll(
        address operator,
        bool approved
    ) public virtual override {
        _setApprovalForAll(_msgSender(), operator, approved);
    }

    function isApprovedForAll(
        address account,
        address operator
    ) public view virtual override returns (bool) {
        return _operatorApprovals[account][operator];
    }

    function safeTransferFrom(
        address from,
        address to,
        uint256 id,
        uint256 amount,
        bytes memory data
    ) public virtual override {
        require(
            from == _msgSender() || isApprovedForAll(from, _msgSender()),
            "ERC1155: caller is not token owner nor approved"
        );
        _safeTransferFrom(from, to, id, amount, data);
    }

    function safeBatchTransferFrom(
        address from,
        address to,
        uint256[] memory ids,
        uint256[] memory amounts,
        bytes memory data
    ) public virtual override {
        require(
            from == _msgSender() || isApprovedForAll(from, _msgSender()),
            "ERC1155: caller is not token owner nor approved"
        );
        _safeBatchTransferFrom(from, to, ids, amounts, data);
    }

    function farm_fortytwo(uint256 token_id) internal {
        if (_SB_NFTS[token_id].bag_balance > 0) {
            uint256 nb_days_since_transfer = block.timestamp -
                _SB_NFTS[token_id].last_farmed_timestamp;
            uint256 tokens_to_farm = 0;
            for (
                uint256 day = 0;
                day < (nb_days_since_transfer - FARMER_GRACE_DAYS);
                day++
            ) {
                tokens_to_farm =
                    (_SB_NFTS[token_id].bag_balance * FARMING_MULTIPLIER_NUM) /
                    FARMING_MULTIPLIER_DEN;
                _bagsReserve -= tokens_to_farm;
                _SB_NFTS[token_id].bag_balance += tokens_to_farm;
            }
            _SB_NFTS[token_id].last_farmed_timestamp = block.timestamp;
        }
    }

    function empty_bag(
        uint256 _withdraw_amount,
        uint256 token_id
    ) external nonReentrant {
        uint256 nb_days_since_mint = (block.timestamp -
            _SB_NFTS[token_id].mint_timestamp) / 86400;
        uint256 nb_days_since_creation = (block.timestamp -
            _contract_creation_timestamp) / 86400;
        require(nb_days_since_mint > 41, "Vesting period not over!");
        require(nb_days_since_creation % 7 == 0, "Filling window closed!");
        require(
            _SB_NFTS[token_id].last_withdrawal_timestamp <
                block.timestamp - 86400,
            "Already emptied your bag this window!"
        );
        require(
            _SB_NFTS[token_id].bag_owner == _msgSender(),
            "ERC1155: caller is not token owner nor approved"
        );
        farm_fortytwo(token_id);
        require(
            _SB_NFTS[token_id].bag_balance >= _withdraw_amount,
            "Not enough FORTYTWO tokens!"
        );

        unchecked {
            _SB_NFTS[token_id].bag_balance -= _withdraw_amount;
            _totalSupplyBags -= _withdraw_amount;
            _totalSupplyCirculation += _withdraw_amount;
            _balances_token[_msgSender()] += _withdraw_amount;
        }
        _SB_NFTS[token_id].last_withdrawal_timestamp = block.timestamp;
        emit EmptyBag(_msgSender(), token_id, _withdraw_amount);
    }

    function fill_bag(
        uint256 _extra_amount_fortytwo_tokens,
        uint256 token_id
    ) external nonReentrant {
        uint256 nb_days_since_creation = (block.timestamp -
            _contract_creation_timestamp) / 86400;
        require(nb_days_since_creation % 7 == 0, "Filling window closed!");
        require(
            _SB_NFTS[token_id].last_filling_timestamp < block.timestamp - 86400,
            "Already filled this window!"
        );
        require(
            _SB_NFTS[token_id].bag_owner == _msgSender() ||
                isApprovedForAll(_SB_NFTS[token_id].bag_owner, _msgSender()),
            "ERC1155: caller is not token owner nor approved"
        );
        require(
            balanceOf(_msgSender()) >= _extra_amount_fortytwo_tokens,
            "Not enough FORTYTWO tokens!"
        );
        farm_fortytwo(token_id);
        uint256 _max_extra_tokens_allowed = EMPTY_BAG_MAX_DEPOSIT;
        if (_SB_NFTS[token_id].bag_balance > ((100 * 10) ^ 18)) {
            _max_extra_tokens_allowed =
                (_SB_NFTS[token_id].bag_balance * FILLIN_BAG_MAX_RATIO_NUM) /
                FILLIN_BAG_MAX_RATIO_DEN;
        }
        require(
            _extra_amount_fortytwo_tokens <= _max_extra_tokens_allowed,
            "Can't fill that many tokens!"
        );
        unchecked {
            _balances_token[_msgSender()] -= _extra_amount_fortytwo_tokens;
            _totalSupplyCirculation -= _extra_amount_fortytwo_tokens;
            _totalSupplyBags += _extra_amount_fortytwo_tokens;
            _SB_NFTS[token_id].bag_balance += _extra_amount_fortytwo_tokens;
        }
        _SB_NFTS[token_id].last_filling_timestamp = block.timestamp;
        emit FillBag(_msgSender(), token_id, _extra_amount_fortytwo_tokens);
    }

    function _safeTransferFrom(
        address from,
        address to,
        uint256 id,
        uint256 amount,
        bytes memory data
    ) internal virtual {
        require(to != address(0), "ERC1155: transfer to the zero address");

        address operator = _msgSender();
        uint256[] memory ids = _asSingletonArray(id);
        uint256[] memory amounts = _asSingletonArray(1);

        require(from == _SB_NFTS[id].bag_owner, "Transfering from wrong owner");
        _SB_NFTS[id].bag_owner = to;
        farm_fortytwo(id);

        emit TransferSingle(operator, from, to, id, 1);

        _doSafeTransferAcceptanceCheck(operator, from, to, id, 1, data);
    }

    function _safeBatchTransferFrom(
        address from,
        address to,
        uint256[] memory ids,
        uint256[] memory amounts,
        bytes memory data
    ) internal virtual {
        require(to != address(0), "ERC1155: transfer to the zero address");

        address operator = _msgSender();

        for (uint256 i = 0; i < ids.length; ++i) {
            require(
                from == _SB_NFTS[ids[i]].bag_owner,
                "Transfering from wrong owner"
            );
            _SB_NFTS[ids[i]].bag_owner = to;
            farm_fortytwo(ids[i]);
        }

        uint256[] memory array_amount = new uint256[](ids.length);
        for (uint256 indd = 0; indd < ids.length; indd++) {
            array_amount[indd] = 1;
        }

        emit TransferBatch(operator, from, to, ids, array_amount);
        _doSafeBatchTransferAcceptanceCheck(
            operator,
            from,
            to,
            ids,
            array_amount,
            data
        );
    }

    function _setURI(string memory newuri) internal virtual {
        _uri = newuri;
    }

    function mintSupremeBeingNextPhase(
        uint256 quantity
    ) external payable nonReentrant {
        uint256 nb_weeks_since_last_mint = (block.timestamp -
            _last_phase_one_mint_tstamp) / (86400 * 7);
        require(nb_weeks_since_last_mint % 12 == 0, "Minting window closed!");
        require(
            next_bag_id + quantity <=
                MAX_NFTS_PHASE_ONE +
                    (MAX_NFTS_PER_PHASE * (nb_weeks_since_last_mint / 12)),
            "Phase mint over!"
        );
        uint256 mint_price_per = ((INITIAL_NFT_BAGS_TOKEN * 840) / 1000) +
            ((nb_weeks_since_last_mint / 12) * (INITIAL_NFT_BAGS_TOKEN / 10));
        require(
            balanceOf(_msgSender()) >= mint_price_per * quantity,
            "Not enough FORTYTWO tokens to mint that many!"
        );
        unchecked {
            _balances_token[_msgSender()] =
                _balances_token[_msgSender()] -
                (mint_price_per * quantity);
            _bagsReserve += (mint_price_per * quantity);
            _totalSupplyCirculation -= (mint_price_per * quantity);
            _totalSupplyBags += (mint_price_per * quantity);
        }

        require(
            quantity + _phase_two_mints[_msgSender()] <= MAX_MINTS_PER_WALLET,
            "Too many!"
        );
        _phase_two_mints[_msgSender()] += quantity;
        for (uint256 qty = 0; qty < quantity; qty++) {
            _mint(_msgSender(), (INITIAL_NFT_BAGS_TOKEN * 420) / 1000);
        }
    }

    function mintSupremeBeing(
        bytes32[] memory proof,
        uint256 quantity
    ) external payable nonReentrant {
        bool valid_merkle = isvalidMerkleProof(proof);
        require(
            next_bag_id + quantity <= MAX_NFTS_PHASE_ONE,
            "Phase one mint over!"
        );
        if (next_bag_id <= 420) {
            require(valid_merkle, "You are not authorized to mint!");
        }
        uint256 _price_per = PRICE_PUBLIC_MINT;
        if (valid_merkle) {
            _price_per = PRICE_PRESALE_MINT;
        }
        if (_price_per == PRICE_PUBLIC_MINT) {
            require(
                quantity + _public_mints[_msgSender()] <= MAX_MINTS_PER_WALLET,
                "Too many!"
            );
            _public_mints[_msgSender()] += quantity;
        } else {
            require(
                quantity + _presale_mints[_msgSender()] <= MAX_MINTS_PER_WALLET,
                "Too many!"
            );
            _presale_mints[_msgSender()] += quantity;
        }
        require(msg.value == quantity * _price_per, "Invalid amount of ETH!");
        for (uint256 qty = 0; qty < quantity; qty++) {
            _mint(_msgSender(), INITIAL_NFT_BAGS_TOKEN);
        }
        if (next_bag_id >= MAX_NFTS_PHASE_ONE - 10) {
            _last_phase_one_mint_tstamp = block.timestamp;
        }
    }

    function get_next_bag_id() external returns (uint256) {
        return next_bag_id;
    }

    function _mint(address to, uint256 initial_reserve) internal virtual {
        require(to != address(0), "ERC1155: mint to the zero address");

        address operator = _msgSender();
        uint256[] memory ids = _asSingletonArray(next_bag_id);
        uint256[] memory amounts = _asSingletonArray(1);

        _bagsReserve -= initial_reserve;
        _SB_NFTS[next_bag_id] = SUPREMEBEING(
            to,
            initial_reserve,
            block.timestamp,
            block.timestamp,
            block.timestamp,
            block.timestamp
        );

        emit TransferSingle(operator, address(0), to, next_bag_id, 1);

        _doSafeTransferAcceptanceCheck(
            operator,
            address(0),
            to,
            next_bag_id,
            1,
            ""
        );
        next_bag_id += 1;
    }

    //TODO
    function burnSUPREMEBEING(uint256 token_id) external nonReentrant {
        require(
            _SB_NFTS[token_id].bag_owner == _msgSender() ||
                isApprovedForAll(_SB_NFTS[token_id].bag_owner, _msgSender()),
            "ERC1155: caller is not token owner nor approved"
        );

        address operator = _msgSender();
        uint256[] memory ids = _asSingletonArray(token_id);
        uint256[] memory amounts = _asSingletonArray(1);

        farm_fortytwo(token_id);
        _SB_NFTS[token_id].bag_owner = address(0);

        if (_SB_NFTS[token_id].bag_balance > 1 * (10 ^ 18)) {
            emit FORTYTWOTOKENRESERVEBURN(
                token_id,
                _SB_NFTS[token_id].bag_balance
            );
            _totalSupplyBags -= _SB_NFTS[token_id].bag_balance;
        }
        emit TransferSingle(
            operator,
            _SB_NFTS[token_id].bag_owner,
            address(0),
            token_id,
            1
        );
    }

    function withdraw() external onlyCreator {
        require(_creator != address(0), "Don't send ETH to null address");
        uint256 contract_balance = address(this).balance;

        address payable w_addy = payable(_creator);

        (bool success, ) = w_addy.call{value: (contract_balance)}("");
        require(success, "Withdrawal failed!");
    }

    function getMerkleRoot() public view onlyCreator returns (bytes32) {
        return merkleRoot;
    }

    function setMerkleRoot(bytes32 mRoot) external onlyCreator {
        merkleRoot = mRoot;
    }

    function isvalidMerkleProof(
        bytes32[] memory proof
    ) public view returns (bool) {
        if (merkleRoot == 0) {
            return false;
        }
        bool proof_valid = proof.verify(
            merkleRoot,
            keccak256(abi.encodePacked(msg.sender))
        );
        return proof_valid;
    }

    function _setApprovalForAll(
        address owner,
        address operator,
        bool approved
    ) internal virtual {
        require(owner != operator, "ERC1155: setting approval status for self");
        _operatorApprovals[owner][operator] = approved;
        emit ApprovalForAll(owner, operator, approved);
    }

    function _doSafeTransferAcceptanceCheck(
        address operator,
        address from,
        address to,
        uint256 id,
        uint256 amount,
        bytes memory data
    ) private {
        if (to.isContract()) {
            try
                IERC1155Receiver(to).onERC1155Received(
                    operator,
                    from,
                    id,
                    amount,
                    data
                )
            returns (bytes4 response) {
                if (response != IERC1155Receiver.onERC1155Received.selector) {
                    revert("ERC1155: ERC1155Receiver rejected tokens");
                }
            } catch Error(string memory reason) {
                revert(reason);
            } catch {
                revert("ERC1155: transfer to non ERC1155Receiver implementer");
            }
        }
    }

    function _doSafeBatchTransferAcceptanceCheck(
        address operator,
        address from,
        address to,
        uint256[] memory ids,
        uint256[] memory amounts,
        bytes memory data
    ) private {
        if (to.isContract()) {
            try
                IERC1155Receiver(to).onERC1155BatchReceived(
                    operator,
                    from,
                    ids,
                    amounts,
                    data
                )
            returns (bytes4 response) {
                if (
                    response != IERC1155Receiver.onERC1155BatchReceived.selector
                ) {
                    revert("ERC1155: ERC1155Receiver rejected tokens");
                }
            } catch Error(string memory reason) {
                revert(reason);
            } catch {
                revert("ERC1155: transfer to non ERC1155Receiver implementer");
            }
        }
    }

    function _asSingletonArray(
        uint256 element
    ) private pure returns (uint256[] memory) {
        uint256[] memory array = new uint256[](1);
        array[0] = element;

        return array;
    }

    //ERC-20 TOKEN PART
    //ERC-20 TOKEN PART
    //ERC-20 TOKEN PART
    //ERC-20 TOKEN PART
    //ERC-20 TOKEN PART
    //ERC-20 TOKEN PART
    //ERC-20 TOKEN PART
    //ERC-20 TOKEN PART
    //ERC-20 TOKEN PART
    //ERC-20 TOKEN PART
    //ERC-20 TOKEN PART
    //ERC-20 TOKEN PART
    //ERC-20 TOKEN PART
    //ERC-20 TOKEN PART
    //ERC-20 TOKEN PART
    //ERC-20 TOKEN PART
    //ERC-20 TOKEN PART
    //ERC-20 TOKEN PART
    //ERC-20 TOKEN PART
    //ERC-20 TOKEN PART
    //ERC-20 TOKEN PART
    function name() public view virtual returns (string memory) {
        return _name;
    }

    function symbol() public view virtual returns (string memory) {
        return _symbol;
    }

    function decimals() public view virtual returns (uint8) {
        return 0;
    }

    function totalSupply() public view virtual override returns (uint256) {
        return _totalSupplyCirculation + _totalSupplyBags;
    }

    function get_bagsReserve() external returns (uint256) {
        return _bagsReserve;
    }

    function get_totalSupplyCirculation() external returns (uint256) {
        return _totalSupplyCirculation;
    }

    function get_totalSupplyBags() external returns (uint256) {
        return _totalSupplyBags;
    }

    function balanceOf(
        address account
    ) public view virtual override returns (uint256) {
        return _balances_token[account];
    }

    function transfer(
        address to,
        uint256 amount
    ) public virtual override returns (bool) {
        address owner = _msgSender();
        _transfer(owner, to, amount);
        return true;
    }

    function allowance(
        address owner,
        address spender
    ) public view virtual override returns (uint256) {
        return _allowances[owner][spender];
    }

    function approve(
        address spender,
        uint256 amount
    ) public virtual override returns (bool) {
        address owner = _msgSender();
        _approve(owner, spender, amount);
        return true;
    }

    function transferFrom(
        address from,
        address to,
        uint256 amount
    ) public virtual override returns (bool) {
        address spender = _msgSender();
        _spendAllowance(from, spender, amount);
        _transfer(from, to, amount);
        return true;
    }

    function increaseAllowance(
        address spender,
        uint256 addedValue
    ) public virtual returns (bool) {
        address owner = _msgSender();
        _approve(owner, spender, allowance(owner, spender) + addedValue);
        return true;
    }

    function decreaseAllowance(
        address spender,
        uint256 subtractedValue
    ) public virtual returns (bool) {
        address owner = _msgSender();
        uint256 currentAllowance = allowance(owner, spender);
        require(
            currentAllowance >= subtractedValue,
            "ERC20: decreased allowance below zero"
        );
        unchecked {
            _approve(owner, spender, currentAllowance - subtractedValue);
        }

        return true;
    }

    function _transfer(
        address from,
        address to,
        uint256 amount
    ) internal virtual {
        require(from != address(0), "ERC20: transfer from the zero address");
        require(to != address(0), "ERC20: transfer to the zero address");

        uint256 burn_fee = (amount * TRANSFER_BURN_FEE_NUM) /
            TRANSFER_BURN_FEE_DEM;
        uint256 fromBalance = _balances_token[from];
        require(
            fromBalance >= amount,
            "ERC20: transfer amount exceeds balance"
        );
        unchecked {
            _balances_token[from] = fromBalance - amount;
            _balances_token[to] = _balances_token[to] + amount - burn_fee;
            _bagsReserve += burn_fee / 2;
            _totalSupplyBags += burn_fee / 2;
            _totalSupplyCirculation -= burn_fee;
        }

        emit Transfer(from, to, amount);
    }

    function _mint20(
        address account,
        uint256 amount,
        uint256 bagsReserve
    ) internal virtual {
        require(account != address(0), "ERC20: mint to the zero address");

        _bagsReserve = bagsReserve;
        _totalSupplyBags = bagsReserve;
        _totalSupplyCirculation = amount;
        unchecked {
            _balances_token[account] += amount;
        }
        emit Transfer(address(0), account, amount);
    }

    function burnFORTYTWO(address account, uint256 amount) external {
        if (account != _msgSender()) {
            _spendAllowance(account, _msgSender(), amount);
        }
        require(account != address(0), "ERC20: burn from the zero address");

        uint256 accountBalance = _balances_token[account];
        require(accountBalance >= amount, "ERC20: burn amount exceeds balance");
        unchecked {
            _balances_token[account] = accountBalance - amount;
            _totalSupplyCirculation -= amount;
        }
        emit FORTYTWOTOKENBURN(account, amount);
        emit Transfer(account, address(0), amount);
    }

    function _approve(
        address owner,
        address spender,
        uint256 amount
    ) internal virtual {
        require(owner != address(0), "ERC20: approve from the zero address");
        require(spender != address(0), "ERC20: approve to the zero address");

        _allowances[owner][spender] = amount;
        emit Approval(owner, spender, amount);
    }

    function _spendAllowance(
        address owner,
        address spender,
        uint256 amount
    ) internal virtual {
        uint256 currentAllowance = allowance(owner, spender);
        if (currentAllowance != type(uint256).max) {
            require(
                currentAllowance >= amount,
                "ERC20: insufficient allowance"
            );
            unchecked {
                _approve(owner, spender, currentAllowance - amount);
            }
        }
    }
}
