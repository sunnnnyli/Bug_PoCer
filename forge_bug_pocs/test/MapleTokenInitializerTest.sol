pragma solidity 0.8.18;

import "forge-std/Test.sol";
import "../src/MapleTokenInitializer.sol";
import "../exploits/MapleTokenInitializerExploit.sol";

contract MapleTokenInitializerExploitTest is Test {
    MapleTokenInitializer public vulnerableContract;
    MapleTokenInitializerExploit public exploitContract;

    function setUp() public {
        // Deploy the vulnerable contract
        vulnerableContract = new MapleTokenInitializer();

        // Set up (deploy) the exploit contract
        exploitContract = new MapleTokenInitializerExploit(address(vulnerableContract));
    }

    function testExploit() public {
        // Trigger the exploit
        exploitContract.hack();

        // Check if the exploit succeeded; revert if not
        require(exploitContract.isHacked(), "Exploit was not successful");
    }
}