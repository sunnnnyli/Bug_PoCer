pragma solidity ^0.8.13;

import "forge-std/Test.sol";
import "../src/ForceSendVulnerable.sol";
import "../exploits/ForceSendVulnerableExploit.sol";

contract ForceSendVulnerableTest is Test {
    ForceSendVulnerable vulnerable;
    ForceSendVulnerableExploit exploit;

    function setUp() public {
        vulnerable = new ForceSendVulnerable();
        exploit = new ForceSendVulnerableExploit(payable(address(vulnerable)));
    }

    function testExploit() public {
        // Fund this contract with 10 Ether to use in testing
        vm.deal(address(this), 10 ether);

        // Make 6 deposits of 1 Ether each
        for (uint256 i = 0; i < 6; i++) {
            vulnerable.deposit{value: 1 ether}();
        }

        // Verify no winner is assigned yet
        assertEq(vulnerable.winner(), address(0), "No winner should be set yet");

        // Execute the exploit with 1 more Ether
        exploit.hack{value: 1 ether}();

        // The test should fail if the exploit was not successful
        require(vulnerable.winner() == address(exploit), "Exploit failed: winner is not the exploit contract");
    }
}
