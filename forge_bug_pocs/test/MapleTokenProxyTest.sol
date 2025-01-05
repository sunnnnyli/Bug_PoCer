pragma solidity 0.8.18;

import "forge-std/Test.sol";
import "../src/MapleTokenProxy.sol";
import "../exploits/MapleTokenProxyExploit.sol";

contract MapleTokenProxyExploitTest is Test {
    MapleTokenProxy public vulnerableContract;
    MapleTokenProxyExploit public exploitContract;

    function setUp() public {
        // Deploy the vulnerable contract with dummy arguments
        // (this may revert in a real scenario, but serves as a placeholder for demonstration)
        vulnerableContract = new MapleTokenProxy(address(0), address(0), address(0), address(0));

        // Set up (deploy) the exploit contract
        exploitContract = new MapleTokenProxyExploit(address(vulnerableContract));
    }

    function testExploit() public {
        // Trigger the exploit
        exploitContract.hack();

        // Check if the exploit succeeded; revert if not
        require(exploitContract.isHacked(), "Exploit was not successful");
    }
}