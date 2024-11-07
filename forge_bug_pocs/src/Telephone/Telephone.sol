// SPDX-License-Identifier: MIT
import "forge-std/console.sol";


pragma solidity ^0.8.0;

contract Telephone {

  address public owner;

  constructor() {
    owner = msg.sender;
  }

  function changeOwner(address _owner) public {
    if (tx.origin != msg.sender) {
      owner = _owner;
    }else{
      console.log('tx.origin != msg.sender');
    }
  }

  receive() external payable {
  }
}