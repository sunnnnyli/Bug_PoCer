pragma solidity ^0.8.13;
import "forge-std/Test.sol";
import "../src/ForceSendVulnerable.sol";
import "../exploits/ForceSendVulnerableExploit.sol";

contract ForceSendVulnerableTest is Test {
    ForceSendVulnerable public target;
    ForceSendVulnerableExploit public exploit;

    function setUp() public {
        target = new ForceSendVulnerable();
        exploit = new ForceSendVulnerableExploit(address(target));
    }

    function testExploit() public {
        // Set up scenario: deposit 6 times
        for (uint i = 0; i < 6; i++) {
            address depositor = address(uint160(i + 1));
            vm.deal(depositor, 1 ether);
            vm.prank(depositor);
            target.deposit{value: 1 ether}();
        }

        // Fund the attacker contract and execute hack
        vm.deal(address(exploit), 10 ether);
        exploit.hack();

        // Verify that the exploit drained the vulnerable contract
        require(address(target).balance == 0, "Exploit not successful");
    }
}
