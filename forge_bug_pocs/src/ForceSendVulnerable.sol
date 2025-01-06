contract ForceSendVulnerable {
    uint256 public targetAmount = 7 ether;
    address public winner;

    // Anyone can deposit 1 Ether and the 7th person to deposit wins all Ether.
    function deposit() public payable {
        require(msg.value == 1 ether, "You can only send 1 Ether");

        uint256 balance = address(this).balance;
        require(balance <= targetAmount, "Game is over");

        // Logic strictly depends on the ETH balance of the contract.
        if (balance == targetAmount) {
            winner = msg.sender;
        }
    }

    function claimReward() public {
        require(msg.sender == winner, "Not winner");

        (bool sent,) = msg.sender.call{value: address(this).balance}("");
        require(sent, "Failed to send Ether");
    }
}