pragma solidity ^0.8.13;

import "forge-std/Test.sol";
import "../src/FrontRunningVulnerable.sol";
import "../exploits/FrontRunningVulnerableExploit.sol";

contract FrontRunningVulnerableTest is Test {
    FrontRunningVulnerable vulnerable;
    FrontRunningVulnerableExploit exploit;

    function setUp() public {
        // Prepare a simple password hash
        bytes32 testHash = keccak256(abi.encodePacked("mySimplePassword"));

        // Deploy the vulnerable contract with some Ether
        vulnerable = new FrontRunningVulnerable{value: 3 ether}(testHash);

        // Set up the exploit with the deployed vulnerable contract
        exploit = new FrontRunningVulnerableExploit(address(vulnerable));
    }

    function testExploit() public {
        // Confirm no winner initially
        assertEq(vulnerable.winner(), address(0), "Winner should be the zero address before exploit");

        // Execute the hack
        exploit.hack();

        // The test should fail if the exploit did not succeed
        require(vulnerable.winner() == address(exploit), "Exploit failed: winner is not set to exploit contract");
    }
}