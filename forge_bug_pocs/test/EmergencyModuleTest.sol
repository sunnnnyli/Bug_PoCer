pragma solidity 0.8.18;

import "forge-std/Test.sol";
import "../src/EmergencyModule.sol";
import "../exploits/EmergencyModuleExploit.sol";

contract EmergencyModuleExploitTest is Test {
    EmergencyModule public vulnerableContract;
    EmergencyModuleExploit public exploitContract;

    function setUp() public {
        // Deploy the vulnerable contract
        vulnerableContract = new EmergencyModule(address(0), address(0));
        // Set up (deploy) the exploit contract
        exploitContract = new EmergencyModuleExploit(address(vulnerableContract));
    }

    function testExploit() public {
        // Trigger the exploit
        exploitContract.hack();
        // Check if the exploit succeeded; revert if not
        require(exploitContract.isHacked(), "Exploit was not successful");
    }
}
