pragma solidity ^0.8.27;

import "forge-std/Test.sol";
import "../src/FrontRunningVulnerable.sol";
import "../exploits/FrontRunningVulnerableExploit.sol";

contract FrontRunningVulnerableTest is Test {
    FrontRunningVulnerable internal vulnerable;
    FrontRunningVulnerableExploit internal exploit;

    function setUp() public {
        // Deploy vulnerable contract with some Ether and a known password hash.
        vm.deal(address(this), 5 ether);
        bytes32 hash = keccak256(abi.encodePacked("secret"));
        vulnerable = new FrontRunningVulnerable{value: 5 ether}(hash);

        // Set up the exploit contract.
        exploit = new FrontRunningVulnerableExploit(payable(address(vulnerable)));
    }

    function testExploit() public {
        // Execute the exploit.
        exploit.hack();

        // Verify exploit success by checking on-chain state.
        // Here, ensuring the exploit has become the winner.
        require(vulnerable.winner() == address(exploit), "Exploit not successful");
        require(address(vulnerable).balance == 0, "Vulnerable contract not drained");
    }
}
