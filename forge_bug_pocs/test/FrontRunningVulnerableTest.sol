pragma solidity ^0.8.13;
import "forge-std/Test.sol";
import "../src/FrontRunningVulnerable.sol";
import "../exploits/FrontRunningVulnerableExploit.sol";

contract FrontRunningVulnerableTest is Test {
    FrontRunningVulnerable public target;
    FrontRunningVulnerableExploit public exploit;

    function setUp() public {
        // Deploy the vulnerable contract with 5 Ether and a placeholder password hash
        bytes32 testHash = keccak256(abi.encodePacked("someRandomPassword"));
        target = new FrontRunningVulnerable{value: 5 ether}(testHash);

        // Set up attacker contract (already written in the exploits folder)
        exploit = new FrontRunningVulnerableExploit(address(target));
    }

    function testExploit() public {
        // Call the exploit
        vm.deal(address(exploit), 1 ether);
        exploit.hack();

        // Verify that the exploit succeeded by checking the winner and contract balance
        require(target.winner() == address(exploit), "Exploit not successful: winner not set to exploit");
        require(address(target).balance == 0, "Exploit not successful: contract still holds funds");
    }
}
