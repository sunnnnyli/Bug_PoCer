import "forge-std/Test.sol";
import "../src/FrontRunningVulnerable.sol";
import "../exploits/FrontRunningVulnerableExploit.sol";

contract FrontRunningVulnerableTest is Test {
    FrontRunningVulnerable public vulnerable;
    FrontRunningVulnerableExploit public exploit;

    function setUp() public {
        // Deploy the vulnerable contract with a dummy password and 1 ETH
        bytes32 dummyPasswordHash = keccak256(abi.encodePacked("notTheRealPassword"));
        vulnerable = new FrontRunningVulnerable{value: 1 ether}(dummyPasswordHash);

        // Set up the exploit contract pointing to the vulnerable contract
        exploit = new FrontRunningVulnerableExploit(address(vulnerable));
    }

    function testExploit() public {
        // Run the exploit strategy
        exploit.hack();

        // Check if the exploit was truly effective
        require(vulnerable.winner() == address(exploit), "Exploit failed: winner is not the exploit");
        require(address(vulnerable).balance == 0, "Exploit failed: contract balance not drained");
    }
}
