/////////////////////////////////////////////////////////////
// Created by: Synopsys DC Ultra(TM) in wire load mode
// Version   : T-2022.03-SP2
// Date      : Tue Jan 20 22:04:45 2026
/////////////////////////////////////////////////////////////


module AHA0 ( a, b, cout, sum );
  input a, b;
  output cout, sum;
  wire   b, n2;
  assign cout = b;

  INV_X1 U5 ( .A(a), .ZN(n2) );
  NOR2_X1 U6 ( .A1(b), .A2(n2), .ZN(sum) );
endmodule

