import "forge-std/Test.sol";
import "../src/ForceSendVulnerable.sol";
import "../exploits/ForceSendVulnerableExploit.sol";

contract ForceSendVulnerableExploitTest is Test {
    ForceSendVulnerable vulnerable;
    ForceSendVulnerableExploit exploit;

    address attacker = address(1337);

    function setUp() public {
        vulnerable = new ForceSendVulnerable();

        // Set up the game state by depositing 6 Ether (one at a time).
        for (uint256 i = 0; i < 6; i++) {
            deal(address(this), 1 ether);
            vulnerable.deposit{value: 1 ether}();
        }

        // Confirm there is no winner and check current contract balance.
        assertEq(vulnerable.winner(), address(0), "Winner should not be set yet");
        assertEq(address(vulnerable).balance, 6 ether, "Contract should have 6 ETH");

        // Deploy exploit contract as the attacker.
        vm.startPrank(attacker);
        exploit = new ForceSendVulnerableExploit();
        vm.stopPrank();
    }

    function testExploit() public {
        // Execute the hack.
        vm.startPrank(attacker);
        exploit.hack{value: 1 ether}(address(vulnerable));
        vm.stopPrank();

        // Verify exploit by checking contract's state directly.
        assertEq(vulnerable.winner(), attacker, "Exploit failed: attacker is not the winner");
    }
}
