import "forge-std/Test.sol";
import "../src/FrontRunningVulnerable.sol";
import "../exploits/FrontRunningVulnerableExploit.sol";

contract FrontRunningVulnerableTest is Test {
    FrontRunningVulnerable private vulnerable;
    FrontRunningVulnerableExploit private attacker;

    function setUp() external {
        // Deploy the vulnerable contract with 1 Ether of funds
        vulnerable = new FrontRunningVulnerable{value: 1 ether}(keccak256(abi.encodePacked("secret")));
    }

    function testHack() external {
        // Deploy attacker
        attacker = new FrontRunningVulnerableExploit(address(vulnerable));
        // Attempt exploit
        attacker.hack();
        // Validate exploit
        require(vulnerable.winner() == address(attacker), "Exploit failed: winner not set to attacker");
    }
}
