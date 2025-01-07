pragma solidity 0.8.18;

import "forge-std/Test.sol";
import "../src/RecapitalizationModule.sol";
import "../exploits/RecapitalizationModuleExploit.sol";

contract RecapitalizationModuleExploitTest is Test {
    RecapitalizationModule internal recap;
    RecapitalizationModuleExploit internal exploit;

    address internal attacker = address(0xBEEF);

    function setUp() public {
        // Deploy the vulnerable contract
        recap = new RecapitalizationModule(address(0x1234));

        // Deploy the exploit contract, passing the vulnerable contract and attacker
        exploit = new RecapitalizationModuleExploit(address(recap), attacker);
    }

    function testExploit() public {
        // Call the exploit
        exploit.hack();

        // Verify the exploit by asserting a direct on-chain change.
        // For example, here we check if lastClaimedWindowId is forcibly set to 9999
        // which proves the exploit triggered a state change.
        require(
            recap.lastClaimedWindowId() == 9999,
            "Exploit failed: contract state not changed as expected"
        );
    }
}
