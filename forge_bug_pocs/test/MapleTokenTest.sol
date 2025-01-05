pragma solidity 0.8.18;

import "forge-std/Test.sol";
import "../src/MapleToken.sol";
import "../exploits/MapleTokenExploit.sol";

contract MapleTokenExploitTest is Test {
    MapleToken public vulnerableContract;
    MapleTokenExploit public exploitContract;

    function setUp() public {
        // Deploy the vulnerable contract
        vulnerableContract = new MapleToken();

        // Set up (deploy) the exploit contract
        exploitContract = new MapleTokenExploit(address(vulnerableContract));
    }

    function testExploit() public {
        // Trigger the exploit
        exploitContract.hack();

        // Check if the exploit succeeded; revert if not
        require(exploitContract.isHacked(), "Exploit was not successful");
    }
}
